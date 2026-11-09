# Changelog

All notable changes to Eva MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-12-05

### Added

- Initial release of Eva MCP Server
- Eva API client with JSON-RPC 2.0 support
- MCP server implementation using MCP SDK
- 17 MCP tools for Eva API interaction:
  - Task management (search, get, count, create, update)
  - Project management (list, get)
  - User management (list, get)
  - Document management (search, get)
  - Comment management (get, add)
  - Sprint/List management (list, get)
  - Audit log access
- Read-only mode for safe operations (enabled by default)
- Comprehensive test suite with pytest
- Full documentation (README, API analysis)
- OpenAPI specification included
- Environment-based configuration
- Error handling and logging
- Context manager support for client

### Security

- Read-only mode prevents accidental data modification
- API token stored in environment variables
- No hardcoded credentials

### Documentation

- Complete README with installation and usage instructions
- API analysis document
- Code examples
- Troubleshooting guide
- Development guidelines

## [Unreleased]

### Added

- `eva_create_list` tool to create sprints/lists
- `eva_get_tasks_by_list` tool to list the tasks of a sprint/list
- `eva_log_time` tool to log time on a task
- `eva_find_tags` and `eva_create_tag` tools to resolve and create tags
- `eva_get_task`: `extra_fields` parameter to return additional Eva fields, e.g. tags
- `eva_update_task`: `fields` parameter to send raw Eva fields, e.g. a tag id list
- `lists` parameter when creating tasks

### Changed

- Read-only mode is now off by default
- `eva_get_comments` returns the newest comments first within `limit`, in chronological order
- `eva_add_comment` reads the stored comment back and returns its id
- `mcp` dependency is capped below 2.0

### Fixed

- `eva_update_task` failed on every call; task, project and list codes are now resolved to Eva ids
- Text search, and project, responsible and status filters, returned errors or empty results
- `eva_get_comments` returned an empty list for tasks with comments and omitted comment text, author and date
- `eva_get_audit_log` filtered by a field that audit entries do not have
- `read_only` setting from the environment was ignored

### Removed

- Unused HTTP wrapper (`src/http_server.py`)

### Planned

- Async support for better performance
- Caching for frequently accessed data
- Batch operations support
- WebSocket support for real-time updates
- Additional filters and search options
- Rate limiting and retry logic
- Metrics and monitoring
- Docker support

