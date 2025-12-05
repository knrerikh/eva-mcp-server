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
- **Read-Only Mode**: Safe mode that prevents write operations (enabled by default)
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
EVA_API_URL=https://eva.s7corp.ru/api
EVA_API_TOKEN=your_token_here

# Optional: Enable read-only mode (default: true)
EVA_READ_ONLY=true

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
      "EVA_API_URL": "https://eva.s7corp.ru/api",
      "EVA_API_TOKEN": "your_token_here",
      "EVA_READ_ONLY": "true"
    }
  }
}
```

4. Restart Cursor
5. The Eva MCP server should now be available

### Integration with Claude Desktop

Add to your Claude Desktop configuration file (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "Eva": {
      "command": "python",
      "args": ["/path/to/eva-mcp-server/src/server.py"],
      "env": {
        "EVA_API_URL": "https://eva.s7corp.ru/api",
        "EVA_API_TOKEN": "your_token_here",
        "EVA_READ_ONLY": "true"
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
  - Parameters: `name`, `project_code`, `description`, `responsible`, `priority`
  
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

### Audit Tools

- **eva_get_audit_log**: Get audit log entries
  - Parameters: `entity_code`, `limit`

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

## Safety and Security

### Read-Only Mode

By default, the server runs in read-only mode (`EVA_READ_ONLY=true`). This prevents:
- Creating tasks
- Updating tasks
- Adding comments
- Any other write operations

To enable write operations:
1. Set `EVA_READ_ONLY=false` in your configuration
2. Be cautious when using write operations on production data
3. Always verify the operation before confirming

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

For detailed API documentation, see [API_ANALYSIS.md](API_ANALYSIS.md).

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
- Check Eva-project documentation: https://docs.evateam.ru/
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

