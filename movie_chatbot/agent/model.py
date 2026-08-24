"""The LLM backend and its tool bindings.

Isolated so swapping model provider (Ollama -> OpenAI, a different local model,
a different host) is a one-file change that the graph never notices.
"""
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

from ..tools import ALL_TOOLS

load_dotenv()

model = ChatOllama(
    model="qwen3:8b",
    temperature=0,
    base_url="http://dabolu:11434",
    # [Claude Code] Dropped validate_model_on_init=True: it pings the Ollama server at
    # import time, so simply importing this module (e.g. from the tests) failed whenever
    # the server was unreachable. Connection problems now surface on the first real call.
)

# Lookup by name, so tool_node can find the right callable when the LLM asks for one.
tools_with_names = {tool.name: tool for tool in ALL_TOOLS}

# Bind tools to the model so it knows what functions it can call.
# This teaches the LLM about available tools and their parameters.
model_with_tools = model.bind_tools(ALL_TOOLS)
