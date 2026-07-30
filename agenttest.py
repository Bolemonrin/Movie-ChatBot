from langchain.messages import AIMessage, AnyMessage, SystemMessage, ToolMessage, HumanMessage
from typing_extensions import TypedDict, Annotated, NotRequired
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from huggingface_hub import InferenceClient
from langchain_ollama import ChatOllama
from typing import Literal
import operator

# Import tools from test_tools.py
from tools import find_media, get_media_summary, get_media_recommendations, get_similar_media, get_cast, get_crew

from dotenv import load_dotenv
import os

# load environment variables
load_dotenv()

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: NotRequired[int]


# model = init_chat_model(
#     model="meta-llama/Llama-3.1-8B-Instruct:novita",
#     model_provider="huggingface", # model comes from huggingface
#     max_tokens = 1024,
#     temperature = 0.3,
# )

model = ChatOllama(
    model="qwen3:8b",
    temperature=0,
    base_url="http://dabolu:11434",
    validate_model_on_init=True
)

# embeddings =


tools = [find_media, get_media_summary, get_media_recommendations, get_similar_media, get_cast, get_crew]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(
    tools=tools,
)
print("Tools bound successfully")

# result = model_with_tools.invoke("what is the summary of game of thrones (Use the apporiate tool to answer the question)")
# print(result)

def llm_call(state: MessagesState):
    """LLM decides whether to call a tool or not"""
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with finding the summary of movies and TV shows."
                    )
                ] + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }

def tool_node(state: MessagesState):
    """Performs the tool call"""
    result = []
    last_message = state["messages"][-1]
    assert isinstance(last_message, AIMessage)
    for tool_call in last_message.tool_calls:
        tool = tools_by_name[tool_call["name"]]
        # [Claude Code] A malformed tool call (bad/missing args) used to raise here and
        # kill the whole program. Feeding the error back as the tool result instead lets
        # the model read it and retry with corrected arguments on the next loop turn.
        try:
            observation = tool.invoke(tool_call["args"])
        except Exception as e:
            observation = f"Tool call failed: {e}"
        result.append(
            ToolMessage(
                content=str(observation),
                tool_call_id=tool_call["id"]
            )
        )
    return {"messages": result}


def should_continue(state: MessagesState):
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""
    messages = state["messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
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

if __name__ == "__main__":
    while True:
        query = input("🎬 Ask about a movie (or 'quit'): ")
        if query.lower() in {"quit", "exit"}:
            break
        messages: list[AnyMessage] = [HumanMessage(content=query)]
        result = agent.invoke({"messages": messages})
        print("\nAssistant:")
        for msg in result["messages"]:
            if hasattr(msg, "content"):
                print(msg.content)
        print("\n")
