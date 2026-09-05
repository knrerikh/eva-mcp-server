"""Tests for the MCP server entry point.

The valuable properties here are structural. A tool is declared in one place
(``list_tools``) and dispatched in another (the map inside ``call_tool``), and
nothing in the module ties the two together — a tool can be advertised to the
client and then fail at call time, or be dispatched while invisible. The schema
is a third copy of the same knowledge: it names the arguments the handler will
be called with. These tests hold the three in agreement.
"""

import inspect
import json
from unittest.mock import create_autospec, patch

import pytest

import server
from tools import EvaTools


@pytest.fixture
def mock_tools():
    """Replace the module-global EvaTools with a signature-checked mock."""
    tools = create_autospec(EvaTools, instance=True, spec_set=True)
    with patch.object(server, "eva_tools", tools):
        yield tools


async def declared_tools():
    return await server.list_tools()


def minimal_arguments(tool):
    """The smallest argument set the schema declares as required."""
    properties = tool.inputSchema.get("properties", {})
    placeholder = {"integer": 1, "number": 1, "boolean": False, "array": []}
    return {
        name: placeholder.get(properties.get(name, {}).get("type"), "X")
        for name in tool.inputSchema.get("required", [])
    }


async def dispatched_method_name(mock_tools, tool):
    """Call a tool and report which EvaTools method it reached, if any."""
    mock_tools.reset_mock()
    await server.call_tool(tool.name, minimal_arguments(tool))
    called = [
        name
        for name in dir(mock_tools)
        if not name.startswith("_") and getattr(getattr(mock_tools, name), "called", False)
    ]
    return called[0] if len(called) == 1 else None


# --- What the server advertises ---------------------------------------------


async def test_tools_are_declared():
    """The server offers a non-empty catalogue."""
    tools = await declared_tools()

    assert tools
    assert all(tool.name.startswith("eva_") for tool in tools)


async def test_tool_names_are_unique():
    """A duplicate name would silently shadow a tool in any client's registry."""
    names = [tool.name for tool in await declared_tools()]

    assert len(names) == len(set(names))


async def test_every_tool_declares_an_object_schema():
    """Clients validate arguments against this before calling."""
    for tool in await declared_tools():
        assert tool.inputSchema["type"] == "object"
        assert "properties" in tool.inputSchema
        assert tool.description


# --- Declaration and dispatch agree ------------------------------------------


async def test_every_declared_tool_is_dispatched(mock_tools):
    """A tool advertised but missing from the dispatch map fails only at call time."""
    unreachable = []
    for tool in await declared_tools():
        result = await server.call_tool(tool.name, minimal_arguments(tool))
        if "Unknown tool" in result[0].text:
            unreachable.append(tool.name)

    assert unreachable == []


async def test_unknown_tool_is_reported(mock_tools):
    """An unknown name comes back as a readable error, not an exception."""
    result = await server.call_tool("eva_does_not_exist", {})
    payload = json.loads(result[0].text)

    assert payload["success"] is False
    assert "Unknown tool" in payload["error"]


async def test_each_tool_reaches_exactly_one_method(mock_tools):
    """Dispatch is one-to-one: no tool quietly shares another's handler."""
    reached = {}
    for tool in await declared_tools():
        reached[tool.name] = await dispatched_method_name(mock_tools, tool)

    assert all(
        reached.values()
    ), f"no single handler for: {[k for k, v in reached.items() if not v]}"
    assert len(set(reached.values())) == len(reached)


# --- Schemas match the handlers they will be called with ---------------------


async def test_schema_arguments_are_accepted_by_the_handler(mock_tools):
    """The schema names the keyword arguments the handler is invoked with.

    ``call_tool`` splats the client's arguments straight into the method, so a
    property the method does not accept becomes a TypeError at call time — for
    the user, a tool that fails whenever they use that argument.
    """
    mismatches = []
    for tool in await declared_tools():
        method_name = await dispatched_method_name(mock_tools, tool)
        signature = inspect.signature(getattr(EvaTools, method_name))
        accepted = set(signature.parameters) - {"self"}

        for prop in tool.inputSchema["properties"]:
            if prop not in accepted:
                mismatches.append(f"{tool.name}.{prop} -> {method_name}{tuple(accepted)}")

    assert mismatches == []


