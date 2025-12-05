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

### Planned

- Async support for better performance
- Caching for frequently accessed data
- Batch operations support
- WebSocket support for real-time updates
- Additional filters and search options
- Rate limiting and retry logic
- Metrics and monitoring
- Docker support
- CI/CD pipeline

