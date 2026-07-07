from langchain.messages import AnyMessage, SystemMessage, ToolMessage, HumanMessage
from typing_extensions import TypedDict, Annotated
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from typing import Literal
import operator

# Import tools from test_tools.py
from test_tools import find_media, get_media_summary

from dotenv import load_dotenv
import os

# load environment variables
load_dotenv()

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llmCalls: int

model = init_chat_model(
    model="meta-llama/Llama-3.1-8B-Instruct:novita",
    model_provider="hugginface", # model comes from huggingface
    max_tokens = 1024,
    temperature = 0.3,
)

tools = [find_media, get_media_summary]
toolsByName = {tool.name: tool for tool in tools}
modelWithTools = model.bind_tools(
    tools,
    tool_choice = "required"
)
print("Tools bound successfully")

def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""
    return {
        "messages": [
            modelWithTools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with finding the summary of movies and TV shows."
                    )
                ] + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }

def tool_node(state: dict):
    """Performs the tool call"""
    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = toolsByName[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(
            ToolMessage(
                content={"type": "text", "text": str(observation)},
                tool_call_id=tool_call["id"]
            )
        )
    return {"messages": result}

def should_continue(state: MessagesState) -> Literal["tool_node", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "tool_node"

    # Otherwise, we stop (reply to the user)
    return END

# Build workflow
agent_builder = StateGraph(MessagesState)

# Add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

# Add edges to connect nodes
agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)
agent_builder.add_edge("tool_node", "llm_call")

# Compile the agent
agent = agent_builder.compile()

while True:
    query = input("🎬 Ask about a movie (or 'quit'): ")
    if query.lower() in {"quit", "exit"}:
        break

    messages = [HumanMessage(content=query)]
    result = agent.invoke({"messages": messages})
    print("\nAssistant:")
    for msg in result["messages"]:
        if hasattr(msg, "content"):
            print(msg.content)
    print("\n")
