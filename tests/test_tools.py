"""Tests for Eva MCP tools."""

import pytest
import json
from unittest.mock import Mock, patch
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from tools import EvaTools
from eva_client import EvaClient, EvaAPIError


@pytest.fixture
def mock_client():
    """Create a mock Eva client."""
    client = Mock(spec=EvaClient)
    client.read_only = True
    return client


@pytest.fixture
def eva_tools(mock_client):
    """Create Eva tools instance with mock client."""
    return EvaTools(mock_client)


# Codes an Eva instance would resolve to internal identifiers. Fictional on purpose:
# the repository is public and must carry no real project or task codes.
RESOLVED = {
    "ACME-1": "CmfTask:11111111-1111-1111-1111-111111111111",
    "acme_project": "CmfProject:22222222-2222-2222-2222-222222222222",
    "someone@example.com": "CmfPerson:33333333-3333-3333-3333-333333333333",
    "DOC-1": "CmfDocument:44444444-4444-4444-4444-444444444444",
}


@pytest.fixture
def resolving_client(mock_client):
    """Mock client whose resolve_id behaves like the real one for known codes."""
    def resolve(code, entity="CmfTask"):
        if str(code).startswith("Cmf") and ":" in str(code):
            return code
        if code in RESOLVED:
            return RESOLVED[code]
        raise EvaAPIError(f"Cannot resolve '{code}'", code=500)

    mock_client.resolve_id.side_effect = resolve
    return mock_client


def _filters_of(mock_call):
    """Pull the filter list out of a recorded client call."""
    return mock_call.call_args.kwargs["filters"]


def test_search_tasks_success(eva_tools, mock_client):
    """Test successful task search."""
    mock_client.list_tasks.return_value = [
        {"code": "TASK-1", "name": "Task 1"},
        {"code": "TASK-2", "name": "Task 2"}
    ]
    
    result = eva_tools.search_tasks(query="test", limit=10)
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["count"] == 2
    assert len(result_data["tasks"]) == 2


def test_search_tasks_error(eva_tools, mock_client):
    """Test task search with error."""
    mock_client.list_tasks.side_effect = EvaAPIError("API Error", code=-32600)
    
    result = eva_tools.search_tasks(query="test")
    result_data = json.loads(result)
    
    assert result_data["success"] is False
    assert "API Error" in result_data["error"]


def test_get_task_details_success(eva_tools, mock_client):
    """Test getting task details."""
    mock_client.get_task.return_value = {
        "code": "TASK-123",
        "name": "Test Task",
        "status": "open"
    }
    
    result = eva_tools.get_task_details("TASK-123")
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["task"]["code"] == "TASK-123"


def test_count_tasks_success(eva_tools, resolving_client):
    """Test counting tasks."""
    resolving_client.count_tasks.return_value = 42

    result = eva_tools.count_tasks_by_filter(project="acme_project")
    result_data = json.loads(result)

    assert result_data["success"] is True
    assert result_data["count"] == 42


def test_list_projects_success(eva_tools, mock_client):
    """Test listing projects."""
    mock_client.list_projects.return_value = [
        {"code": "PROJ-1", "name": "Project 1"},
        {"code": "PROJ-2", "name": "Project 2"}
    ]
    
    result = eva_tools.list_projects(limit=10)
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["count"] == 2


def test_get_project_details_success(eva_tools, mock_client):
    """Test getting project details."""
    mock_client.get_project.return_value = {
        "code": "PROJ-1",
        "name": "Test Project"
    }
    
    result = eva_tools.get_project_details("PROJ-1")
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["project"]["code"] == "PROJ-1"


def test_list_users_success(eva_tools, mock_client):
    """Test listing users."""
    mock_client.list_users.return_value = [
        {"code": "user1", "name": "User 1"},
        {"code": "user2", "name": "User 2"}
    ]
    
    result = eva_tools.list_users(limit=50)
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["count"] == 2


def test_search_documents_success(eva_tools, mock_client):
    """Test searching documents."""
    mock_client.list_documents.return_value = [
        {"code": "DOC-1", "name": "Document 1"}
    ]
    
    result = eva_tools.search_documents(query="test")
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["count"] == 1


def test_get_comments_success(eva_tools, resolving_client):
    """Test getting comments."""
    resolving_client.list_comments.return_value = [
        {"code": "COMM-1", "text": "Comment 1"}
    ]

    result = eva_tools.get_comments("ACME-1")
    result_data = json.loads(result)

    assert result_data["success"] is True
    assert result_data["count"] == 1


def test_get_tasks_by_list_success(eva_tools, mock_client):
    """Test listing tasks in a sprint/list."""
    mock_client.get_list.return_value = {
        "id": "CmfList:aa404b17-3d52-11f1-923c-0a580aee2812",
        "code": "LST-002269",
        "cache_members_count": 2,
    }
    mock_client.list_tasks_by_list.return_value = [
        {"code": "FT-1", "name": "Task 1", "text": "<p>Desc 1</p>"},
        {"code": "FT-2", "name": "Task 2", "text": None},
    ]

    result = eva_tools.get_tasks_by_list(list_code="LST-002269")
    result_data = json.loads(result)

    assert result_data["success"] is True
    assert result_data["count"] == 2
    assert result_data["tasks"][0]["text"] == "<p>Desc 1</p>"
    mock_client.list_tasks_by_list.assert_called_once()


