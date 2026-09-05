"""Eva API Client - HTTP client for Eva-project API."""

import os
import re
import uuid
import logging
from typing import Any, Dict, Optional, List, Sequence, Tuple, Union
from datetime import datetime

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Eva addresses every entity by an internal identifier of the form "CmfTask:<uuid>".
# Human-readable codes (task codes, project codes, logins) are a separate namespace
# and most filters and all update methods reject them.
ENTITY_ID_RE = re.compile(r"^Cmf[A-Za-z]+:[0-9a-fA-F-]{8,}$")


def is_entity_id(value: Any) -> bool:
    """True if the value already is an Eva entity identifier."""
    return isinstance(value, str) and bool(ENTITY_ID_RE.match(value))


class EvaAPIError(Exception):
    """Base exception for Eva API errors."""
    
    def __init__(self, message: str, code: Optional[int] = None, details: Optional[Dict] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class EvaClient:
    """Client for interacting with Eva-project API using JSON-RPC 2.0."""
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_token: Optional[str] = None,
        read_only: Optional[bool] = None,
        timeout: int = 30,
    ):
        """
        Initialize Eva API client.
        
        Args:
            api_url: Eva API base URL (default: from EVA_API_URL env var)
            api_token: API authentication token (default: from EVA_API_TOKEN env var)
            read_only: Enable read-only mode to prevent write operations (default: from EVA_READ_ONLY env var or True if not set)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_url = api_url or os.getenv("EVA_API_URL", "https://your-eva-instance.com/api")
        self.api_token = api_token or os.getenv("EVA_API_TOKEN", "")
        # По умолчанию read-only режим включен (true), если не указано явно или через EVA_READ_ONLY
        self.read_only = read_only if read_only is not None else os.getenv("EVA_READ_ONLY", "true").lower() == "true"
        self.timeout = timeout or int(os.getenv("EVA_TIMEOUT", "30"))
        
        if not self.api_token:
            raise ValueError("API token is required. Set EVA_API_TOKEN environment variable.")
        
        self.client = httpx.Client(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json",
            },
            follow_redirects=False,
        )
        
        # Resolved code -> entity id, so repeated filters cost one lookup, not many
        self._id_cache: Dict[Tuple[str, Tuple[str, ...]], str] = {}

        logger.info(f"Eva client initialized (read_only={self.read_only}, url={self.api_url})")
    
    def _generate_callid(self) -> str:
        """Generate a unique call ID for JSON-RPC request."""
        return str(uuid.uuid4())
    
    def _build_request(
        self,
        method: str,
        kwargs: Optional[Dict[str, Any]] = None,
        args: Optional[Sequence[Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build JSON-RPC 2.0 request.

        Args:
            method: API method name (e.g., "CmfTask.get")
            kwargs: Method parameters
            args: Positional parameters. Update methods take the entity
                identifier here — Eva answers "Необходимо указать id в args[0]"
                when it is missing.

        Returns:
            JSON-RPC request dictionary
        """
        request = {
            "jsonrpc": "2.2",
            "method": method,
            "callid": self._generate_callid(),
            "kwargs": kwargs or {},
        }
        if args:
            request["args"] = list(args)
        return request
    
    def _check_write_operation(self, method: str) -> None:
        """
        Check if write operation is allowed.
        
        Args:
            method: API method name
            
        Raises:
            EvaAPIError: If write operation is attempted in read-only mode
        """
        write_operations = ["create", "update", "delete", "append", "set_", "do_"]
        
        if self.read_only and any(op in method.lower() for op in write_operations):
            raise EvaAPIError(
                f"Write operation '{method}' is not allowed in read-only mode. "
                "Set read_only=False to enable write operations.",
                code=-32001
            )
    
    def call(self, method: str, *args, **kwargs) -> Any:
        """
        Make a JSON-RPC API call.

        Args:
            method: API method name (e.g., "CmfTask.get")
            *args: Positional parameters (entity identifier for update methods)
            **kwargs: Method parameters

        Returns:
            API response result

        Raises:
            EvaAPIError: If API returns an error or request fails
        """
        self._check_write_operation(method)

        request_data = self._build_request(method, kwargs, args=args)

        logger.debug(f"API call: {method} with args: {args}, params: {kwargs}")
        
        try:
            # Method is added as query parameter in URL
            url_with_method = f"{self.api_url}/?m={method}"
            response = self.client.post(url_with_method, json=request_data)
            response.raise_for_status()
            
            result = response.json()
            
            # Check for JSON-RPC error
            if "error" in result:
                error = result["error"]
                raise EvaAPIError(
                    message=error.get("message", "Unknown error"),
                    code=error.get("code"),
                    details=error
                )
            
            logger.debug(f"API call successful: {method}")
            return result.get("result")
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}")
            raise EvaAPIError(f"HTTP error: {e.response.status_code}", details={"response": str(e)})
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise EvaAPIError(f"Request error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise EvaAPIError(f"Unexpected error: {str(e)}")
    
    def resolve_id(
        self,
        code: Any,
        entity: Union[str, Sequence[str]] = "CmfTask",
    ) -> str:
        """
        Resolve a human-readable code to the internal Eva identifier.

        Eva stores relations as ``CmfTask:<uuid>``. Passing a code such as a task
        code, a project code or a login into a filter matches nothing and returns
        an empty result without an error, so every relation filter and every
        update has to resolve first.

        Args:
            code: Human-readable code, or an identifier (returned unchanged)
            entity: Entity class to look up, or several to try in order —
                a comment parent, for instance, may be a task or a document

        Returns:
            Entity identifier

        Raises:
            EvaAPIError: If the code cannot be resolved
        """
        if is_entity_id(code):
            return code

        if not code or not str(code).strip():
            raise EvaAPIError("Cannot resolve an empty code to an entity id")

        code = str(code).strip()
        entities: Tuple[str, ...] = (entity,) if isinstance(entity, str) else tuple(entity)

        cache_key = (code, entities)
        if cache_key in self._id_cache:
            return self._id_cache[cache_key]

        last_error: Optional[EvaAPIError] = None
        for entity_name in entities:
            try:
                found = self.call(f"{entity_name}.get", code=code, fields=["id", "code"])
            except EvaAPIError as e:
                last_error = e
                continue
            entity_id = (found or {}).get("id")
            if entity_id:
                self._id_cache[cache_key] = entity_id
                return entity_id

        raise EvaAPIError(
            f"Cannot resolve '{code}' to a {'/'.join(entities)} id"
            + (f": {last_error.message}" if last_error else ""),
            code=last_error.code if last_error else None,
        )

    # Task operations
    def get_task(
        self,
        code: str,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Get task by code."""
        params: Dict[str, Any] = {"code": code}
        if fields:
            params["fields"] = fields
        return self.call("CmfTask.get", **params)
    
    def list_tasks(
        self,
        filters: Optional[List[List[Any]]] = None,
        limit: int = 50,
        offset: int = 0,
        fields: Optional[List[str]] = None,
        order_by: Optional[List[str]] = None,
        include_archived: bool = False,
    ) -> List[Dict[str, Any]]:
        """List tasks with optional filters."""
        params = {
            "slice": [offset, offset + limit],
            "include_archived": include_archived
        }
        if filters:
            params["filter"] = filters
        if fields:
            params["fields"] = fields
        if order_by:
            params["order_by"] = order_by
        return self.call("CmfTask.list", **params)
    
    def count_tasks(self, filters: Optional[List[List[Any]]] = None) -> int:
        """Count tasks with optional filters."""
        params = {}
        if filters:
            params["filter"] = filters
        return self.call("CmfTask.count", **params)

    def list_tasks_by_list(
        self,
        list_code: str,
        limit: int = 100,
        offset: int = 0,
        fields: Optional[List[str]] = None,
        include_archived: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List tasks in a sprint/list.

        Filter must use list entity id (CmfList:uuid), not human-readable code.
        """
        list_id = self.resolve_id(list_code, "CmfList")

        params: Dict[str, Any] = {
            "filter": [["lists", "IN", [list_id]]],
            "slice": [offset, offset + limit],
            "include_archived": include_archived,
        }
        if fields:
            params["fields"] = fields
        return self.call("CmfTask.list", **params)
    
    def create_task(
        self,
        name: str,
        parent: Optional[str] = None,
        lists: Optional[List[str]] = None,
        text: Optional[str] = None,
        responsible: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new task."""
        params = {"name": name}
        
        if parent:
            params["parent"] = parent
        if lists:
            params["lists"] = lists
        if text:
            params["text"] = text
        if responsible:
            params["responsible"] = responsible
        params.update(kwargs)
        return self.call("CmfTask.create", **params)
    
    def update_task(self, code: str, **kwargs) -> Dict[str, Any]:
        """
        Update an existing task.

        The identifier goes in ``args[0]`` — Eva rejects it both as a keyword
        argument and as a human-readable code in ``args[0]``, so it is resolved
        to an entity id first.
        """
        task_id = self.resolve_id(code, "CmfTask")
        return self.call("CmfTask.update", task_id, **kwargs)
    
    # Project operations
    def get_project(self, code: str) -> Dict[str, Any]:
        """Get project by code."""
        return self.call("CmfProject.get", code=code)
    
    def list_projects(
        self,
        filters: Optional[List[List[Any]]] = None,
        limit: int = 50,
        offset: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List projects with optional filters."""
        params = {"slice": [offset, offset + limit]}
        if filters:
            params["filter"] = filters
        if fields:
            params["fields"] = fields
        return self.call("CmfProject.list", **params)
    
    def count_projects(self, filters: Optional[List[List[Any]]] = None) -> int:
        """Count projects with optional filters."""
        params = {}
        if filters:
            params["filter"] = filters
        return self.call("CmfProject.count", **params)
    
    # User operations
    def get_user(self, code: str) -> Dict[str, Any]:
        """Get user by code."""
        return self.call("CmfPerson.get", code=code)
    
    def list_users(
        self,
        filters: Optional[List[List[Any]]] = None,
        limit: int = 50,
        offset: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List users with optional filters."""
        params = {"slice": [offset, offset + limit]}
        if filters:
            params["filter"] = filters
        if fields:
            params["fields"] = fields
        return self.call("CmfPerson.list", **params)
    
    # Document operations
    def get_document(self, code: str) -> Dict[str, Any]:
        """Get document by code."""
        return self.call("CmfDocument.get", code=code)
    
    def list_documents(
        self,
        filters: Optional[List[List[Any]]] = None,
        limit: int = 50,
        offset: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List documents with optional filters."""
        params = {"slice": [offset, offset + limit]}
        if filters:
            params["filter"] = filters
        if fields:
            params["fields"] = fields
        return self.call("CmfDocument.list", **params)
    
    # Comment operations
    def list_comments(
        self,
        filters: Optional[List[List[Any]]] = None,
        limit: int = 50,
        offset: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List comments with optional filters."""
        params = {"slice": [offset, offset + limit]}
        if filters:
            params["filter"] = filters
        if fields:
            params["fields"] = fields
        return self.call("CmfComment.list", **params)
    
    def create_comment(
        self,
        parent: str,
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a new comment."""
        params = {
            "parent": parent,
            "text": text,
        }
        params.update(kwargs)
        return self.call("CmfComment.create", **params)
    
    # List/Sprint operations
    def get_list(self, code: str) -> Dict[str, Any]:
        """Get list/sprint by code."""
        return self.call("CmfList.get", code=code)
    
    def create_list(self, name: str, parent: str, **kwargs) -> Dict[str, Any]:
        """Create a new list/sprint under a project.

        NOTE: This is a write operation and will be blocked when read_only=True.
        """
        params = {"name": name, "parent": parent}
        params.update(kwargs)
        return self.call("CmfList.create", **params)
    
    def list_lists(
        self,
        filters: Optional[List[List[Any]]] = None,
        limit: int = 50,
        offset: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List all lists/sprints with optional filters."""
        params = {"slice": [offset, offset + limit]}
        if filters:
            params["filter"] = filters
        if fields:
            params["fields"] = fields
        return self.call("CmfList.list", **params)
    
    # Audit operations
    def list_audit(
        self,
        filters: Optional[List[List[Any]]] = None,
        limit: int = 50,
        offset: int = 0,
        fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """List audit log entries with optional filters."""
        params = {"slice": [offset, offset + limit]}
        if filters:
            params["filter"] = filters
        if fields:
            params["fields"] = fields
        return self.call("CmfAudit.list", **params)
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

