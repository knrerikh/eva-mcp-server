# Quick Start Guide

Quick guide to get started with Eva MCP Server.

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd eva-mcp-server

# 2. Install dependencies
py -m pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

```env
EVA_API_URL=https://eva.s7corp.ru/api
EVA_API_TOKEN=your_token_here
EVA_READ_ONLY=true
```

## Cursor Integration

1. Open file `C:\Users\<username>\.cursor\mcp.json` (Windows) or `~/.cursor/mcp.json` (Mac/Linux)

2. Add configuration:

```json
{
  "mcpServers": {
    "Eva": {
      "command": "py",
      "args": ["C:\\path\\to\\eva-mcp-server\\src\\server.py"],
      "env": {
        "EVA_API_URL": "https://eva.s7corp.ru/api",
        "EVA_API_TOKEN": "your_token_here",
        "EVA_READ_ONLY": "true"
      }
    }
  }
}
```

3. Restart Cursor

## First Steps

Try in Cursor:

```
"Show list of projects in Eva"
"Find tasks created in January 2025"
"How many tasks are in the system?"
```

## Available Tools

### Tasks
- `eva_search_tasks` - Search tasks
- `eva_get_task` - Get task by code
- `eva_count_tasks` - Count tasks
- `eva_create_task` - Create task (requires write mode)
- `eva_update_task` - Update task (requires write mode)

### Projects
- `eva_list_projects` - List projects
- `eva_get_project` - Get project by code

### Users
- `eva_list_users` - List users
- `eva_get_user` - Get user

### Documents
- `eva_search_documents` - Search documents
- `eva_get_document` - Get document

### Comments
- `eva_get_comments` - Get comments
- `eva_add_comment` - Add comment (requires write mode)

### Sprints
- `eva_list_sprints` - List sprints
- `eva_get_sprint` - Get sprint

### Audit
- `eva_get_audit_log` - Get audit log

## Security

⚠️ **Read-only mode is enabled by default**

This prevents accidental data modification. To enable write operations:

```env
EVA_READ_ONLY=false
```

## Requirements

- Python 3.10+
- Access to Eva API (S7 corporate network or VPN)
- Valid API token

## Troubleshooting

**Server doesn't start:**
- Check Cursor logs (View → Output → MCP)
- Make sure Python is installed
- Verify the path in configuration

**API doesn't respond:**
- Connect to corporate network/VPN
- Check API token
- Verify `EVA_API_URL` is correct

**Tools don't appear:**
- Fully restart Cursor
- Check JSON syntax in `mcp.json`
- Check server logs

## Additional Information

- [Full Documentation](README.md)
- [Cursor Setup](SETUP_CURSOR.md)
- [API Analysis](API_ANALYSIS.md)
- [Contributing](CONTRIBUTING.md)
