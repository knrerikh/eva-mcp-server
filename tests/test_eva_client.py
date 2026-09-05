"""Tests for Eva API client."""

import os
import sys
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from eva_client import EvaAPIError, EvaClient


@pytest.fixture
def real_client():
    """A real EvaClient pointed at a stub URL.

    Nothing here is mocked except the HTTP transport in the tests that need it:
    these exercise the client's own logic — request building, positional
    arguments, code resolution — so the object under test has to be the real one.
    """
    with patch.dict(os.environ, {"EVA_API_TOKEN": "test_token"}):
        client = EvaClient(
            api_url="https://test.eva.com/api", api_token="test_token", read_only=True
        )
        yield client
        client.close()


def test_client_initialization():
    """Test client initialization."""
    with patch.dict(os.environ, {"EVA_API_TOKEN": "test_token"}):
        client = EvaClient(
            api_url="https://test.eva.com/api", api_token="test_token", read_only=True
        )

        assert client.api_url == "https://test.eva.com/api"
        assert client.api_token == "test_token"
        assert client.read_only is True

        client.close()


def test_client_initialization_without_token():
    """Test that client initialization fails without token."""
    with (
        patch.dict(os.environ, {}, clear=True),
        pytest.raises(ValueError, match="API token is required"),
    ):
        EvaClient(api_url="https://test.eva.com/api")


def test_read_only_protection(real_client):
    """Test that write operations are blocked in read-only mode."""
    with pytest.raises(EvaAPIError, match="read-only mode"):
        real_client.create_task(name="Test", parent="project")


def test_read_only_protection_create_list(real_client):
    """Test that list creation is blocked in read-only mode."""
    with pytest.raises(EvaAPIError, match="read-only mode"):
        real_client.create_list(name="List 1", parent="CmfProject:proj")


def test_generate_callid(real_client):
    """Test call ID generation."""
    callid = real_client._generate_callid()
    assert isinstance(callid, str)
    assert len(callid) > 0


def test_build_request(real_client):
    """Test request building."""
    request = real_client._build_request("CmfTask.get", {"code": "TASK-123"})

    assert request["jsonrpc"] == "2.2"
    assert request["method"] == "CmfTask.get"
    assert "callid" in request
    assert request["kwargs"] == {"code": "TASK-123"}


@pytest.mark.asyncio
async def test_successful_api_call(real_client):
    """Test successful API call."""
    mock_response = Mock()
    mock_response.json.return_value = {"result": {"code": "TASK-123", "name": "Test Task"}}
    mock_response.raise_for_status = Mock()

    with patch.object(real_client.client, "post", return_value=mock_response):
        result = real_client.call("CmfTask.get", code="TASK-123")

        assert result == {"code": "TASK-123", "name": "Test Task"}


@pytest.mark.asyncio
async def test_api_error_response(real_client):
    """Test API error response handling."""
    mock_response = Mock()
    mock_response.json.return_value = {"error": {"code": -32600, "message": "Invalid Request"}}
    mock_response.raise_for_status = Mock()

    with (
        patch.object(real_client.client, "post", return_value=mock_response),
        pytest.raises(EvaAPIError, match="Invalid Request"),
    ):
        real_client.call("CmfTask.get", code="TASK-123")


def test_build_request_with_positional_args(real_client):
    """Eva addresses entities positionally: args[0] must reach the payload."""
    request = real_client._build_request(
        "CmfTask.update",
        {"name": "New name"},
        args=["CmfTask:11111111-2222-3333-4444-555555555555"],
    )

    assert request["args"] == ["CmfTask:11111111-2222-3333-4444-555555555555"]
    assert request["kwargs"] == {"name": "New name"}


def test_build_request_omits_args_when_not_given(real_client):
    """Calls that take no positional arguments keep their previous payload shape."""
    request = real_client._build_request("CmfTask.get", {"code": "TASK-123"})

    assert "args" not in request


@pytest.mark.asyncio
async def test_call_sends_positional_args(real_client):
    """call() forwards positional arguments to the JSON-RPC 'args' field."""
    mock_response = Mock()
    mock_response.json.return_value = {"result": "CmfTask:abc"}
    mock_response.raise_for_status = Mock()

    with patch.object(real_client.client, "post", return_value=mock_response) as post:
        real_client.call("CmfTask.get", "CmfTask:abc", name="New name")

    assert post.call_args.kwargs["json"]["args"] == ["CmfTask:abc"]
    assert post.call_args.kwargs["json"]["kwargs"] == {"name": "New name"}


def test_resolve_id_passes_entity_ids_through(real_client):
    """An internal identifier needs no lookup."""
    with patch.object(real_client, "call") as call:
        resolved = real_client.resolve_id("CmfTask:11111111-2222-3333-4444-555555555555", "CmfTask")

    assert resolved == "CmfTask:11111111-2222-3333-4444-555555555555"
    call.assert_not_called()


def test_resolve_id_looks_up_human_code(real_client):
    """A human-readable code is resolved through <Entity>.get."""
    with patch.object(
        real_client, "call", return_value={"id": "CmfTask:abc", "code": "ABC-1"}
    ) as call:
        resolved = real_client.resolve_id("ABC-1", "CmfTask")

    assert resolved == "CmfTask:abc"
    call.assert_called_once_with("CmfTask.get", code="ABC-1", fields=["id", "code"])


def test_resolve_id_caches_lookups(real_client):
    """The same code is looked up once, not on every call."""
    with patch.object(real_client, "call", return_value={"id": "CmfTask:abc"}) as call:
        real_client.resolve_id("ABC-1", "CmfTask")
        real_client.resolve_id("ABC-1", "CmfTask")

    assert call.call_count == 1


def test_resolve_id_tries_several_entities(real_client):
    """A comment parent may be a task or a document."""

    def fake_call(method, *args, **kwargs):
        if method == "CmfTask.get":
            raise EvaAPIError("not found", code=500)
        return {"id": "CmfDocument:abc"}

    with patch.object(real_client, "call", side_effect=fake_call):
        resolved = real_client.resolve_id("DOC-1", ("CmfTask", "CmfDocument"))

    assert resolved == "CmfDocument:abc"


def test_resolve_id_reports_unresolvable_code(real_client):
    """An unresolvable code fails loudly instead of returning a silent zero."""
    with (
        patch.object(real_client, "call", return_value={}),
        pytest.raises(EvaAPIError, match="NOPE-1"),
    ):
        real_client.resolve_id("NOPE-1", "CmfTask")


@pytest.mark.asyncio
async def test_update_task_sends_resolved_id_positionally(real_client):
    """Defect 1: CmfTask.update takes the entity id in args[0]."""
    real_client.read_only = False

    with (
        patch.object(real_client, "resolve_id", return_value="CmfTask:abc"),
        patch.object(real_client, "call", return_value="CmfTask:abc") as call,
    ):
        real_client.update_task("ABC-1", name="New name")

    call.assert_called_once_with("CmfTask.update", "CmfTask:abc", name="New name")


def test_context_manager(real_client):
    """Test client as context manager."""
    with (
        patch.dict(os.environ, {"EVA_API_TOKEN": "test_token"}),
        EvaClient(api_url="https://test.eva.com/api", api_token="test_token") as client,
    ):
        assert client.api_url == "https://test.eva.com/api"