async def test_required_schema_fields_are_real_parameters(mock_tools):
    """A required field the handler does not take makes the tool unusable."""
    for tool in await declared_tools():
        required = tool.inputSchema.get("required", [])
        if not required:
            continue
        method_name = await dispatched_method_name(mock_tools, tool)
        accepted = set(inspect.signature(getattr(EvaTools, method_name)).parameters) - {"self"}

        assert set(required) <= accepted, f"{tool.name}: {required} vs {sorted(accepted)}"


# --- Calling through ---------------------------------------------------------


async def test_result_is_passed_through_untouched(mock_tools):
    """The tool's JSON reaches the client as text, unwrapped and unaltered."""
    mock_tools.list_projects.return_value = '{"success": true, "count": 0}'

    result = await server.call_tool("eva_list_projects", {"limit": 5})

    assert len(result) == 1
    assert result[0].text == '{"success": true, "count": 0}'
    mock_tools.list_projects.assert_called_once_with(limit=5)


async def test_arguments_are_forwarded(mock_tools):
    """Client arguments arrive as keyword arguments."""
    mock_tools.get_task_details.return_value = "{}"

    await server.call_tool("eva_get_task", {"task_code": "ACME-1"})

    mock_tools.get_task_details.assert_called_once_with(task_code="ACME-1")


async def test_failure_is_reported_as_json(mock_tools):
    """A handler that raises still yields a readable JSON error."""
    mock_tools.list_projects.side_effect = RuntimeError("boom")

    result = await server.call_tool("eva_list_projects", {})
    payload = json.loads(result[0].text)

    assert payload["success"] is False
    assert "boom" in payload["error"]


async def test_failure_json_survives_quotes_in_the_message(mock_tools):
    """Eva error text carries quotes and newlines; the envelope must still parse.

    A real example: Invalid filter operation ('>', '<', '==', ...) arrives with
    quotes, and a traceback arrives with newlines. Building the envelope by
    string interpolation produces invalid JSON for both, so the client sees a
    parse failure instead of the error.
    """
    mock_tools.list_projects.side_effect = RuntimeError('Field "code" not found\nsecond line')

    result = await server.call_tool("eva_list_projects", {})
    payload = json.loads(result[0].text)

    assert payload["success"] is False
    assert 'Field "code" not found' in payload["error"]


# --- Start-up ----------------------------------------------------------------


def test_initialize_client_requires_a_token():
    """Without a token the server exits rather than starting up unusable."""
    with patch.dict("os.environ", {"EVA_API_TOKEN": ""}, clear=True), pytest.raises(SystemExit):
        server.initialize_client()


def test_initialize_client_builds_client_and_tools():
    """A token is enough to bring both globals up."""
    env = {"EVA_API_TOKEN": "test_token", "EVA_API_URL": "https://test.eva.com/api"}

    with patch.dict("os.environ", env, clear=True):
        server.initialize_client()

    assert server.eva_client is not None
    assert server.eva_tools is not None
    assert server.eva_client.api_url == "https://test.eva.com/api"


def test_initialize_client_honours_read_only():
    """EVA_READ_ONLY is opt-in; the default allows writes."""
    env = {"EVA_API_TOKEN": "test_token", "EVA_READ_ONLY": "true"}

    with patch.dict("os.environ", env, clear=True):
        server.initialize_client()

    assert server.eva_client.read_only is True


def test_initialize_client_exits_when_the_client_cannot_be_built():
    """A failure behind the token — a bad URL, a refused transport — is fatal too."""
    with (
        patch.dict("os.environ", {"EVA_API_TOKEN": "test_token"}, clear=True),
        patch.object(server, "EvaClient", side_effect=RuntimeError("no transport")),
        pytest.raises(SystemExit),
    ):
        server.initialize_client()


# --- Process lifecycle -------------------------------------------------------


def test_run_exits_quietly_on_interrupt():
    """Ctrl-C is an ordinary way to stop a stdio server, not a crash."""
    # main() is stubbed as well as asyncio.run: calling the real one would build
    # a coroutine that nothing ever awaits, which surfaces later as a warning
    # attributed to an unrelated test.
    with (
        patch.object(server, "main", new=lambda: None),
        patch.object(server.asyncio, "run", side_effect=KeyboardInterrupt),
    ):
        server.run()  # must return normally


def test_run_exits_nonzero_on_failure():
    """Any other failure has to reach the supervisor as a non-zero exit."""
    with (
        patch.object(server, "main", new=lambda: None),
        patch.object(server.asyncio, "run", side_effect=RuntimeError("boom")),
        pytest.raises(SystemExit) as exit_info,
    ):
        server.run()

    assert exit_info.value.code == 1
