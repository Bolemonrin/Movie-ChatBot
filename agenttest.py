# from IPython.display import Image, display
# from dotenv import load_dotenv
# load_dotenv()

# from typing import Annotated
# from typing_extensions import TypedDict
# from langgraph.graph import StateGraph, START, END
# from langgraph.graph.message import add_messages
# from langchain.chat_models import init_chat_model

# class State(TypedDict):
#     messages: Annotated[list, add_messages]
    
    
# workflow = StateGraph(State)
# llm = init_chat_model("openai:gpt-5")

# def chatbot(state: State):
#     response = llm.invoke(state['messages'])
#     return {'messages': [response]}

# workflow.add_node(
#     "chatbot",
#     chatbot
# )
# workflow.add_edge(START, "chatbot")
# workflow.add_edge("chatbot", END)

# graph = workflow.compile()


# try:
#     display(Image(graph.get_graph().draw_mermaid_png()))
# except Exception:
#     # This requires some extra dependencies and is optional
#     pass


# def stream_graph_updates(user_input: str):
#     for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
#         for value in event.values():
#             print("Assistant:", value["messages"][-1].content)


# while True:
#     try:
#         user_input = input("User: ")
#         if user_input.lower() in ["quit", "exit", "q"]:
#             print("Goodbye!")
#             break
#         stream_graph_updates(user_input)
#     except:
#         # fallback if input() is not available
#         user_input = "What do you know about LangGraph?"
#         print("User: " + user_input)
#         stream_graph_updates(user_input)
#         break


from langchain.messages import AnyMessage, SystemMessage, ToolMessage
from typing_extensions import TypedDict, Annotated
from langchain.chat_models import init_chat_model
from langgraph.graph import StateGraph, START, END
from typing import Literal
import operator

from test_tools import *

class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llmCalls: int


model = init_chat_model(
    "openai:gpt-5",
    temperature = 0
)


tools = [find_media, get_media_summary]
toolsByName = {tool.name: tool for tool in tools}
modelWithTools = model.bind_tools(toolsByName)

def llm_call(state: dict):
    """LLM decides whether to call a tool or not"""

    return {
        "messages": [
            modelWithTools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful assistant tasked with finding the summary of movies and Tv show."
                    )
                ]
                + state["messages"]
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
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
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

# Show the agent
from IPython.display import Image, display
display(Image(agent.get_graph(xray=True).draw_mermaid_png()))

# Invoke
from langchain.messages import HumanMessage
messages = [HumanMessage(content="Add 3 and 4.")]
messages = agent.invoke({"messages": messages})
for m in messages["messages"]:
    m.pretty_print()