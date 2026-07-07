# tests/test_agenttest.py
import pytest
from agenttest import agent

def test_agent_process_query():
    # Test with a query about a movie
    query = "what are movies similar to django"
    result = agent.invoke({"messages": [HumanMessage(content=query)]})
    assert len(result["messages"]) > 0
    assert "content" in result["messages"][0]

def test_agent_quit_command():
    # Test with the quit command
    query = "quit"
    result = agent.invoke({"messages": [HumanMessage(content=query)]})
    assert len(result["messages"]) == 0
