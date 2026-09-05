"""Shared fixtures for the Eva MCP test suite.

The response shapes the fixtures hand out live in ``tests/fixtures.py``; this
module only wires them into pytest. Both ``src`` and the tests directory go on
``sys.path`` here, before any test module is imported, so the suite runs the
same way from the repository root and from an installed checkout.
"""

import os
import sys
from unittest.mock import create_autospec

import pytest

TESTS_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(TESTS_DIR, "..", "src"))
sys.path.insert(0, TESTS_DIR)

from eva_client import EvaAPIError, EvaClient  # noqa: E402
from fixtures import RESOLVED  # noqa: E402
from tools import EvaTools  # noqa: E402


@pytest.fixture
def mock_client():
    """A mock Eva client that validates call signatures.

    ``create_autospec`` is used rather than ``Mock(spec=...)`` because only the
    former checks the arguments a call was made with. A plain spec mock accepts
    a misspelled keyword and records it happily, which hides exactly the kind of
    mistake these tests exist to catch.
    """
    return create_autospec(EvaClient, instance=True, spec_set=True)


@pytest.fixture
def resolving_client(mock_client):
    """Mock client whose ``resolve_id`` behaves like the real implementation.

    Identifiers pass through untouched, known codes resolve, and anything else
    raises — matching the client, which fails loudly rather than letting an
    unresolvable code turn into an empty result.
    """

    def resolve(code, entity="CmfTask"):
        if str(code).startswith("Cmf") and ":" in str(code):
            return code
        if code in RESOLVED:
            return RESOLVED[code]
        raise EvaAPIError(f"Cannot resolve '{code}' to a {entity} id", code=500)

    mock_client.resolve_id.side_effect = resolve
    return mock_client


@pytest.fixture
def eva_tools(mock_client):
    """Eva tools instance wired to the mock client."""
    return EvaTools(mock_client)
