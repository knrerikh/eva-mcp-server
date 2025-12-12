"""Eva API Client - HTTP client for Eva-project API."""

import os
import uuid
import logging
from typing import Any, Dict, Optional, List
from datetime import datetime

import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


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
        
        logger.info(f"Eva client initialized (read_only={self.read_only}, url={self.api_url})")
    
    def _generate_callid(self) -> str:
        """Generate a unique call ID for JSON-RPC request."""
        return str(uuid.uuid4())
    
    def _build_request(self, method: str, kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Build JSON-RPC 2.0 request.
        
        Args:
            method: API method name (e.g., "CmfTask.get")
            kwargs: Method parameters
            
        Returns:
            JSON-RPC request dictionary
        """
        return {
            "jsonrpc": "2.2",
            "method": method,
            "callid": self._generate_callid(),
            "kwargs": kwargs or {},
        }
    
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
    
    def call(self, method: str, **kwargs) -> Any:
        """
        Make a JSON-RPC API call.
        
        Args:
            method: API method name (e.g., "CmfTask.get")
            **kwargs: Method parameters
            
        Returns:
            API response result
            
        Raises:
            EvaAPIError: If API returns an error or request fails
        """
        self._check_write_operation(method)
        
        request_data = self._build_request(method, kwargs)
        
        logger.debug(f"API call: {method} with params: {kwargs}")
        
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
    
    # Task operations
    def get_task(self, code: str) -> Dict[str, Any]:
        """Get task by code."""
        return self.call("CmfTask.get", code=code)
    
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
        """Update an existing task."""
        return self.call("CmfTask.update", code=code, **kwargs)
    
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

