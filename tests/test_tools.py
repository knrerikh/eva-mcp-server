"""Tests for Eva MCP tools.

These tests assert what the tools *send*, not only that they returned success.
Eva answers a filter it cannot satisfy with an empty result and no error, so a
test that checks `success` and `count` alone passes just as happily on a filter
built against the wrong field or the wrong namespace. The request payload is the
thing under test.
"""

import json

import pytest
from fixtures import (
    AUDIT_ROW_DENIED,
    CMF_PERSON,
    CMF_STATUS,
    COMMENT_ID,
    COMMENT_ROW,
    COMMENT_ROW_NEWER,
    DOCUMENT_CODE,
    DOCUMENT_ID,
    LIST_CODE,
    LIST_ID,
    LIST_ROW,
    PERSON_ID,
    PERSON_LOGIN,
    PROJECT_CODE,
    PROJECT_ID,
    PROJECT_ROW,
    TASK_CODE,
    TASK_DEFAULT_FIELDS,
    TASK_DETAILED,
    TASK_ID,
    filters_of,
)

from eva_client import EvaAPIError
from tools import TASK_DETAIL_FIELDS

UNRESOLVABLE = "no_such_code"


# --- Task search -------------------------------------------------------------


def test_search_tasks_success(eva_tools, mock_client):
    """A text query searches title and description with an upper-case operation."""
    mock_client.list_tasks.return_value = [
        {"code": "ACME-1", "name": "Task 1"},
        {"code": "ACME-2", "name": "Task 2"},
    ]

    result_data = json.loads(eva_tools.search_tasks(query="widget", limit=10))

    assert result_data["success"] is True
    assert result_data["count"] == 2
    assert filters_of(mock_client.list_tasks) == [
        ["OR", ["name", "ILIKE", "%widget%"], ["text", "ILIKE", "%widget%"]]
    ]
    assert mock_client.list_tasks.call_args.kwargs["limit"] == 10


def test_search_tasks_error(eva_tools, mock_client):
    """An API error is reported rather than swallowed."""
    mock_client.list_tasks.side_effect = EvaAPIError("API Error", code=-32600)

    result_data = json.loads(eva_tools.search_tasks(query="widget"))

    assert result_data["success"] is False
    assert "API Error" in result_data["error"]


def test_search_tasks_uses_uppercase_ilike(eva_tools, mock_client):
    """Eva rejects lowercase 'ilike' as an invalid filter operation."""
    mock_client.list_tasks.return_value = []

    eva_tools.search_tasks(query="widget")

    group = filters_of(mock_client.list_tasks)[0]
    assert all(clause[1] == "ILIKE" for clause in group[1:])


def test_search_tasks_searches_name_and_text(eva_tools, mock_client):
    """A query matches the description too, not only the title."""
    mock_client.list_tasks.return_value = []

    eva_tools.search_tasks(query="widget")

    group = filters_of(mock_client.list_tasks)[0]
    assert group[0] == "OR"
    assert {clause[0] for clause in group[1:]} == {"name", "text"}


def test_search_tasks_resolves_project_to_id(eva_tools, resolving_client):
    """A project code in a relation filter silently matches nothing."""
    resolving_client.list_tasks.return_value = []

    eva_tools.search_tasks(project=PROJECT_CODE)

    assert ["parent", "=", PROJECT_ID] in filters_of(resolving_client.list_tasks)


def test_search_tasks_resolves_responsible_to_id(eva_tools, resolving_client):
    """A responsible filter needs the person id, not the login."""
    resolving_client.list_tasks.return_value = []

    eva_tools.search_tasks(responsible=PERSON_LOGIN)

    assert ["responsible", "=", PERSON_ID] in filters_of(resolving_client.list_tasks)


def test_search_tasks_status_type_uses_cache_status_type(eva_tools, mock_client):
    """Status *types* live in cache_status_type; 'status' is a relation."""
    mock_client.list_tasks.return_value = []

    eva_tools.search_tasks(status=CMF_STATUS["status_type"])

    assert ["cache_status_type", "=", "OPEN"] in filters_of(mock_client.list_tasks)


