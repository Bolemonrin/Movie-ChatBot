import pytest
from unittest.mock import patch, MagicMock
from langchain.messages import HumanMessage, AIMessage, ToolMessage


def test_agent_returns_messages():
    """Graph runs and returns messages; LLM mocked, no network."""
    fake_reply = AIMessage(content="Django Unchained is similar to...")
    fake_reply.tool_calls = []                       # no tool calls -> END

    mock_model = MagicMock()
    mock_model.invoke.return_value = fake_reply

    # pass mock_model as the 2nd arg -> patch won't introspect the real object
    with patch("agenttest.modelWithTools", mock_model):
        from agenttest import agent
        result = agent.invoke({"messages": [HumanMessage(content="movies like django")]})

    assert len(result["messages"]) > 0
    assert result["messages"][-1].content == "Django Unchained is similar to..."


def test_agent_routes_to_tool_when_tool_called():
    """LLM emits a tool call -> graph should run tool_node."""
    tool_call_reply = AIMessage(content="")
    tool_call_reply.tool_calls = [
        {"name": "find_media",
         "args": {"media_name": "django", "media_type": "movie"},
         "id": "call_1"}
    ]
    final_reply = AIMessage(content="Here are the results")
    final_reply.tool_calls = []

    mock_model = MagicMock()
    mock_model.invoke.side_effect = [tool_call_reply, final_reply]   # two turns

    mock_tool = MagicMock()
    mock_tool.invoke.return_value = "mocked tool output"
    mock_tools = {"find_media": mock_tool}           # a real dict, not a MagicMock

    with patch("agenttest.modelWithTools", mock_model), \
         patch("agenttest.toolsByName", mock_tools):
        from agenttest import agent
        result = agent.invoke({"messages": [HumanMessage(content="find django")]})

    assert any(isinstance(m, ToolMessage) for m in result["messages"])
