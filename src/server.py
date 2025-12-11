"""Eva MCP Server - Main server implementation using MCP SDK."""

import asyncio
import logging
import os
import sys
from typing import Any
from pathlib import Path

# Add src directory to path if running as script
if __name__ == "__main__":
    src_dir = Path(__file__).parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from eva_client import EvaClient
from tools import EvaTools

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MCP server
app = Server("eva-mcp-server")

# Global client and tools instances
eva_client: EvaClient = None
eva_tools: EvaTools = None


def initialize_client():
    """Initialize Eva API client and tools."""
    global eva_client, eva_tools
    
    try:
        # Get configuration from environment
        api_url = os.getenv("EVA_API_URL", "https://your-eva-instance.com/api")
        api_token = os.getenv("EVA_API_TOKEN")
        # По умолчанию запись разрешена (false), явно укажите "true" для read-only режима
        read_only = os.getenv("EVA_READ_ONLY", "false").lower() == "true"
        
        logger.info(f"Initializing Eva MCP Server...")
        logger.info(f"API URL: {api_url}")
        logger.info(f"Read-only mode: {read_only}")
        logger.info(f"Token present: {bool(api_token)}")
        
        if not api_token:
            logger.error("EVA_API_TOKEN environment variable is required")
            sys.exit(1)
        
        # Initialize client
        eva_client = EvaClient(
            api_url=api_url,
            api_token=api_token,
            read_only=read_only
        )
        logger.info("Eva client initialized")
        
        # Initialize tools
        eva_tools = EvaTools(eva_client)
        logger.info("Eva tools initialized")
        
        logger.info(f"✓ Eva MCP Server ready (read_only={read_only})")
        
    except Exception as e:
        logger.error(f"Failed to initialize Eva client: {e}", exc_info=True)
        sys.exit(1)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return [
        # Task tools
        Tool(
            name="eva_search_tasks",
            description="Search and list tasks with optional filters (query, project, responsible, status)",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text"},
                    "project": {"type": "string", "description": "Filter by project code"},
                    "responsible": {"type": "string", "description": "Filter by responsible user"},
                    "status": {"type": "string", "description": "Filter by task status"},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 20},
                },
            },
        ),
        Tool(
            name="eva_get_task",
            description="Get detailed information about a specific task by code",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_code": {"type": "string", "description": "Task code/ID"},
                },
                "required": ["task_code"],
            },
        ),
        Tool(
            name="eva_count_tasks",
            description="Count tasks matching filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "project": {"type": "string", "description": "Filter by project code"},
                    "responsible": {"type": "string", "description": "Filter by responsible user"},
                    "status": {"type": "string", "description": "Filter by task status"},
                },
            },
        ),
        Tool(
            name="eva_create_task",
            description="Create a new task (WARNING: write operation, requires read_only=False). For tasks in sprints, provide BOTH project_code and lists for proper linking.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Task name/title"},
                    "project_code": {"type": "string", "description": "Parent project code. Required for sprint tasks to properly link to project."},
                    "lists": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of sprint/list codes to add task to (e.g., ['SPR-000929']). Use with project_code for proper linking."
                    },
                    "description": {"type": "string", "description": "Task description (HTML)"},
                    "responsible": {"type": "string", "description": "Responsible user email/login"},
                    "priority": {"type": "integer", "description": "Task priority (0-5)"},
                },
                "required": ["name"],
            },
        ),
        Tool(
            name="eva_update_task",
            description="Update an existing task (WARNING: write operation, requires read_only=False)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_code": {"type": "string", "description": "Task code to update"},
                    "name": {"type": "string", "description": "New task name"},
                    "description": {"type": "string", "description": "New task description (HTML)"},
                    "responsible": {"type": "string", "description": "New responsible user"},
                    "status": {"type": "string", "description": "New task status"},
                    "priority": {"type": "integer", "description": "New task priority (0-5)"},
                },
                "required": ["task_code"],
            },
        ),
        
        # Project tools
        Tool(
            name="eva_list_projects",
            description="List all projects",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 20},
                },
            },
        ),
        Tool(
            name="eva_get_project",
            description="Get detailed information about a specific project by code",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_code": {"type": "string", "description": "Project code/ID"},
                },
                "required": ["project_code"],
            },
        ),
        
        # User tools
        Tool(
            name="eva_list_users",
            description="List all users",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 50},
                },
            },
        ),
        Tool(
            name="eva_get_user",
            description="Get detailed information about a specific user",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_code": {"type": "string", "description": "User code/email/login"},
                },
                "required": ["user_code"],
            },
        ),
        
        # Document tools
        Tool(
            name="eva_search_documents",
            description="Search and list documents with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query text"},
                    "project": {"type": "string", "description": "Filter by project code"},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 20},
                },
            },
        ),
        Tool(
            name="eva_get_document",
            description="Get detailed information about a specific document",
            inputSchema={
                "type": "object",
                "properties": {
                    "document_code": {"type": "string", "description": "Document code/ID"},
                },
                "required": ["document_code"],
            },
        ),
        
        # Comment tools
        Tool(
            name="eva_get_comments",
            description="Get comments for a task or document",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent_code": {"type": "string", "description": "Parent task or document code"},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 50},
                },
                "required": ["parent_code"],
            },
        ),
        Tool(
            name="eva_add_comment",
            description="Add a comment to a task or document (WARNING: write operation, requires read_only=False)",
            inputSchema={
                "type": "object",
                "properties": {
                    "parent_code": {"type": "string", "description": "Parent task or document code"},
                    "text": {"type": "string", "description": "Comment text (HTML)"},
                },
                "required": ["parent_code", "text"],
            },
        ),
        
        # Sprint/List tools
        Tool(
            name="eva_list_sprints",
            description="List all sprints/lists",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 50},
                },
            },
        ),
        Tool(
            name="eva_get_sprint",
            description="Get detailed information about a specific sprint/list",
            inputSchema={
                "type": "object",
                "properties": {
                    "list_code": {"type": "string", "description": "Sprint/list code"},
                },
                "required": ["list_code"],
            },
        ),
        
        # Audit tools
        Tool(
            name="eva_get_audit_log",
            description="Get audit log entries with optional filters",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_code": {"type": "string", "description": "Filter by specific entity code"},
                    "limit": {"type": "integer", "description": "Maximum number of results", "default": 50},
                },
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls."""
    try:
        logger.info(f"Tool called: {name} with arguments: {arguments}")
        
        # Map tool names to methods
        tool_map = {
            "eva_search_tasks": eva_tools.search_tasks,
            "eva_get_task": eva_tools.get_task_details,
            "eva_count_tasks": eva_tools.count_tasks_by_filter,
            "eva_create_task": eva_tools.create_task,
            "eva_update_task": eva_tools.update_task,
            "eva_list_projects": eva_tools.list_projects,
            "eva_get_project": eva_tools.get_project_details,
            "eva_list_users": eva_tools.list_users,
            "eva_get_user": eva_tools.get_user_details,
            "eva_search_documents": eva_tools.search_documents,
            "eva_get_document": eva_tools.get_document_details,
            "eva_get_comments": eva_tools.get_comments,
            "eva_add_comment": eva_tools.add_comment,
            "eva_list_sprints": eva_tools.list_sprints,
            "eva_get_sprint": eva_tools.get_sprint_details,
            "eva_get_audit_log": eva_tools.get_audit_log,
        }
        
        if name not in tool_map:
            raise ValueError(f"Unknown tool: {name}")
        
        # Call the tool method
        result = tool_map[name](**arguments)
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        error_result = f'{{"success": false, "error": "{str(e)}"}}'
        return [TextContent(type="text", text=error_result)]


async def main():
    """Main entry point for the MCP server."""
    logger.info("=" * 60)
    logger.info("Starting Eva MCP Server...")
    logger.info("=" * 60)
    
    # Initialize client before starting server
    initialize_client()
    
    # Run the server
    async with stdio_server() as (read_stream, write_stream):
        logger.info("Eva MCP Server started and listening for requests")
        logger.info("=" * 60)
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


def run():
    """Run the server (entry point for CLI)."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run()

