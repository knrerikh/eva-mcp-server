# Getting Started with Eva MCP Server

## Prerequisites

- Python 3.10 or higher
- Access to Eva API (S7 corporate network or VPN)
- Valid Eva API token

## Quick Setup

### 1. Install Dependencies

```bash
cd eva-mcp-server
python -m pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file (optional, can also configure in Cursor):

```env
EVA_API_URL=https://eva.s7corp.ru/api
EVA_API_TOKEN=your_token_here
EVA_READ_ONLY=true
```

### 3. Configure Cursor

**Windows:** Edit `C:\Users\<username>\.cursor\mcp.json`  
**Mac/Linux:** Edit `~/.cursor/mcp.json`

Add this configuration:

```json
{
  "mcpServers": {
    "Eva": {
      "command": "python",
      "args": [
        "C:\\absolute\\path\\to\\eva-mcp-server\\src\\server.py"
      ],
      "env": {
        "EVA_API_URL": "https://eva.s7corp.ru/api",
        "EVA_API_TOKEN": "your_token_here",
        "EVA_READ_ONLY": "true"
      }
    }
  }
}
```

**Important:** Use absolute path to `server.py` file!

### 4. Restart Cursor

1. Close all Cursor windows
2. End all Cursor processes (Task Manager on Windows)
3. Start Cursor again
4. Wait 10-15 seconds for MCP servers to initialize

### 5. Verify Installation

Check logs: **View → Output → MCP**

You should see:
```
============================================================
Starting Eva MCP Server...
============================================================
Initializing Eva MCP Server...
✓ Eva MCP Server ready (read_only=True)
Eva MCP Server started and listening for requests
============================================================
```

### 6. Test the Server

Try these commands in Cursor:

```
"Show me Eva projects"
"Find tasks created in January 2025"
"How many tasks are in the system?"
```

## Available Tools

The server provides 15 tools for interacting with Eva:

**Tasks:**
- `eva_search_tasks` - Search and filter tasks
- `eva_get_task` - Get task details by code
- `eva_count_tasks` - Count tasks with filters
- `eva_create_task` - Create new task (write mode)
- `eva_update_task` - Update existing task (write mode)

**Projects:**
- `eva_list_projects` - List all projects
- `eva_get_project` - Get project details

**Users:**
- `eva_list_users` - List all users
- `eva_get_user` - Get user details

**Documents:**
- `eva_search_documents` - Search documents
- `eva_get_document` - Get document details

**Comments:**
- `eva_get_comments` - Get comments for task/document
- `eva_add_comment` - Add comment (write mode)

**Sprints:**
- `eva_list_sprints` - List sprints/lists
- `eva_get_sprint` - Get sprint details

**Audit:**
- `eva_get_audit_log` - View audit history

## Security

### Read-Only Mode (Default)

By default, the server runs in read-only mode to prevent accidental data modification.

**Blocked operations:**
- Creating tasks
- Updating tasks
- Adding comments
- Any other write operations

### Enabling Write Mode

To enable write operations, set in configuration:

```json
"EVA_READ_ONLY": "false"
```

⚠️ **Warning:** Be careful with write operations on production data!

## Troubleshooting

### Server doesn't start

**Check:**
1. Python is installed: `python --version`
2. Dependencies installed: `pip list | grep mcp`
3. Path in `mcp.json` is correct and absolute
4. Cursor logs (View → Output → MCP)

**Common error:** `ModuleNotFoundError: No module named 'src'`
- **Solution:** Use absolute path to `server.py` in configuration

### API doesn't respond

**Check:**
1. Connected to VPN: `ping eva.s7corp.ru`
2. Token is valid
3. API URL is correct

**Error:** `getaddrinfo failed` or `Cannot connect`
- **Solution:** Connect to S7 corporate network or VPN

### Tools don't appear in Cursor

**Try:**
1. Wait 30 seconds after Cursor starts
2. Fully restart Cursor (close all windows + end processes)
3. Check JSON syntax in `mcp.json`
4. Verify server started without errors in logs

## Next Steps

- Read [Full Documentation](README.md)
- Check [API Analysis](API_ANALYSIS.md)
- See [Contributing Guide](CONTRIBUTING.md)

## Support

- **Issues:** Create an issue on GitHub
- **Documentation:** See [README.md](README.md)
- **Eva API Docs:** https://docs.evateam.ru/

---

**Version:** 0.1.0  
**Status:** ✅ Production Ready

