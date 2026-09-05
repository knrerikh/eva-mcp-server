"""Eva MCP HTTP Server - HTTP wrapper for Eva Project MCP Server."""

import os
import sys
import json
import asyncio
from typing import Any, Dict, List
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Add src directory to path
src_dir = Path(__file__).parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from eva_client import EvaClient
from tools import EvaTools

app = FastAPI(title="Eva Project MCP HTTP Server")

# Global instances
eva_client: EvaClient = None
eva_tools: EvaTools = None


def initialize_client():
    """Initialize Eva API client and tools."""
    global eva_client, eva_tools
    
    try:
        api_url = os.getenv("EVA_API_URL", "https://eva-api.example.com")
        api_token = os.getenv("EVA_API_TOKEN")
        read_only = os.getenv("EVA_READ_ONLY", "false").lower() == "true"
        
        print(f"Initializing Eva MCP HTTP Server...")
        print(f"API URL: {api_url}")
        print(f"API Token from env: {api_token[:4] if api_token else 'MISSING'}...{api_token[-4:] if api_token and len(api_token) > 8 else ''}")
        print(f"Read-only mode: {read_only}")
        
        if not api_token:
            raise ValueError("EVA_API_TOKEN environment variable is required")
        
        eva_client = EvaClient(
            api_url=api_url,
            api_token=api_token,
            read_only=read_only
        )
        eva_tools = EvaTools(eva_client)
        
        print("[OK] Eva MCP HTTP Server ready")
        
    except Exception as e:
        print(f"Failed to initialize: {e}")
        sys.exit(1)


# Pydantic models for request/response
class SearchTasksRequest(BaseModel):
    query: str = ""
    project: str = ""
    responsible: str = ""
    status: str = ""
    limit: int = 20


class TaskCodeRequest(BaseModel):
    task_code: str


class CountTasksRequest(BaseModel):
    project: str = ""
    responsible: str = ""
    status: str = ""


class CreateTaskRequest(BaseModel):
    name: str
    project_code: str = ""
    lists: List[str] = []
    description: str = ""
    responsible: str = ""
    priority: int = 0


class UpdateTaskRequest(BaseModel):
    task_code: str
    name: str = ""
    description: str = ""
    responsible: str = ""
    status: str = ""
    priority: int = 0


class ListProjectsRequest(BaseModel):
    limit: int = 20


class UserCodeRequest(BaseModel):
    user_code: str


class ListUsersRequest(BaseModel):
    limit: int = 50


class SearchDocumentsRequest(BaseModel):
    query: str = ""
    project: str = ""
    limit: int = 20


class DocumentCodeRequest(BaseModel):
    document_code: str


class ParentCodeRequest(BaseModel):
    parent_code: str
    limit: int = 50


class AddCommentRequest(BaseModel):
    parent_code: str
    text: str


class ListSprintsRequest(BaseModel):
    limit: int = 50


class SprintCodeRequest(BaseModel):
    list_code: str


class CreateListRequest(BaseModel):
    name: str
    project_code: str


class AuditLogRequest(BaseModel):
    entity_code: str = ""
    limit: int = 50


# Tool endpoints
@app.post("/tools/eva_search_tasks")
async def search_tasks(request: SearchTasksRequest):
    """Search and list tasks."""
    try:
        result = eva_tools.search_tasks(
            query=request.query,
            project=request.project,
            responsible=request.responsible,
            status=request.status,
            limit=request.limit
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_get_task")
async def get_task(request: TaskCodeRequest):
    """Get task details."""
    try:
        result = eva_tools.get_task_details(task_code=request.task_code)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_count_tasks")
async def count_tasks(request: CountTasksRequest):
    """Count tasks by filter."""
    try:
        result = eva_tools.count_tasks_by_filter(
            project=request.project,
            responsible=request.responsible,
            status=request.status
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_create_task")
async def create_task(request: CreateTaskRequest):
    """Create a new task."""
    try:
        result = eva_tools.create_task(
            name=request.name,
            project_code=request.project_code,
            lists=request.lists,
            description=request.description,
            responsible=request.responsible,
            priority=request.priority
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_update_task")
async def update_task(request: UpdateTaskRequest):
    """Update existing task."""
    try:
        result = eva_tools.update_task(
            task_code=request.task_code,
            name=request.name,
            description=request.description,
            responsible=request.responsible,
            status=request.status,
            priority=request.priority
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_list_projects")
async def list_projects(request: ListProjectsRequest):
    """List all projects."""
    try:
        result = eva_tools.list_projects(limit=request.limit)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_get_project")
async def get_project(task_code: str):
    """Get project details."""
    try:
        result = eva_tools.get_project_details(project_code=task_code)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_list_users")
async def list_users(request: ListUsersRequest):
    """List all users."""
    try:
        result = eva_tools.list_users(limit=request.limit)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_get_user")
async def get_user(request: UserCodeRequest):
    """Get user details."""
    try:
        result = eva_tools.get_user_details(user_code=request.user_code)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_search_documents")
async def search_documents(request: SearchDocumentsRequest):
    """Search documents."""
    try:
        result = eva_tools.search_documents(
            query=request.query,
            project=request.project,
            limit=request.limit
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_get_document")
async def get_document(request: DocumentCodeRequest):
    """Get document details."""
    try:
        result = eva_tools.get_document_details(document_code=request.document_code)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_get_comments")
async def get_comments(request: ParentCodeRequest):
    """Get comments."""
    try:
        result = eva_tools.get_comments(
            parent_code=request.parent_code,
            limit=request.limit
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_add_comment")
async def add_comment(request: AddCommentRequest):
    """Add comment."""
    try:
        result = eva_tools.add_comment(
            parent_code=request.parent_code,
            text=request.text
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_list_sprints")
async def list_sprints(request: ListSprintsRequest):
    """List sprints."""
    try:
        result = eva_tools.list_sprints(limit=request.limit)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_get_sprint")
async def get_sprint(request: SprintCodeRequest):
    """Get sprint details."""
    try:
        result = eva_tools.get_sprint_details(list_code=request.list_code)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_get_tasks_by_list")
async def get_tasks_by_list(request: SprintCodeRequest):
    """Get tasks in a sprint/list."""
    try:
        result = eva_tools.get_tasks_by_list(list_code=request.list_code)
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_create_list")
async def create_list(request: CreateListRequest):
    """Create new sprint."""
    try:
        result = eva_tools.create_list(
            name=request.name,
            project_code=request.project_code
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tools/eva_get_audit_log")
async def get_audit_log(request: AuditLogRequest):
    """Get audit log."""
    try:
        result = eva_tools.get_audit_log(
            entity_code=request.entity_code,
            limit=request.limit
        )
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "service": "eva-mcp-http"}


@app.on_event("startup")
async def startup_event():
    """Initialize client on startup."""
    initialize_client()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("EVA_MCP_HTTP_PORT", "8081"))
    print(f"Starting Eva MCP HTTP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
