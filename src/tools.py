"""MCP Tools for Eva API - Tool definitions for Model Context Protocol."""

import json
import logging
from typing import Any, Dict, Optional, List

from eva_client import EvaClient, EvaAPIError

logger = logging.getLogger(__name__)


class EvaTools:
    """MCP tools for interacting with Eva API."""
    
    def __init__(self, client: EvaClient):
        """
        Initialize Eva tools with API client.
        
        Args:
            client: EvaClient instance
        """
        self.client = client
    
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
            query: Search query text
            project: Filter by project code
            responsible: Filter by responsible user
            status: Filter by task status
            limit: Maximum number of results (default: 20)
            
        Returns:
            JSON string with task list
        """
        try:
            filters = []
            
            if project:
                filters.append(["parent", "=", project])
            if responsible:
                filters.append(["responsible", "=", responsible])
            if status:
                filters.append(["status", "=", status])
            # Note: text search might require different field name
            if query:
                filters.append(["name", "ilike", f"%{query}%"])
            
            tasks = self.client.list_tasks(
                filters=filters if filters else None,
                limit=limit
            )
            
            return json.dumps({
                "success": True,
                "count": len(tasks),
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
            task = self.client.get_task(task_code)
            
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
    
    def count_tasks_by_filter(
        self,
        project: Optional[str] = None,
        responsible: Optional[str] = None,
        status: Optional[str] = None,
    ) -> str:
        """
        Count tasks matching filters.
        
        Args:
            project: Filter by project code
            responsible: Filter by responsible user
            status: Filter by task status
            
        Returns:
            JSON string with task count
        """
        try:
            filters = []
            
            if project:
                filters.append(["parent", "=", project])
            if responsible:
                filters.append(["responsible", "=", responsible])
            if status:
                filters.append(["status", "=", status])
            
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
            description: Task description (HTML)
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
            if description:
                kwargs["text"] = description
            if priority is not None:
                kwargs["priority"] = priority
            
            task = self.client.create_task(
                name=name,
                parent=project_code,
                lists=lists,
                responsible=responsible,
                **kwargs
            )
            
            return json.dumps({
                "success": True,
                "task": task,
                "message": "Task created successfully"
            }, ensure_ascii=False, indent=2)
            
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
            task_code: Task code to update
            name: New task name
            description: New task description (HTML)
            responsible: New responsible user
            status: New task status
            priority: New task priority (0-5)
            
        Returns:
            JSON string with updated task details
        """
        try:
            kwargs = {}
            if name:
                kwargs["name"] = name
            if description:
                kwargs["text"] = description
            if responsible:
                kwargs["responsible"] = responsible
            if status:
                kwargs["status"] = status
            if priority is not None:
                kwargs["priority"] = priority
            
            task = self.client.update_task(task_code, **kwargs)
            
            return json.dumps({
                "success": True,
                "task": task,
                "message": "Task updated successfully"
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
            query: Search query text
            project: Filter by project code
            limit: Maximum number of results (default: 20)
            
        Returns:
            JSON string with document list
        """
        try:
            filters = []
            
            if project:
                filters.append(["parent", "=", project])
            if query:
                filters.append(["name", "ilike", f"%{query}%"])
            
            documents = self.client.list_documents(
                filters=filters if filters else None,
                limit=limit
            )
            
            return json.dumps({
                "success": True,
                "count": len(documents),
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
            parent_code: Parent task or document code
            limit: Maximum number of results (default: 50)
            
        Returns:
            JSON string with comment list
        """
        try:
            comments = self.client.list_comments(
                filters=[["parent", "=", parent_code]],
                limit=limit
            )
            
            return json.dumps({
                "success": True,
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
            parent_code: Parent task or document code
            text: Comment text (HTML)
            
        Returns:
            JSON string with created comment details
        """
        try:
            comment = self.client.create_comment(parent=parent_code, text=text)
            
            return json.dumps({
                "success": True,
                "comment": comment,
                "message": "Comment added successfully"
            }, ensure_ascii=False, indent=2)
            
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
        
        Args:
            entity_code: Filter by specific entity code
            limit: Maximum number of results (default: 50)
            
        Returns:
            JSON string with audit log entries
        """
        try:
            filters = []
            if entity_code:
                filters.append(["object_code", "=", entity_code])
            
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