def test_search_tasks_status_name_uses_relation_path(eva_tools, mock_client):
    """A named status is matched through the status relation."""
    mock_client.list_tasks.return_value = []

    eva_tools.search_tasks(status=CMF_STATUS["name"])

    assert ["status.name", "=", "Backlog"] in filters_of(mock_client.list_tasks)


def test_search_tasks_combines_filters(eva_tools, resolving_client):
    """Several filters are ANDed, with the text query as one OR group among them."""
    resolving_client.list_tasks.return_value = []

    eva_tools.search_tasks(query="widget", project=PROJECT_CODE, status="OPEN")

    filters = filters_of(resolving_client.list_tasks)
    assert ["parent", "=", PROJECT_ID] in filters
    assert ["cache_status_type", "=", "OPEN"] in filters
    assert sum(1 for f in filters if f[0] == "OR") == 1


# --- Silent-zero guard -------------------------------------------------------


@pytest.mark.parametrize(
    "call_tool, guarded_method",
    [
        (lambda t: t.search_tasks(project=UNRESOLVABLE), "list_tasks"),
        (lambda t: t.search_tasks(responsible=UNRESOLVABLE), "list_tasks"),
        (lambda t: t.count_tasks_by_filter(project=UNRESOLVABLE), "count_tasks"),
        (lambda t: t.count_tasks_by_filter(responsible=UNRESOLVABLE), "count_tasks"),
        (lambda t: t.search_documents(project=UNRESOLVABLE), "list_documents"),
        (lambda t: t.get_comments(UNRESOLVABLE), "list_comments"),
        (lambda t: t.add_comment(parent_code=UNRESOLVABLE, text="<p>x</p>"), "create_comment"),
        (lambda t: t.get_audit_log(entity_code=UNRESOLVABLE), "list_audit"),
    ],
    ids=[
        "search_tasks-project",
        "search_tasks-responsible",
        "count_tasks-project",
        "count_tasks-responsible",
        "search_documents-project",
        "get_comments-parent",
        "add_comment-parent",
        "get_audit_log-entity",
    ],
)
def test_unresolvable_code_fails_loudly(eva_tools, resolving_client, call_tool, guarded_method):
    """A code that resolves to nothing is an error, never an empty result.

    This is the defect class the suite was blind to: Eva answers a filter on an
    unresolvable code with an empty list and no error, so the tool must refuse
    before it ever reaches the API.
    """
    result_data = json.loads(call_tool(eva_tools))

    assert result_data["success"] is False
    assert UNRESOLVABLE in result_data["error"]
    getattr(resolving_client, guarded_method).assert_not_called()


# --- Task details ------------------------------------------------------------


def test_get_task_details_success(eva_tools, mock_client):
    """Task details are requested with an explicit field list.

    ``CmfTask.get`` omits the description unless the fields are named, so the
    tool has to ask for them; the fixture keeps the real relation shapes.
    """
    mock_client.get_task.return_value = TASK_DETAILED

    result_data = json.loads(eva_tools.get_task_details(TASK_CODE))

    assert result_data["success"] is True
    assert result_data["task"]["code"] == TASK_CODE
    assert result_data["task"]["status"]["status_type"] == "OPEN"

    mock_client.get_task.assert_called_once_with(TASK_CODE, fields=TASK_DETAIL_FIELDS)
    assert "text" in mock_client.get_task.call_args.kwargs["fields"]


def test_task_default_response_omits_description(eva_tools, mock_client):
    """Guard the reason the field list exists at all."""
    assert "text" not in TASK_DEFAULT_FIELDS
    assert "text" in TASK_DETAIL_FIELDS


def test_count_tasks_success(eva_tools, resolving_client):
    """Counting shares the resolving path with search."""
    resolving_client.count_tasks.return_value = 42

    result_data = json.loads(eva_tools.count_tasks_by_filter(project=PROJECT_CODE))

    assert result_data["success"] is True
    assert result_data["count"] == 42
    assert ["parent", "=", PROJECT_ID] in filters_of(resolving_client.count_tasks)


