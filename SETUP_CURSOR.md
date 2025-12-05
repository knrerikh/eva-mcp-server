# Eva MCP Server Setup in Cursor

## Step 1: Install Dependencies

```bash
cd eva-mcp-server
py -m pip install -r requirements.txt
```

## Step 2: Configure Environment Variables

Create a `.env` file in the `eva-mcp-server` directory:

```env
EVA_API_URL=https://eva.s7corp.ru/api
EVA_API_TOKEN=your_token_here
EVA_READ_ONLY=true
EVA_TIMEOUT=30
```

## Step 3: Add Configuration to Cursor

1. Open the Cursor MCP configuration file:
   - Windows: `C:\Users\<username>\.cursor\mcp.json`
   - Mac/Linux: `~/.cursor/mcp.json`

2. Add the following configuration:

```json
{
  "mcpServers": {
    "Eva": {
      "command": "py",
      "args": [
        "C:\\path\\to\\eva-mcp-server\\src\\server.py"
      ],
      "env": {
        "EVA_API_URL": "https://your-eva-instance.com/api",
        "EVA_API_TOKEN": "your_token_here",
        "EVA_READ_ONLY": "true",
        "EVA_TIMEOUT": "30"
      }
    }
  }
}
```

**Important:** Replace the path in `args` with the absolute path to your `eva-mcp-server/src/server.py` file.

## Step 4: Restart Cursor

1. Completely close Cursor
2. Open Cursor again
3. The MCP server should start automatically

## Step 5: Verify Operation

In Cursor, you should see available Eva tools:

- `eva_search_tasks` - Search tasks
- `eva_get_task` - Get task
- `eva_list_projects` - List projects
- `eva_get_project` - Get project
- `eva_list_users` - List users
- And more...

## Testing

Try in Cursor:
- "Show me the list of projects in Eva"
- "Find tasks created in January 2025"
- "How many tasks are in the system?"

## Troubleshooting

### Server doesn't start

1. Check Cursor logs (View → Output → MCP)
2. Make sure Python is installed and accessible via `py` command
3. Verify all dependencies are installed
4. Ensure the path in configuration is correct

### API requests don't work

1. Make sure you're connected to S7 corporate network (VPN)
2. Verify that `EVA_API_TOKEN` is valid
3. Check server logs

### Tools don't appear

1. Fully restart Cursor
2. Check JSON syntax in `mcp.json`
3. Make sure the server started without errors

## Security

- Read-only mode is enabled by default (`read_only=true`), which blocks write operations
- To enable create/update operations, set `EVA_READ_ONLY=false`
- **Be careful with write operations on production server!**
