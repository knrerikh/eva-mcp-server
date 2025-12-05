# Eva API Analysis

## API Overview

- **Protocol**: JSON-RPC 2.0
- **Base URL**: `https://eva.s7corp.ru/api` (production) or `https://test.evateam.ru` (test)
- **Authentication**: Bearer token in headers
- **Request Format**: POST requests with JSON-RPC 2.0 structure

## Request Structure

```json
{
  "jsonrpc": "2.2",
  "method": "EntityName.operation",
  "callid": "uuid-v4",
  "kwargs": {
    // operation-specific parameters
  }
}
```

## Available Entities

Based on the OpenAPI specification, the following entities are available:

### 1. CmfTask (Tasks)
- `CmfTask.create` - Create a new task
- `CmfTask.update` - Update an existing task
- `CmfTask.get` - Get task details
- `CmfTask.list` - List tasks with filters
- `CmfTask.count` - Count tasks
- `CmfTask.create_task_from_template` - Create task from template
- `CmfTask.fix_versions.append` - Append fix versions

### 2. CmfDocument (Documents)
- `CmfDocument.create` - Create a document
- `CmfDocument.update` - Update a document
- `CmfDocument.get` - Get document details
- `CmfDocument.list` - List documents
- `CmfDocument.count` - Count documents
- `CmfDocument.do_publish` - Publish a document
- `CmfDocument.download_all_attachment` - Download all attachments

### 3. CmfProject (Projects)
- `CmfProject.create` - Create a project
- `CmfProject.update` - Update a project
- `CmfProject.get` - Get project details
- `CmfProject.list` - List projects
- `CmfProject.count` - Count projects

### 4. CmfList (Lists/Sprints)
- `CmfList.create` - Create a list
- `CmfList.update` - Update a list
- `CmfList.get` - Get list details
- `CmfList.list` - List all lists
- `CmfList.count` - Count lists

### 5. CmfPerson (Users)
- `CmfPerson.create` - Create a user
- `CmfPerson.update` - Update a user
- `CmfPerson.get` - Get user details
- `CmfPerson.list` - List users
- `CmfPerson.count` - Count users
- `CmfPerson.set_avatar` - Set user avatar

### 6. CmfAttachment (Attachments)
- `CmfAttachment.create` - Create an attachment
- `CmfAttachment.update` - Update an attachment
- `CmfAttachment.get` - Get attachment details
- `CmfAttachment.list` - List attachments
- `CmfAttachment.count` - Count attachments

### 7. CmfAudit (Audit Log)
- `CmfAudit.get` - Get audit entry
- `CmfAudit.list` - List audit entries
- `CmfAudit.count` - Count audit entries

### 8. CmfComment (Comments)
- `CmfComment.create` - Create a comment
- `CmfComment.update` - Update a comment
- `CmfComment.get` - Get comment details
- `CmfComment.list` - List comments
- `CmfComment.count` - Count comments

### 9. CmfCompany (Companies)
- `CmfCompany.create` - Create a company
- `CmfCompany.update` - Update a company
- `CmfCompany.get` - Get company details
- `CmfCompany.list` - List companies
- `CmfCompany.count` - Count companies

### 10. CmfGanttTask (Gantt Tasks)
- `CmfGanttTask.update` - Update Gantt task

### 11. CmfLogicType (Logic Types)
- `CmfLogicType.create` - Create a logic type
- `CmfLogicType.update` - Update a logic type
- `CmfLogicType.get` - Get logic type details
- `CmfLogicType.list` - List logic types
- `CmfLogicType.count` - Count logic types

### 12. CmfNotepad (Notepads)
- `CmfNotepad.create` - Create a notepad
- `CmfNotepad.update` - Update a notepad
- `CmfNotepad.get` - Get notepad details
- `CmfNotepad.list` - List notepads
- `CmfNotepad.count` - Count notepads

### 13. CmfRelationOption (Relation Options)
- `CmfRelationOption.create` - Create a relation option
- `CmfRelationOption.update` - Update a relation option
- `CmfRelationOption.get` - Get relation option details
- `CmfRelationOption.list` - List relation options
- `CmfRelationOption.count` - Count relation options

### 14. CmfStatusHistory (Status History)
- `CmfStatusHistory.get` - Get status history entry
- `CmfStatusHistory.list` - List status history
- `CmfStatusHistory.count` - Count status history entries

### 15. CmfTimeTrackerHistory (Time Tracker History)
- `CmfTimeTrackerHistory.list` - List time tracker history
- `CmfTimeTrackerHistory.count` - Count time tracker entries

## Priority MCP Tools to Implement

### High Priority (Read Operations - Safe)
1. **Search Tasks** - Search and filter tasks
2. **Get Task** - Get detailed task information
3. **List Tasks** - List tasks with pagination
4. **Get Project** - Get project details
5. **List Projects** - List all projects
6. **Get User** - Get user information
7. **List Users** - List all users
8. **Search Documents** - Search documents
9. **Get Document** - Get document details

### Medium Priority (Read Operations)
10. **List Comments** - Get comments for a task/document
11. **Get Audit Log** - View audit history
12. **List Lists/Sprints** - Get available lists/sprints
13. **Count Tasks** - Get task counts with filters

### Low Priority (Write Operations - Requires Caution)
14. **Create Task** - Create a new task (with confirmation)
15. **Update Task** - Update task details (with confirmation)
16. **Create Comment** - Add a comment (with confirmation)
17. **Update Document** - Update document (with confirmation)

## Authentication

The API uses Bearer token authentication. The token should be passed in the Authorization header:

```
Authorization: Bearer <token>
```

## Error Handling

JSON-RPC 2.0 error responses:
```json
{
  "jsonrpc": "2.2",
  "error": {
    "code": -32600,
    "message": "Invalid Request"
  },
  "id": null
}
```

## Implementation Notes

1. All write operations should be wrapped with read-only mode check
2. Implement retry logic for network errors
3. Add request/response logging for debugging
4. Use UUID v4 for callid generation
5. Implement proper error handling for JSON-RPC errors
6. Cache frequently accessed data (projects, users) to reduce API calls