# --- Projects and users ------------------------------------------------------


def test_list_projects_success(eva_tools, mock_client):
    """Test listing projects."""
    mock_client.list_projects.return_value = [PROJECT_ROW]

    result_data = json.loads(eva_tools.list_projects(limit=10))

    assert result_data["success"] is True
    assert result_data["count"] == 1
    mock_client.list_projects.assert_called_once_with(limit=10)


def test_get_project_details_success(eva_tools, mock_client):
    """Test getting project details."""
    mock_client.get_project.return_value = PROJECT_ROW

    result_data = json.loads(eva_tools.get_project_details(PROJECT_CODE))

    assert result_data["success"] is True
    assert result_data["project"]["code"] == PROJECT_CODE
    mock_client.get_project.assert_called_once_with(PROJECT_CODE)


def test_list_users_success(eva_tools, mock_client):
    """Test listing users."""
    mock_client.list_users.return_value = [{"code": PERSON_LOGIN, "name": "Test Person"}]

    result_data = json.loads(eva_tools.list_users(limit=50))

    assert result_data["success"] is True
    assert result_data["count"] == 1
    mock_client.list_users.assert_called_once_with(limit=50)


# --- Documents ---------------------------------------------------------------


def test_search_documents_success(eva_tools, mock_client):
    """Documents are searched by title and body, like tasks."""
    mock_client.list_documents.return_value = [{"code": DOCUMENT_CODE, "name": "Document 1"}]

    result_data = json.loads(eva_tools.search_documents(query="widget"))

    assert result_data["success"] is True
    assert result_data["count"] == 1
    assert filters_of(mock_client.list_documents) == [
        ["OR", ["name", "ILIKE", "%widget%"], ["text", "ILIKE", "%widget%"]]
    ]


def test_search_documents_resolves_project(eva_tools, resolving_client):
    """Documents suffer from the same relation-filter defect as tasks."""
    resolving_client.list_documents.return_value = []

    eva_tools.search_documents(query="widget", project=PROJECT_CODE)

    assert ["parent", "=", PROJECT_ID] in filters_of(resolving_client.list_documents)


# --- Comments ----------------------------------------------------------------


def test_get_comments_success(eva_tools, resolving_client):
    """A comment parent is matched by identifier, so the code is resolved first."""
    resolving_client.list_comments.return_value = [COMMENT_ROW]

    result_data = json.loads(eva_tools.get_comments(TASK_CODE))

    assert result_data["success"] is True
    assert result_data["count"] == 1
    assert result_data["parent_id"] == TASK_ID
    assert filters_of(resolving_client.list_comments) == [["parent", "=", TASK_ID]]
    assert resolving_client.list_comments.call_args.kwargs["limit"] == 50


def test_get_comments_accepts_document_parent(eva_tools, resolving_client):
    """Comments hang off documents as well as tasks."""
    resolving_client.list_comments.return_value = []

    eva_tools.get_comments(DOCUMENT_CODE)

    assert filters_of(resolving_client.list_comments) == [["parent", "=", DOCUMENT_ID]]


def test_add_comment_resolves_parent_to_id(eva_tools, resolving_client):
    """The API spec addresses a comment parent by entity id."""
    resolving_client.create_comment.return_value = {"id": COMMENT_ROW["id"]}
    resolving_client.get_comment.return_value = COMMENT_ROW

    eva_tools.add_comment(parent_code=TASK_CODE, text="<p>Hi</p>")

    assert resolving_client.create_comment.call_args.kwargs["parent"] == TASK_ID


# --- Sprints and lists -------------------------------------------------------


def test_get_tasks_by_list_success(eva_tools, mock_client):
    """Test listing tasks in a sprint/list."""
    mock_client.get_list.return_value = LIST_ROW
    mock_client.list_tasks_by_list.return_value = [
        {"code": "ACME-1", "name": "Task 1", "text": "<p>Desc 1</p>"},
        {"code": "ACME-2", "name": "Task 2", "text": None},
    ]

    result_data = json.loads(eva_tools.get_tasks_by_list(list_code=LIST_CODE))

    assert result_data["success"] is True
    assert result_data["count"] == 2
    assert result_data["list_id"] == LIST_ID
    assert result_data["tasks"][0]["text"] == "<p>Desc 1</p>"
    assert mock_client.list_tasks_by_list.call_args.kwargs["list_code"] == LIST_CODE
    assert mock_client.list_tasks_by_list.call_args.kwargs["fields"] == TASK_DETAIL_FIELDS