def test_get_tasks_by_list_empty_code(eva_tools, mock_client):
    """Test get_tasks_by_list with missing list_code."""
    result = eva_tools.get_tasks_by_list(list_code="")
    result_data = json.loads(result)

    assert result_data["success"] is False
    assert "required" in result_data["error"].lower()
    mock_client.get_list.assert_not_called()


def test_list_sprints_success(eva_tools, mock_client):
    """Test listing sprints."""
    mock_client.list_lists.return_value = [
        {"code": "SPR-1", "name": "Sprint 1"}
    ]
    
    result = eva_tools.list_sprints(limit=50)
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["count"] == 1


def test_create_list_success(eva_tools, mock_client):
    """Test creating list/sprint/release."""
    mock_client.create_list.return_value = {
        "code": "SPR-1",
        "name": "Sprint 1",
        "parent": "CmfProject:proj"
    }
    
    result = eva_tools.create_list(name="Sprint 1", project_code="CmfProject:proj")
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["list"]["code"] == "SPR-1"
    mock_client.create_list.assert_called_once_with(name="Sprint 1", parent="CmfProject:proj")


def test_create_list_error(eva_tools, mock_client):
    """Test creating list with error."""
    mock_client.create_list.side_effect = EvaAPIError("API Error", code=-32600)
    
    result = eva_tools.create_list(name="Sprint 1", project_code="CmfProject:proj")
    result_data = json.loads(result)
    
    assert result_data["success"] is False
    assert "API Error" in result_data["error"]


def test_create_list_validation_empty_name(eva_tools, mock_client):
    """Test creating list with empty name."""
    result = eva_tools.create_list(name="", project_code="CmfProject:proj")
    result_data = json.loads(result)
    
    assert result_data["success"] is False
    assert "required" in result_data["error"].lower()


def test_create_list_validation_empty_project(eva_tools, mock_client):
    """Test creating list with empty project_code."""
    result = eva_tools.create_list(name="Sprint 1", project_code="")
    result_data = json.loads(result)
    
    assert result_data["success"] is False
    assert "required" in result_data["error"].lower()


def test_get_audit_log_success(eva_tools, resolving_client):
    """Test getting audit log."""
    resolving_client.list_audit.return_value = [
        {"code": "AUD-1", "action": "created"}
    ]

    result = eva_tools.get_audit_log(entity_code="ACME-1")
    result_data = json.loads(result)

    assert result_data["success"] is True
    assert result_data["count"] == 1


# --- Defect 2: search filters -------------------------------------------------


def test_search_tasks_uses_uppercase_ilike(eva_tools, resolving_client):
    """Eva rejects lowercase 'ilike' as an invalid filter operation."""
    resolving_client.list_tasks.return_value = []

    eva_tools.search_tasks(query="widget")

    operations = [f[1] for f in _filters_of(resolving_client.list_tasks) if isinstance(f[1], str)]
    assert "ilike" not in operations
    assert all(op.isupper() for op in operations)


def test_search_tasks_searches_name_and_text(eva_tools, resolving_client):
    """A text query matches the description too, not only the title."""
    resolving_client.list_tasks.return_value = []

    eva_tools.search_tasks(query="widget")

    group = _filters_of(resolving_client.list_tasks)[0]
    assert group[0] == "OR"
    fields = {clause[0] for clause in group[1:]}
    assert fields == {"name", "text"}
    assert all(clause[1] == "ILIKE" for clause in group[1:])


def test_search_tasks_resolves_project_to_id(eva_tools, resolving_client):
    """Defect 2: filtering by a project code silently matches nothing."""
    resolving_client.list_tasks.return_value = []

    eva_tools.search_tasks(project="acme_project")

    assert ["parent", "=", RESOLVED["acme_project"]] in _filters_of(resolving_client.list_tasks)


def test_search_tasks_resolves_responsible_to_id(eva_tools, resolving_client):
    """A responsible filter needs the person id, not the login."""
    resolving_client.list_tasks.return_value = []

    eva_tools.search_tasks(responsible="someone@example.com")

    assert ["responsible", "=", RESOLVED["someone@example.com"]] in _filters_of(
        resolving_client.list_tasks
    )


def test_search_tasks_status_type_uses_cache_status_type(eva_tools, resolving_client):
    """Status *types* live in cache_status_type; 'status' is a relation."""
    resolving_client.list_tasks.return_value = []

    eva_tools.search_tasks(status="OPEN")

    assert ["cache_status_type", "=", "OPEN"] in _filters_of(resolving_client.list_tasks)


