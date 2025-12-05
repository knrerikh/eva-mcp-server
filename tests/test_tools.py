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


def test_count_tasks_success(eva_tools, mock_client):
    """Test counting tasks."""
    mock_client.count_tasks.return_value = 42
    
    result = eva_tools.count_tasks_by_filter(project="PROJECT-1")
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


def test_get_comments_success(eva_tools, mock_client):
    """Test getting comments."""
    mock_client.list_comments.return_value = [
        {"code": "COMM-1", "text": "Comment 1"}
    ]
    
    result = eva_tools.get_comments("TASK-123")
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["count"] == 1


def test_list_sprints_success(eva_tools, mock_client):
    """Test listing sprints."""
    mock_client.list_lists.return_value = [
        {"code": "SPR-1", "name": "Sprint 1"}
    ]
    
    result = eva_tools.list_sprints(limit=50)
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["count"] == 1


def test_get_audit_log_success(eva_tools, mock_client):
    """Test getting audit log."""
    mock_client.list_audit.return_value = [
        {"code": "AUD-1", "action": "created"}
    ]
    
    result = eva_tools.get_audit_log(entity_code="TASK-123")
    result_data = json.loads(result)
    
    assert result_data["success"] is True
    assert result_data["count"] == 1

