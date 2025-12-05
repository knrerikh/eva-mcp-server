# Publishing Eva MCP Server to GitHub

## Option 1: Create Separate Repository (Recommended)

Eva MCP Server should be in its own repository.

### Steps:

1. **Create new GitHub repository:**
   - Go to https://github.com/new
   - Repository name: `eva-mcp-server`
   - Description: `MCP Server for Eva-project API integration`
   - Public or Private (your choice)
   - **DO NOT** add README, .gitignore, or LICENSE (already exist)
   - Click "Create repository"

2. **Initialize git in project:**

```bash
cd C:\Users\k.rerikh\Repos\personal\eva-mcp-server

# Remove existing git (it's from parent repo)
rmdir /s /q .git

# Initialize new git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Eva MCP Server v0.1.0

- Eva API client with JSON-RPC 2.0 support
- MCP server with 15 tools
- Complete documentation in English
- Unit tests (24 tests)
- Read-only mode for safety
- Cursor integration ready"
```

3. **Connect to GitHub and push:**

```bash
# Add your GitHub repository as remote
git remote add origin https://github.com/YOUR_USERNAME/eva-mcp-server.git

# Rename branch to main
git branch -M main

# Push to GitHub
git push -u origin main
```

4. **Create release (optional but recommended):**
   - Go to your repository on GitHub
   - Click "Releases" → "Create a new release"
   - Tag: `v0.1.0`
   - Title: `Eva MCP Server v0.1.0`
   - Description:
     ```
     Initial release of Eva MCP Server
     
     ## Features
     - 15 MCP tools for Eva-project API
     - Read-only mode by default
     - Complete documentation
     - Unit tests
     - Cursor integration
     
     ## Installation
     See [GETTING_STARTED.md](GETTING_STARTED.md) for setup instructions.
     ```
   - Click "Publish release"

## Option 2: Add to Existing Personal Repository

If you want to keep it in your personal monorepo:

```bash
cd C:\Users\k.rerikh\Repos\personal

# Create new branch for Eva MCP Server
git checkout -b feature/eva-mcp-server

# Add all Eva MCP Server files
git add eva-mcp-server/

# Commit
git commit -m "Add Eva MCP Server

- MCP server for Eva-project API integration
- 15 tools for tasks, projects, users, etc.
- Complete English documentation
- Unit tests
- Cursor integration"

# Push to origin
git push -u origin feature/eva-mcp-server
```

Then create a Pull Request on GitHub.

## After Publishing

### Update README

Add badges to README.md:

```markdown
# Eva MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)
```

### Add Topics

On GitHub repository page, add topics:
- `mcp`
- `mcp-server`
- `eva-project`
- `cursor`
- `claude`
- `ai-assistant`
- `python`
- `json-rpc`

### Share

- Share on social media
- Add to MCP servers list
- Share with team

## Verification Checklist

Before publishing, verify:

- [ ] All sensitive data removed (tokens, passwords)
- [ ] .gitignore properly configured
- [ ] All documentation in English
- [ ] Tests passing
- [ ] LICENSE file present
- [ ] README.md complete
- [ ] No temporary files included

## Post-Publication

1. **Test installation:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/eva-mcp-server.git
   cd eva-mcp-server
   pip install -r requirements.txt
   ```

2. **Update documentation** if needed

3. **Monitor issues** on GitHub

4. **Accept contributions** following CONTRIBUTING.md

---

**Recommended:** Option 1 (Separate Repository)

This keeps Eva MCP Server independent and easier to maintain.

