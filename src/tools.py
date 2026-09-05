"""MCP Tools for Eva API - Tool definitions for Model Context Protocol."""

import html
import json
import logging
import re
from typing import Any, Dict, Optional, List

from eva_client import EvaClient, EvaAPIError

logger = logging.getLogger(__name__)

# Eva rejects lowercase filter operations outright: the accepted set is
# > < == >= <= = IN != >< <> "NOT IN" LIKE "NOT LIKE" ILIKE "NOT ILIKE" ...
ILIKE = "ILIKE"

# A task carries both a named status (a CmfStatus relation, e.g. "Backlog") and a
# status type in cache_status_type (e.g. "OPEN"). Filtering the relation by a type
# name matches nothing, so the two are routed to different fields.
STATUS_TYPE_RE = re.compile(r"^[A-Z][A-Z_]*$")

# Fields worth searching when the caller passes free text.
TEXT_SEARCH_FIELDS = ("name", "text")

TASK_DETAIL_FIELDS = [
    "code",
    "name",
    "text",
    "parent_id",
    "project_id",
    "cache_status_type",
    "cache_child_tasks_count",
    "workflow_id",
    "epic",
    "epic_id",
    "deadline",
    "priority",
    "responsible",
    "responsible_id",
    "lists",
    "cmf_owner_id",
]


def looks_double_escaped(text: Optional[str]) -> bool:
    """
    True if the text looks like HTML that was escaped twice.

    Eva stores the ``description``/``text`` fields as raw HTML. A caller that
    escapes its markup first sends "&lt;p&gt;" where Eva expects "<p>", and Eva
    stores that verbatim, so the reader sees tags as text. A string that carries
    entities but not a single "<" is a caller mistake rather than content.
    """
    if not text or "<" in text:
        return False
    return "&lt;" in text or "&gt;" in text


def repair_html(text: Optional[str]) -> tuple:
    """
    Undo double escaping, if that is what happened.

    Returns:
        (text, repaired) — the text to send and whether it was changed
    """
    if looks_double_escaped(text):
        return html.unescape(text), True
    return text, False


def text_search_filter(query: str) -> List[Any]:
    """
    Build a filter matching the query in either the title or the description.

    Eva groups alternatives as ["OR", <clause>, <clause>], and such a group
    combines with the other clauses of the filter list by AND.
    """
    pattern = f"%{query}%"
    return ["OR"] + [[field, ILIKE, pattern] for field in TEXT_SEARCH_FIELDS]


def status_filter(status: str) -> List[Any]:
    """Route a status to the relation or to the cached status type."""
    if STATUS_TYPE_RE.match(status):
        return ["cache_status_type", "=", status]
    return ["status.name", "=", status]