def test_search_tasks_status_name_uses_relation_path(eva_tools, resolving_client):
    """A named status is matched through the status relation."""
    resolving_client.list_tasks.return_value = []

    eva_tools.search_tasks(status="Backlog")

    assert ["status.name", "=", "Backlog"] in _filters_of(resolving_client.list_tasks)


def test_search_tasks_reports_unresolvable_project(eva_tools, resolving_client):
    """An unknown project code fails loudly instead of returning an empty list."""
    resolving_client.list_tasks.return_value = []

    result = json.loads(eva_tools.search_tasks(project="no_such_project"))

    assert result["success"] is False
    assert "no_such_project" in result["error"]
    resolving_client.list_tasks.assert_not_called()


def test_count_tasks_resolves_project_to_id(eva_tools, resolving_client):
    """count_tasks_by_filter shares the resolving path with search."""
    resolving_client.count_tasks.return_value = 42

    eva_tools.count_tasks_by_filter(project="acme_project")

    assert ["parent", "=", RESOLVED["acme_project"]] in _filters_of(resolving_client.count_tasks)


def test_search_documents_resolves_project_and_uses_ilike(eva_tools, resolving_client):
    """Documents suffer from the same two defects as tasks."""
    resolving_client.list_documents.return_value = []

    eva_tools.search_documents(query="widget", project="acme_project")

    filters = _filters_of(resolving_client.list_documents)
    assert ["parent", "=", RESOLVED["acme_project"]] in filters
    assert any(f[0] == "OR" for f in filters)


# --- Defect 3: comments -------------------------------------------------------


def test_get_comments_resolves_parent_to_id(eva_tools, resolving_client):
    """Defect 3: CmfComment.parent holds an entity id, so a code matches nothing."""
    resolving_client.list_comments.return_value = []

    eva_tools.get_comments("ACME-1")

    assert _filters_of(resolving_client.list_comments) == [
        ["parent", "=", RESOLVED["ACME-1"]]
    ]


def test_get_comments_accepts_document_parent(eva_tools, resolving_client):
    """Comments hang off documents as well as tasks."""
    resolving_client.list_comments.return_value = []

    eva_tools.get_comments("DOC-1")

    assert _filters_of(resolving_client.list_comments) == [
        ["parent", "=", RESOLVED["DOC-1"]]
    ]


def test_add_comment_resolves_parent_to_id(eva_tools, resolving_client):
    """The API spec addresses a comment parent by entity id."""
    resolving_client.create_comment.return_value = {"id": "CmfComment:abc"}

    eva_tools.add_comment(parent_code="ACME-1", text="<p>Hi</p>")

    assert resolving_client.create_comment.call_args.kwargs["parent"] == RESOLVED["ACME-1"]


def test_get_audit_log_filters_by_resolved_parent(eva_tools, resolving_client):
    """CmfAudit has no object_code field; entries hang off 'parent'."""
    resolving_client.list_audit.return_value = []

    eva_tools.get_audit_log(entity_code="ACME-1")

    assert _filters_of(resolving_client.list_audit) == [
        ["parent", "=", RESOLVED["ACME-1"]]
    ]


# --- Double-escaped HTML guard ------------------------------------------------


def test_create_task_repairs_double_escaped_html(eva_tools, resolving_client):
    """A description with no '<' but with '&lt;' is a caller mistake, not content."""
    resolving_client.create_task.return_value = {"code": "ACME-2"}

    result = json.loads(
        eva_tools.create_task(name="Task", description="&lt;p&gt;Hello&lt;/p&gt;")
    )

    assert resolving_client.create_task.call_args.kwargs["text"] == "<p>Hello</p>"
    assert result["html_unescaped"] is True


def test_create_task_leaves_raw_html_alone(eva_tools, resolving_client):
    """Genuine markup passes through untouched."""
    resolving_client.create_task.return_value = {"code": "ACME-2"}

    result = json.loads(
        eva_tools.create_task(name="Task", description="<p>5 &lt; 7</p>")
    )

    assert resolving_client.create_task.call_args.kwargs["text"] == "<p>5 &lt; 7</p>"
    assert "html_unescaped" not in result


def test_add_comment_repairs_double_escaped_html(eva_tools, resolving_client):
    """The same guard protects comment text."""
    resolving_client.create_comment.return_value = {"id": "CmfComment:abc"}

    eva_tools.add_comment(parent_code="ACME-1", text="&lt;p&gt;Hello&lt;/p&gt;")

    assert resolving_client.create_comment.call_args.kwargs["text"] == "<p>Hello</p>"


def test_update_task_repairs_double_escaped_html(eva_tools, resolving_client):
    """And the update path, which is how a damaged description gets repaired."""
    resolving_client.update_task.return_value = "CmfTask:abc"

    eva_tools.update_task(task_code="ACME-1", description="&lt;p&gt;Hello&lt;/p&gt;")

    assert resolving_client.update_task.call_args.kwargs["text"] == "<p>Hello</p>"

