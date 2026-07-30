"""Tests for the langgraph agent in main.py.

The LLM and the tools are mocked, so no Ollama server or TMDB access is needed.
main.py's agent is compiled with a checkpointer, so every invoke needs a config
with a thread_id — a fresh uuid per test keeps tests isolated from each other.
"""
import uuid
from unittest.mock import MagicMock, patch

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage


def _config():
    """Fresh conversation thread for each test so no state leaks between them."""
    return {"configurable": {"thread_id": str(uuid.uuid4())}}


def _tool_call_reply(name, args):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": "call_1"}])


def test_agent_returns_reply_without_tools():
    """No tool calls -> graph goes straight to END with the model's reply."""
    fake_reply = AIMessage(content="Django Unchained is similar to...")

    mock_model = MagicMock()
    mock_model.invoke.return_value = fake_reply

    with patch("main.model_with_tools", mock_model):
        from main import media_agent
        result = media_agent.invoke(
            {"messages": [HumanMessage(content="movies like django")]},
            config=_config(),
        )

    assert result["messages"][-1].content == "Django Unchained is similar to..."


def test_agent_routes_to_tool_when_tool_called():
    """LLM emits a tool call -> tool_node runs the tool and its result reaches history."""
    final_reply = AIMessage(content="Here are the results")

    mock_model = MagicMock()
    mock_model.invoke.side_effect = [
        _tool_call_reply("find_media", {"media_name": "django", "media_type": "movie"}),
        final_reply,
    ]

    mock_tool = MagicMock()
    mock_tool.invoke.return_value = "mocked tool output"

    with patch("main.model_with_tools", mock_model), \
         patch("main.tools_with_names", {"find_media": mock_tool}):
        from main import media_agent
        result = media_agent.invoke(
            {"messages": [HumanMessage(content="find django")]},
            config=_config(),
        )

    mock_tool.invoke.assert_called_once_with({"media_name": "django", "media_type": "movie"})
    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert tool_messages[0].content == "mocked tool output"
    assert result["messages"][-1].content == "Here are the results"


def test_agent_remembers_history_across_turns():
    """Same thread_id -> the second turn must see the first turn's messages."""
    mock_model = MagicMock()
    mock_model.invoke.side_effect = [
        AIMessage(content="It was directed by Andrew Stanton."),
        AIMessage(content="He also directed WALL-E."),
    ]

    with patch("main.model_with_tools", mock_model):
        from main import media_agent
        config = _config()  # one shared thread across both turns

        media_agent.invoke(
            {"messages": [HumanMessage(content="who directed finding nemo")]},
            config=config,
        )
        result = media_agent.invoke(
            {"messages": [HumanMessage(content="what else did he direct")]},
            config=config,
        )

    # Full history: turn 1 human + AI, turn 2 human + AI
    assert len(result["messages"]) == 4

    # The model's second call must have received the first turn in its prompt
    second_call_messages = mock_model.invoke.call_args_list[1].args[0]
    contents = [m.content for m in second_call_messages]
    assert "who directed finding nemo" in contents
    assert "It was directed by Andrew Stanton." in contents


def test_agent_updates_last_media_context():
    """update_context should capture the media name/type from the tool call args."""
    mock_model = MagicMock()
    mock_model.invoke.side_effect = [
        _tool_call_reply("get_media_summary", {"media_name": "Finding Nemo", "media_type": "movie"}),
        AIMessage(content="Here's the summary"),
    ]

    mock_tool = MagicMock()
    mock_tool.invoke.return_value = "Title: Finding Nemo\nOverview: fish gets lost"

    with patch("main.model_with_tools", mock_model), \
         patch("main.tools_with_names", {"get_media_summary": mock_tool}):
        from main import media_agent
        config = _config()
        media_agent.invoke(
            {"messages": [HumanMessage(content="summary of finding nemo")]},
            config=config,
        )
        state = media_agent.get_state(config).values

    assert state["last_media_name"] == "Finding Nemo"
    assert state["last_media_type"] == "movie"


def test_tool_error_is_fed_back_to_model_not_raised():
    """A failing tool must become a readable ToolMessage, not crash the graph."""
    mock_model = MagicMock()
    mock_model.invoke.side_effect = [
        _tool_call_reply("find_media", {"media_name": "django"}),
        AIMessage(content="Sorry, that search failed."),
    ]

    mock_tool = MagicMock()
    mock_tool.invoke.side_effect = ValueError("boom")

    with patch("main.model_with_tools", mock_model), \
         patch("main.tools_with_names", {"find_media": mock_tool}):
        from main import media_agent
        result = media_agent.invoke(
            {"messages": [HumanMessage(content="find django")]},
            config=_config(),
        )

    tool_messages = [m for m in result["messages"] if isinstance(m, ToolMessage)]
    assert len(tool_messages) == 1
    assert "Tool call failed" in tool_messages[0].content
    assert "boom" in tool_messages[0].content