class EvaTools:
    """MCP tools for interacting with Eva API."""

    def __init__(self, client: EvaClient):
        """
        Initialize Eva tools with API client.

        Args:
            client: EvaClient instance
        """
        self.client = client

    def _entity_filters(
        self,
        query: Optional[str] = None,
        project: Optional[str] = None,
        responsible: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[List[Any]]:
        """
        Build the filter list shared by the task and document tools.

        Relation filters (``parent``, ``responsible``) are matched against entity
        identifiers, so codes and logins are resolved first. Without that, Eva
        returns an empty result and no error — the filter silently matches nothing.
        """
        filters: List[List[Any]] = []

        if project:
            filters.append(["parent", "=", self.client.resolve_id(project, "CmfProject")])
        if responsible:
            filters.append(
                ["responsible", "=", self.client.resolve_id(responsible, "CmfPerson")]
            )
        if status:
            filters.append(status_filter(status))
        if query:
            filters.append(text_search_filter(query))

        return filters

    # Task Tools

    def search_tasks(
        self,
        query: Optional[str] = None,
        project: Optional[str] = None,
        responsible: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """
        Search and list tasks with filters.
        
        Args:
            query: Search query text, matched against the title and the description
            project: Filter by project code or id
            responsible: Filter by responsible user login/email or id
            status: Status name (e.g. "Backlog") or status type (e.g. "OPEN")
            limit: Maximum number of results (default: 20)

        Returns:
            JSON string with task list
        """
        try:
            filters = self._entity_filters(
                query=query,
                project=project,
                responsible=responsible,
                status=status,
            )

            tasks = self.client.list_tasks(
                filters=filters if filters else None,
                limit=limit
            )

            return json.dumps({
                "success": True,
                "count": len(tasks),
                "filters": filters,
                "tasks": tasks
            }, ensure_ascii=False, indent=2)

        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    def get_task_details(self, task_code: str) -> str:
        """
        Get detailed information about a specific task.
        
        Args:
            task_code: Task code/ID
            
        Returns:
            JSON string with task details
        """
        try:
            task = self.client.get_task(task_code, fields=TASK_DETAIL_FIELDS)
            
            return json.dumps({
                "success": True,
                "task": task
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)

    def get_tasks_by_list(
        self,
        list_code: str,
        limit: Optional[int] = None,
        offset: int = 0,
        include_archived: bool = False,
    ) -> str:
        """
        Get tasks in a sprint/list (e.g. LST-002269).

        Uses ``lists IN [CmfList:uuid]`` and returns task ``text`` (HTML description).
        """
        try:
            if not list_code or not str(list_code).strip():
                raise ValueError("list_code is required")

            list_code = str(list_code).strip()
            list_meta = self.client.get_list(list_code)

            expected = list_meta.get("cache_members_count")
            target = limit if limit is not None else (int(expected) + 5 if expected else 50)
            page_size = min(50, max(target, 1))

            tasks: List[Dict[str, Any]] = []
            current_offset = offset

            while len(tasks) < target:
                batch = self.client.list_tasks_by_list(
                    list_code=list_code,
                    limit=page_size,
                    offset=current_offset,
                    fields=TASK_DETAIL_FIELDS,
                    include_archived=include_archived,
                )
                if not batch:
                    break
                tasks.extend(batch)
                if len(batch) < page_size:
                    break
                current_offset += page_size
                if limit is not None:
                    break

            if limit is not None:
                tasks = tasks[:limit]

            return json.dumps(
                {
                    "success": True,
                    "list_code": list_code,
                    "list_id": list_meta.get("id"),
                    "list": list_meta,
                    "count": len(tasks),
                    "tasks": tasks,
                },
                ensure_ascii=False,
                indent=2,
            )

        except EvaAPIError as e:
            return json.dumps(
                {"success": False, "error": e.message, "code": e.code},
                ensure_ascii=False,
                indent=2,
            )
        except ValueError as e:
            return json.dumps(
                {"success": False, "error": str(e)},
                ensure_ascii=False,
                indent=2,
            )
    
    def count_tasks_by_filter(
        self,
        project: Optional[str] = None,
        responsible: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Count tasks matching filters.
        
        Args:
            project: Filter by project code or id
            responsible: Filter by responsible user login/email or id
            status: Status name (e.g. "Backlog") or status type (e.g. "OPEN")

        Returns:
            JSON string with task count
        """
        try:
            filters = self._entity_filters(
                project=project,
                responsible=responsible,
                status=status,
            )

            count = self.client.count_tasks(filters=filters if filters else None)
            
            return json.dumps({
                "success": True,
                "count": count,
                "filters": filters
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    def create_task(
        self,
        name: str,
        project_code: Optional[str] = None,
        lists: Optional[List[str]] = None,
        description: Optional[str] = None,
        responsible: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> str:
        """
        Create a new task in Eva.
        
        WARNING: This is a write operation. Requires read_only=False.
        
        Args:
            name: Task name/title
            project_code: Parent project code (optional)
            lists: List of sprint/list codes to add task to (e.g., ['SPR-000929'])
            description: Task description as raw HTML, e.g. "<p>Text</p>".
                Pre-escaped markup ("&lt;p&gt;") would be stored verbatim and
                shown to the reader as tags.
            responsible: Responsible user email/login
            priority: Task priority (0-5)

        Note:
            - For tasks in projects: specify only project_code
            - For tasks in sprints: specify BOTH project_code and lists
            - If only lists is provided, task will be created but not linked to project

        Returns:
            JSON string with created task details
        """
        try:
            kwargs = {}
            repaired = False
            if description:
                kwargs["text"], repaired = repair_html(description)
            if priority is not None:
                kwargs["priority"] = priority

            task = self.client.create_task(
                name=name,
                parent=project_code,
                lists=lists,
                responsible=responsible,
                **kwargs
            )

            payload = {
                "success": True,
                "task": task,
                "message": "Task created successfully"
            }
            if repaired:
                payload["html_unescaped"] = True
                payload["warning"] = (
                    "description arrived HTML-escaped and was unescaped before "
                    "sending; pass raw HTML"
                )
            return json.dumps(payload, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    def update_task(
        self,
        task_code: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        responsible: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[int] = None,
    ) -> str:
        """
        Update an existing task.
        
        WARNING: This is a write operation. Requires read_only=False.
        
        Args:
            task_code: Task code to update (or entity id)
            name: New task name
            description: New task description as raw HTML, e.g. "<p>Text</p>".
                Pre-escaped markup ("&lt;p&gt;") would be stored verbatim and
                shown to the reader as tags.
            responsible: New responsible user
            status: New task status
            priority: New task priority (0-5)

        Returns:
            JSON string with updated task details
        """
        try:
            kwargs = {}
            repaired = False
            if name:
                kwargs["name"] = name
            if description:
                kwargs["text"], repaired = repair_html(description)
            if responsible:
                kwargs["responsible"] = responsible
            if status:
                kwargs["status"] = status
            if priority is not None:
                kwargs["priority"] = priority

            if not kwargs:
                raise ValueError("Nothing to update: pass at least one field")

            task = self.client.update_task(task_code, **kwargs)

            payload = {
                "success": True,
                "task": task,
                "message": "Task updated successfully"
            }
            if repaired:
                payload["html_unescaped"] = True
                payload["warning"] = (
                    "description arrived HTML-escaped and was unescaped before "
                    "sending; pass raw HTML"
                )
            return json.dumps(payload, ensure_ascii=False, indent=2)

        except ValueError as e:
            return json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    # Project Tools
    
    def list_projects(self, limit: int = 20) -> str:
        """
        List all projects.
        
        Args:
            limit: Maximum number of results (default: 20)
            
        Returns:
            JSON string with project list
        """
        try:
            projects = self.client.list_projects(limit=limit)
            
            return json.dumps({
                "success": True,
                "count": len(projects),
                "projects": projects
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    def get_project_details(self, project_code: str) -> str:
        """
        Get detailed information about a specific project.
        
        Args:
            project_code: Project code/ID
            
        Returns:
            JSON string with project details
        """
        try:
            project = self.client.get_project(project_code)
            
            return json.dumps({
                "success": True,
                "project": project
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    # User Tools
    
    def list_users(self, limit: int = 50) -> str:
        """
        List all users.
        
        Args:
            limit: Maximum number of results (default: 50)
            
        Returns:
            JSON string with user list
        """
        try:
            users = self.client.list_users(limit=limit)
            
            return json.dumps({
                "success": True,
                "count": len(users),
                "users": users
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    def get_user_details(self, user_code: str) -> str:
        """
        Get detailed information about a specific user.
        
        Args:
            user_code: User code/email/login
            
        Returns:
            JSON string with user details
        """
        try:
            user = self.client.get_user(user_code)
            
            return json.dumps({
                "success": True,
                "user": user
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    # Document Tools
    
    def search_documents(
        self,
        query: Optional[str] = None,
        project: Optional[str] = None,
        limit: int = 20,
    ) -> str:
        """
        Search and list documents with filters.
        
        Args:
            query: Search query text, matched against the title and the body
            project: Filter by project code or id
            limit: Maximum number of results (default: 20)

        Returns:
            JSON string with document list
        """
        try:
            filters = self._entity_filters(query=query, project=project)

            documents = self.client.list_documents(
                filters=filters if filters else None,
                limit=limit
            )

            return json.dumps({
                "success": True,
                "count": len(documents),
                "filters": filters,
                "documents": documents
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    def get_document_details(self, document_code: str) -> str:
        """
        Get detailed information about a specific document.
        
        Args:
            document_code: Document code/ID
            
        Returns:
            JSON string with document details
        """
        try:
            document = self.client.get_document(document_code)
            
            return json.dumps({
                "success": True,
                "document": document
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    # Comment Tools
    
    def get_comments(
        self,
        parent_code: str,
        limit: int = 50,
    ) -> str:
        """
        Get comments for a task or document.
        
        Args:
            parent_code: Parent task or document code (or entity id)
            limit: Maximum number of results (default: 50)

        Returns:
            JSON string with comment list
        """
        try:
            parent_id = self.client.resolve_id(parent_code, ("CmfTask", "CmfDocument"))

            comments = self.client.list_comments(
                filters=[["parent", "=", parent_id]],
                limit=limit
            )

            return json.dumps({
                "success": True,
                "parent_id": parent_id,
                "count": len(comments),
                "comments": comments
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    def add_comment(
        self,
        parent_code: str,
        text: str,
    ) -> str:
        """
        Add a comment to a task or document.
        
        WARNING: This is a write operation. Requires read_only=False.
        
        Args:
            parent_code: Parent task or document code (or entity id)
            text: Comment text as raw HTML, e.g. "<p>Done</p>". Pre-escaped
                markup ("&lt;p&gt;") would be stored verbatim and shown as tags.

        Returns:
            JSON string with created comment details
        """
        try:
            parent_id = self.client.resolve_id(parent_code, ("CmfTask", "CmfDocument"))
            text, repaired = repair_html(text)

            comment = self.client.create_comment(parent=parent_id, text=text)

            payload = {
                "success": True,
                "parent_id": parent_id,
                "comment": comment,
                "message": "Comment added successfully"
            }
            if repaired:
                payload["html_unescaped"] = True
                payload["warning"] = (
                    "text arrived HTML-escaped and was unescaped before sending; "
                    "pass raw HTML"
                )
            return json.dumps(payload, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    # List/Sprint Tools
    
    def list_sprints(self, limit: int = 50) -> str:
        """
        List all sprints/lists.
        
        Args:
            limit: Maximum number of results (default: 50)
            
        Returns:
            JSON string with sprint/list list
        """
        try:
            lists = self.client.list_lists(limit=limit)
            
            return json.dumps({
                "success": True,
                "count": len(lists),
                "lists": lists
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    def create_list(self, name: str, project_code: str) -> str:
        """
        Create a new list (sprint/release/list) in Eva under a project.
        
        WARNING: This is a write operation. Requires read_only=False.
        NOTE: API schema (oas) exposes only 'name' and 'parent', so list type is determined by Eva side.
        
        Args:
            name: List name/title
            project_code: Parent project code (e.g., CmfProject:...)
            
        Returns:
            JSON string with created list details
        """
        try:
            if not name or not name.strip():
                raise ValueError("name is required")
            if not project_code or not project_code.strip():
                raise ValueError("project_code is required")
            
            created = self.client.create_list(name=name, parent=project_code)
            
            return json.dumps({
                "success": True,
                "list": created,
                "message": "List created successfully"
            }, ensure_ascii=False, indent=2)
            
        except (EvaAPIError, ValueError) as e:
            if isinstance(e, EvaAPIError):
                return json.dumps({
                    "success": False,
                    "error": e.message,
                    "code": e.code
                }, ensure_ascii=False, indent=2)
            return json.dumps({
                "success": False,
                "error": str(e)
            }, ensure_ascii=False, indent=2)
    
    def get_sprint_details(self, list_code: str) -> str:
        """
        Get detailed information about a specific sprint/list.
        
        Args:
            list_code: Sprint/list code
            
        Returns:
            JSON string with sprint/list details
        """
        try:
            sprint = self.client.get_list(list_code)
            
            return json.dumps({
                "success": True,
                "list": sprint
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)
    
    # Audit Tools
    
    def get_audit_log(
        self,
        entity_code: Optional[str] = None,
        limit: int = 50,
    ) -> str:
        """
        Get audit log entries.
        
        Note:
            Audit entries hang off the audited entity via ``parent`` and are
            addressed by id. Field-level content may still be hidden by ACL —
            entries then come back with "_acl_obj": "deny" and no readable fields.

        Args:
            entity_code: Filter by specific entity code (task, document or id)
            limit: Maximum number of results (default: 50)

        Returns:
            JSON string with audit log entries
        """
        try:
            filters = []
            if entity_code:
                entity_id = self.client.resolve_id(
                    entity_code, ("CmfTask", "CmfDocument", "CmfProject")
                )
                filters.append(["parent", "=", entity_id])

            audit_entries = self.client.list_audit(
                filters=filters if filters else None,
                limit=limit
            )
            
            return json.dumps({
                "success": True,
                "count": len(audit_entries),
                "audit_log": audit_entries
            }, ensure_ascii=False, indent=2)
            
        except EvaAPIError as e:
            return json.dumps({
                "success": False,
                "error": e.message,
                "code": e.code
            }, ensure_ascii=False, indent=2)