def test_get_tasks_by_list_empty_code(eva_tools, mock_client):
    """Test get_tasks_by_list with missing list_code."""
    result_data = json.loads(eva_tools.get_tasks_by_list(list_code=""))

    assert result_data["success"] is False
    assert "required" in result_data["error"].lower()
    mock_client.get_list.assert_not_called()


def test_list_sprints_success(eva_tools, mock_client):
    """Test listing sprints."""
    mock_client.list_lists.return_value = [LIST_ROW]

    result_data = json.loads(eva_tools.list_sprints(limit=50))

    assert result_data["success"] is True
    assert result_data["count"] == 1
    mock_client.list_lists.assert_called_once_with(limit=50)


def test_create_list_success(eva_tools, mock_client):
    """Test creating list/sprint/release."""
    mock_client.create_list.return_value = LIST_ROW

    result_data = json.loads(eva_tools.create_list(name="Test Sprint", project_code=PROJECT_ID))

    assert result_data["success"] is True
    assert result_data["list"]["code"] == LIST_CODE
    mock_client.create_list.assert_called_once_with(name="Test Sprint", parent=PROJECT_ID)


def test_create_list_error(eva_tools, mock_client):
    """Test creating list with error."""
    mock_client.create_list.side_effect = EvaAPIError("API Error", code=-32600)

    result_data = json.loads(eva_tools.create_list(name="Test Sprint", project_code=PROJECT_ID))

    assert result_data["success"] is False
    assert "API Error" in result_data["error"]


def test_create_list_validation_empty_name(eva_tools, mock_client):
    """Test creating list with empty name."""
    result_data = json.loads(eva_tools.create_list(name="", project_code=PROJECT_ID))

    assert result_data["success"] is False
    assert "required" in result_data["error"].lower()
    mock_client.create_list.assert_not_called()


def test_create_list_validation_empty_project(eva_tools, mock_client):
    """Test creating list with empty project_code."""
    result_data = json.loads(eva_tools.create_list(name="Test Sprint", project_code=""))

    assert result_data["success"] is False
    assert "required" in result_data["error"].lower()
    mock_client.create_list.assert_not_called()


# --- Audit -------------------------------------------------------------------


def test_get_audit_log_success(eva_tools, resolving_client):
    """CmfAudit has no object_code field; entries hang off 'parent' by id."""
    resolving_client.list_audit.return_value = [AUDIT_ROW_DENIED]

    result_data = json.loads(eva_tools.get_audit_log(entity_code=TASK_CODE))

    assert result_data["success"] is True
    assert result_data["count"] == 1
    assert filters_of(resolving_client.list_audit) == [["parent", "=", TASK_ID]]


def test_get_audit_log_tolerates_acl_denied_rows(eva_tools, resolving_client):
    """An entry may be found and still withhold every field."""
    resolving_client.list_audit.return_value = [AUDIT_ROW_DENIED]

    result_data = json.loads(eva_tools.get_audit_log(entity_code=TASK_CODE))

    assert result_data["success"] is True
    assert result_data["audit_log"][0]["_acl_obj"] == "deny"


# --- Raw HTML guard ----------------------------------------------------------


def test_create_task_repairs_double_escaped_html(eva_tools, mock_client):
    """A description with no '<' but with '&lt;' is a caller mistake, not content."""
    mock_client.create_task.return_value = {"code": "ACME-2"}

    result_data = json.loads(
        eva_tools.create_task(name="Task", description="&lt;p&gt;Hello&lt;/p&gt;")
    )

    assert mock_client.create_task.call_args.kwargs["text"] == "<p>Hello</p>"
    assert result_data["html_unescaped"] is True


