# Eva MCP Server

[![CI](https://github.com/knrerikh/eva-mcp-server/workflows/CI/badge.svg)](https://github.com/knrerikh/eva-mcp-server/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

MCP (Model Context Protocol) server for Eva-project API integration. This server allows AI assistants like Claude and Cursor to interact with Eva-project tasks, projects, documents, and more.

> **Quick Start:** See [GETTING_STARTED.md](GETTING_STARTED.md) for step-by-step setup instructions.

## Features

- **Task Management**: Search, view, create, and update tasks
- **Project Management**: List and view project details
- **User Management**: List and view user information
- **Document Management**: Search and view documents
- **Comments**: View and add comments to tasks/documents
- **Sprint Management**: List and view sprints/lists
- **Audit Log**: View audit history
- **Read-Only Mode**: Optional safe mode that prevents write operations (disabled by default for convenience)
- **JSON-RPC 2.0**: Full support for Eva API protocol

## Installation

### Prerequisites

- Python 3.10 or higher
- Eva API access token

### Install from source

```bash
# Clone the repository
git clone https://github.com/knrerikh/eva-mcp-server.git
cd eva-mcp-server

# Install dependencies
pip install -r requirements.txt

# Or install in development mode
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file in the project root (use `.env.example` as template):

```bash
# Eva API Configuration
EVA_API_URL=https://your-eva-instance.com/api
EVA_API_TOKEN=your_token_here

# Optional: Enable read-only mode (default: false - write operations allowed)
# Set to "true" to prevent write operations
EVA_READ_ONLY=false

# Optional: Request timeout in seconds (default: 30)
EVA_TIMEOUT=30
```

### Getting an API Token

1. Log in to your Eva-project instance
2. Navigate to your profile settings
3. Generate an API token
4. Copy the token to your `.env` file

## Usage

### Running the Server

```bash
# Using Python
python -m eva_mcp_server.server

# Or if installed as package
eva-mcp-server
```

### Integration with Cursor

1. Open Cursor settings
2. Navigate to MCP Servers configuration
3. Add the following configuration:

```json
{
  "Eva": {
    "command": "python",
    "args": ["/path/to/eva-mcp-server/src/server.py"],
    "env": {
      "EVA_API_URL": "https://your-eva-instance.com/api",
      "EVA_API_TOKEN": "your_token_here"
    }
  }
}
```

4. Restart Cursor
5. The Eva MCP server should now be available

### Optional: Enabling Read-Only Mode for Safety

By default, write operations are **allowed**. If you want to protect your Eva instance from accidental modifications (e.g., for production environments or analytics), you can enable read-only mode:

1. Open Cursor Settings (Ctrl+Shift+P → "Preferences: Open Settings (JSON)")
2. Find the Eva MCP server configuration in the `mcpServers` section
3. Add `"EVA_READ_ONLY": "true"` in the `env` section:

```json
{
  "mcpServers": {
    "Eva Project MCP": {
      "command": "python",
      "args": ["C:\\Users\\YourUser\\Repos\\eva-mcp-server\\src\\server.py"],
      "env": {
        "EVA_API_URL": "https://your-eva-instance.com/api",
        "EVA_API_TOKEN": "your_token",
        "EVA_READ_ONLY": "true"
      }
    }
  }
}
```

4. Save the configuration file
5. Restart Cursor
6. The Eva MCP server will now block all write operations

### Integration with Claude Desktop

Add to your Claude Desktop configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "Eva": {
      "command": "python",
      "args": ["/path/to/eva-mcp-server/src/server.py"],
      "env": {
        "EVA_API_URL": "https://your-eva-instance.com/api",
        "EVA_API_TOKEN": "your_token_here"
      }
    }
  }
}
```

## Available Tools

### Task Tools

- **eva_search_tasks**: Search and list tasks with filters
  - Parameters: `query`, `project`, `responsible`, `status`, `limit`
  
- **eva_get_task**: Get detailed task information
  - Parameters: `task_code`
  
- **eva_count_tasks**: Count tasks matching filters
  - Parameters: `project`, `responsible`, `status`
  
- **eva_create_task**: Create a new task (requires `read_only=false`)
  - Parameters: `name`, `project_code` (optional), `lists` (optional), `description`, `responsible`, `priority`
  - **Important**: 
    - For tasks in projects: specify only `project_code`
    - For tasks in sprints: specify **both** `project_code` (sprint's parent project) and `lists` (sprint codes)
    - If only `lists` is provided, task will be created but won't be properly linked to a project
  
- **eva_update_task**: Update an existing task (requires `read_only=false`)
  - Parameters: `task_code`, `name`, `description`, `responsible`, `status`, `priority`

### Project Tools

- **eva_list_projects**: List all projects
  - Parameters: `limit`
  
- **eva_get_project**: Get detailed project information
  - Parameters: `project_code`

### User Tools

- **eva_list_users**: List all users
  - Parameters: `limit`
  
- **eva_get_user**: Get detailed user information
  - Parameters: `user_code`

### Document Tools

- **eva_search_documents**: Search and list documents
  - Parameters: `query`, `project`, `limit`
  
- **eva_get_document**: Get detailed document information
  - Parameters: `document_code`

### Comment Tools

- **eva_get_comments**: Get comments for a task or document
  - Parameters: `parent_code`, `limit`
  
- **eva_add_comment**: Add a comment (requires `read_only=false`)
  - Parameters: `parent_code`, `text`

### Sprint/List Tools

- **eva_list_sprints**: List all sprints/lists
  - Parameters: `limit`
  
- **eva_get_sprint**: Get detailed sprint/list information
  - Parameters: `list_code`
  
- **eva_create_list**: Create a new list/sprint/release (requires `read_only=false`)
  - Parameters: `name`, `project_code`

### Audit Tools

- **eva_get_audit_log**: Get audit log entries
  - Parameters: `entity_code`, `limit`

## Best Practices

### Creating Tasks

**For project tasks (no sprint):**
```json
{
  "name": "Task name",
  "project_code": "PROJ-123"
}
```

**For sprint tasks (recommended):**
```json
{
  "name": "Task name",
  "project_code": "CmfProject:xxx",  // Sprint's parent project
  "lists": ["SPR-000929"]             // Sprint code
}
```

**Why both parameters?**
- Using only `lists` will add the task to the sprint, but it won't be linked to the project hierarchy
- Using both `project_code` and `lists` ensures proper linking in both the project tree and sprint board
- This matches the behavior of the Eva web interface

## Examples

### Example 1: Search for tasks

```python
# In your AI assistant
"Search for tasks in project PROJ-123 assigned to user@example.com"
```

This will call `eva_search_tasks` with:
```json
{
  "project": "PROJ-123",
  "responsible": "user@example.com",
  "limit": 20
}
```

### Example 2: Get task details

```python
"Show me details of task TASK-456"
```

This will call `eva_get_task` with:
```json
{
  "task_code": "TASK-456"
}
```

### Example 3: List projects

```python
"List all projects"
```

This will call `eva_list_projects` with default parameters.

### Example 4: Create a task (requires write mode)

```python
# First, disable read-only mode in configuration
"Create a new task named 'Implement feature X' in project PROJ-123"
```

This will call `eva_create_task` with:
```json
{
  "name": "Implement feature X",
  "project_code": "PROJ-123"
}
```

### Example 5: Create a task in a sprint/list (recommended approach)

```python
"Create a new task named 'Fix bug in authentication' in sprint SPR-000929"
```

This will call `eva_create_task` with:
```json
{
  "name": "Fix bug in authentication",
  "project_code": "CmfProject:xxx",
  "lists": ["SPR-000929"]
}
```

**Note**: It's recommended to specify both `project_code` (the sprint's parent project) and `lists` to properly link the task to both the project and the sprint. If only `lists` is provided, the task will be added to the sprint but won't be linked to the project hierarchy.

## Safety and Security

### Read-Only Mode

By default, the server allows write operations (`EVA_READ_ONLY=false`) for convenient usage. 

To enable read-only mode for safety (e.g., for production environments):
1. Set `EVA_READ_ONLY=true` in your configuration
2. This will prevent:
   - Creating tasks
   - Updating tasks
   - Adding comments
   - Any other write operations

**Recommendation**: Use read-only mode when you only need to analyze data or when multiple users share the same configuration.

### API Token Security

- Never commit your API token to version control
- Store the token in `.env` file (which is gitignored)
- Use environment variables for configuration
- Rotate tokens regularly

### Production Usage

When using with production Eva instance:
- Keep read-only mode enabled unless absolutely necessary
- Test write operations on a test instance first
- Monitor API usage and logs
- Implement proper error handling

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_eva_client.py
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

### Project Structure

```
eva-mcp-server/
├── src/
│   ├── __init__.py
│   ├── server.py          # Main MCP server
│   ├── eva_client.py      # Eva API client
│   └── tools.py           # MCP tool implementations
├── tests/
│   ├── __init__.py
│   ├── test_eva_client.py # Client tests
│   └── test_tools.py      # Tools tests
├── .env.example           # Example configuration
├── .gitignore            # Git ignore rules
├── requirements.txt       # Python dependencies
├── pyproject.toml        # Project configuration
├── pytest.ini            # Pytest configuration
├── README.md             # This file
├── API_ANALYSIS.md       # API documentation
└── oas_evateam_v1_9_22.json  # OpenAPI specification
```

## Troubleshooting

### Server won't start

1. Check that Python 3.10+ is installed: `python --version`
2. Verify all dependencies are installed: `pip install -r requirements.txt`
3. Check that `EVA_API_TOKEN` is set in `.env`
4. Review server logs for specific errors

### API calls fail

1. Verify the API token is valid
2. Check network connectivity to Eva API endpoint
3. Ensure the API URL is correct
4. Check if read-only mode is blocking write operations
5. Review Eva API documentation for endpoint requirements

### Tools not appearing in Cursor/Claude

1. Verify the MCP server configuration is correct
2. Restart Cursor/Claude Desktop
3. Check server logs for initialization errors
4. Ensure the server process is running

## API Documentation

For detailed API documentation, refer to the Eva-project API documentation at your Eva instance.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check Eva-project documentation at your Eva instance
- Review the API specification in `oas_evateam_v1_9_22.json`

## Changelog

### Version 0.1.0 (Initial Release)

- Initial implementation of Eva MCP server
- Support for task, project, user, document, comment, sprint, and audit operations
- Read-only mode for safe operations
- Comprehensive test suite
- Full documentation

## Acknowledgments

- Eva-project team for the API
- Model Context Protocol (MCP) specification
- Anthropic for Claude and MCP SDK

