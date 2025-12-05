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


def test_context_manager(mock_client):
    """Test client as context manager."""
    with patch.dict(os.environ, {"EVA_API_TOKEN": "test_token"}):
        with EvaClient(api_url="https://test.eva.com/api", api_token="test_token") as client:
            assert client.api_url == "https://test.eva.com/api"