def test_create_task_leaves_raw_html_alone(eva_tools, mock_client):
    """Genuine markup passes through untouched."""
    mock_client.create_task.return_value = {"code": "ACME-2"}

    result_data = json.loads(eva_tools.create_task(name="Task", description="<p>5 &lt; 7</p>"))

    assert mock_client.create_task.call_args.kwargs["text"] == "<p>5 &lt; 7</p>"
    assert "html_unescaped" not in result_data


def test_add_comment_repairs_double_escaped_html(eva_tools, resolving_client):
    """The same guard protects comment text."""
    resolving_client.create_comment.return_value = {"id": COMMENT_ROW["id"]}
    resolving_client.get_comment.return_value = COMMENT_ROW

    eva_tools.add_comment(parent_code=TASK_CODE, text="&lt;p&gt;Hello&lt;/p&gt;")

    assert resolving_client.create_comment.call_args.kwargs["text"] == "<p>Hello</p>"


def test_update_task_repairs_double_escaped_html(eva_tools, mock_client):
    """And the update path, which is how a damaged description gets repaired."""
    mock_client.update_task.return_value = TASK_ID

    eva_tools.update_task(task_code=TASK_CODE, description="&lt;p&gt;Hello&lt;/p&gt;")

    assert mock_client.update_task.call_args.kwargs["text"] == "<p>Hello</p>"


def test_update_task_requires_a_field(eva_tools, mock_client):
    """An update with nothing to change is refused rather than sent."""
    result_data = json.loads(eva_tools.update_task(task_code=TASK_CODE))

    assert result_data["success"] is False
    mock_client.update_task.assert_not_called()


# --- Comment bodies ----------------------------------------------------------


def test_get_comments_asks_for_the_body(eva_tools, resolving_client):
    """Without an explicit field list Eva returns no text at all.

    The default CmfComment response carries id, parent, owner id and two nulls.
    A caller can count comments with it and cannot read one, which is how a
    thread stayed unreadable through MCP while `count` looked healthy.
    """
    resolving_client.list_comments.return_value = []

    eva_tools.get_comments(TASK_CODE)

    requested = resolving_client.list_comments.call_args.kwargs["fields"]
    assert "text" in requested
    assert "cmf_created_at" in requested
    assert "cmf_owner" in requested


def test_get_comments_returns_text_author_and_date(eva_tools, resolving_client):
    """What the tool returns is what a reader needs to follow a discussion."""
    resolving_client.list_comments.return_value = [COMMENT_ROW]

    result = json.loads(eva_tools.get_comments(TASK_CODE))
    comment = result["comments"][0]

    assert comment["text"] == "<p>Test comment</p>"
    assert comment["cmf_owner"]["name"] == CMF_PERSON["name"]
    assert comment["cmf_created_at"]


def test_get_comments_reads_oldest_first(eva_tools, resolving_client):
    """A thread reads in the order it was written.

    Eva is asked for the newest first, so that a `limit` keeps the most recent
    comments rather than the oldest ones, and the page is then reversed so the
    conversation still reads top to bottom.
    """
    resolving_client.list_comments.return_value = [COMMENT_ROW_NEWER, COMMENT_ROW]

    result = json.loads(eva_tools.get_comments(TASK_CODE))

    assert resolving_client.list_comments.call_args.kwargs["order_by"] == ["-cmf_created_at"]
    dates = [c["cmf_created_at"] for c in result["comments"]]
    assert dates == sorted(dates)


def test_add_comment_returns_what_was_stored(eva_tools, resolving_client):
    """Creating a comment answers with an id; the caller cannot check the text.

    The tool reads the comment back so the response shows what Eva actually
    kept — the same round trip that revealed HTML arriving escaped.
    """
    resolving_client.create_comment.return_value = COMMENT_ID
    resolving_client.get_comment.return_value = COMMENT_ROW

    result = json.loads(eva_tools.add_comment(parent_code=TASK_CODE, text="<p>Test comment</p>"))

    assert result["success"] is True
    assert result["comment"]["text"] == "<p>Test comment</p>"
    resolving_client.get_comment.assert_called_once()
