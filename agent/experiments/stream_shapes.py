"""Scratch: print every chunk shape langgraph emits, to see what the API can
consume. Moved out of agent/graph.py, where it ran at import time and fired a
full Ollama round-trip on every `from movie_chatbot...` anywhere in the repo.

    uv run python agent/experiments/stream_shapes.py
"""
from langchain_core.messages import HumanMessage

from movie_chatbot.agent.graph import media_agent

for chunk in media_agent.stream(
    {'messages': [HumanMessage(content="tell me about the movie Inception")]},
    {'configurable': {'thread_id': 'test-thread'}},
    stream_mode=['messages', 'updates', 'values', 'debug', 'custom'],
):
    print(chunk)
