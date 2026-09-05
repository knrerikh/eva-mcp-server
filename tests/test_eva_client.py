"""Tests for Eva API client."""

import pytest
from unittest.mock import Mock, patch
import httpx

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from eva_client import EvaClient, EvaAPIError


@pytest.fixture
def mock_client():
    """Create a mock Eva client."""
    with patch.dict(os.environ, {"EVA_API_TOKEN": "test_token"}):
        client = EvaClient(
            api_url="https://test.eva.com/api",
            api_token="test_token",
            read_only=True
        )
        yield client
        client.close()


def test_client_initialization():
    """Test client initialization."""
    with patch.dict(os.environ, {"EVA_API_TOKEN": "test_token"}):
        client = EvaClient(
            api_url="https://test.eva.com/api",
            api_token="test_token",
            read_only=True
        )
        
        assert client.api_url == "https://test.eva.com/api"
        assert client.api_token == "test_token"
        assert client.read_only is True
        
        client.close()


def test_client_initialization_without_token():
    """Test that client initialization fails without token."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="API token is required"):
            EvaClient(api_url="https://test.eva.com/api")


def test_read_only_protection(mock_client):
    """Test that write operations are blocked in read-only mode."""
    with pytest.raises(EvaAPIError, match="read-only mode"):
        mock_client.create_task(name="Test", parent="project")


def test_read_only_protection_create_list(mock_client):
    """Test that list creation is blocked in read-only mode."""
    with pytest.raises(EvaAPIError, match="read-only mode"):
        mock_client.create_list(name="List 1", parent="CmfProject:proj")


def test_generate_callid(mock_client):
    """Test call ID generation."""
    callid = mock_client._generate_callid()
    assert isinstance(callid, str)
    assert len(callid) > 0


def test_build_request(mock_client):
    """Test request building."""
    request = mock_client._build_request("CmfTask.get", {"code": "TASK-123"})
    
    assert request["jsonrpc"] == "2.2"
    assert request["method"] == "CmfTask.get"
    assert "callid" in request
    assert request["kwargs"] == {"code": "TASK-123"}


@pytest.mark.asyncio
async def test_successful_api_call(mock_client):
    """Test successful API call."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "result": {"code": "TASK-123", "name": "Test Task"}
    }
    mock_response.raise_for_status = Mock()
    
    with patch.object(mock_client.client, 'post', return_value=mock_response):
        result = mock_client.call("CmfTask.get", code="TASK-123")
        
        assert result == {"code": "TASK-123", "name": "Test Task"}


@pytest.mark.asyncio
async def test_api_error_response(mock_client):
    """Test API error response handling."""
    mock_response = Mock()
    mock_response.json.return_value = {
        "error": {
            "code": -32600,
            "message": "Invalid Request"
        }
    }
    mock_response.raise_for_status = Mock()
    
    with patch.object(mock_client.client, 'post', return_value=mock_response):
        with pytest.raises(EvaAPIError, match="Invalid Request"):
            mock_client.call("CmfTask.get", code="TASK-123")


def test_build_request_with_positional_args(mock_client):
    """Eva addresses entities positionally: args[0] must reach the payload."""
    request = mock_client._build_request(
        "CmfTask.update",
        {"name": "New name"},
        args=["CmfTask:11111111-2222-3333-4444-555555555555"],
    )

    assert request["args"] == ["CmfTask:11111111-2222-3333-4444-555555555555"]
    assert request["kwargs"] == {"name": "New name"}


def test_build_request_omits_args_when_not_given(mock_client):
    """Calls that take no positional arguments keep their previous payload shape."""
    request = mock_client._build_request("CmfTask.get", {"code": "TASK-123"})

    assert "args" not in request


@pytest.mark.asyncio
async def test_call_sends_positional_args(mock_client):
    """call() forwards positional arguments to the JSON-RPC 'args' field."""
    mock_response = Mock()
    mock_response.json.return_value = {"result": "CmfTask:abc"}
    mock_response.raise_for_status = Mock()

    with patch.object(mock_client.client, "post", return_value=mock_response) as post:
        mock_client.call("CmfTask.get", "CmfTask:abc", name="New name")

    assert post.call_args.kwargs["json"]["args"] == ["CmfTask:abc"]
    assert post.call_args.kwargs["json"]["kwargs"] == {"name": "New name"}


def test_resolve_id_passes_entity_ids_through(mock_client):
    """An internal identifier needs no lookup."""
    with patch.object(mock_client, "call") as call:
        resolved = mock_client.resolve_id(
            "CmfTask:11111111-2222-3333-4444-555555555555", "CmfTask"
        )

    assert resolved == "CmfTask:11111111-2222-3333-4444-555555555555"
    call.assert_not_called()


def test_resolve_id_looks_up_human_code(mock_client):
    """A human-readable code is resolved through <Entity>.get."""
    with patch.object(
        mock_client, "call", return_value={"id": "CmfTask:abc", "code": "ABC-1"}
    ) as call:
        resolved = mock_client.resolve_id("ABC-1", "CmfTask")

    assert resolved == "CmfTask:abc"
    call.assert_called_once_with("CmfTask.get", code="ABC-1", fields=["id", "code"])


def test_resolve_id_caches_lookups(mock_client):
    """The same code is looked up once, not on every call."""
    with patch.object(
        mock_client, "call", return_value={"id": "CmfTask:abc"}
    ) as call:
        mock_client.resolve_id("ABC-1", "CmfTask")
        mock_client.resolve_id("ABC-1", "CmfTask")

    assert call.call_count == 1


def test_resolve_id_tries_several_entities(mock_client):
    """A comment parent may be a task or a document."""
    def fake_call(method, *args, **kwargs):
        if method == "CmfTask.get":
            raise EvaAPIError("not found", code=500)
        return {"id": "CmfDocument:abc"}

    with patch.object(mock_client, "call", side_effect=fake_call):
        resolved = mock_client.resolve_id("DOC-1", ("CmfTask", "CmfDocument"))

    assert resolved == "CmfDocument:abc"


def test_resolve_id_reports_unresolvable_code(mock_client):
    """An unresolvable code fails loudly instead of returning a silent zero."""
    with patch.object(mock_client, "call", return_value={}):
        with pytest.raises(EvaAPIError, match="NOPE-1"):
            mock_client.resolve_id("NOPE-1", "CmfTask")


@pytest.mark.asyncio
async def test_update_task_sends_resolved_id_positionally(mock_client):
    """Defect 1: CmfTask.update takes the entity id in args[0]."""
    mock_client.read_only = False

    with patch.object(mock_client, "resolve_id", return_value="CmfTask:abc"):
        with patch.object(mock_client, "call", return_value="CmfTask:abc") as call:
            mock_client.update_task("ABC-1", name="New name")

    call.assert_called_once_with("CmfTask.update", "CmfTask:abc", name="New name")


def test_context_manager(mock_client):
    """Test client as context manager."""
    with patch.dict(os.environ, {"EVA_API_TOKEN": "test_token"}):
        with EvaClient(api_url="https://test.eva.com/api", api_token="test_token") as client:
            assert client.api_url == "https://test.eva.com/api"

