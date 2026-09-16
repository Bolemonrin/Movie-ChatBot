"""How the nodes are wired together, and the compiled agent itself.

    START -> llm_call --(no tool calls)--> END
                ^  |
                |  (tool calls)
                |  v
    update_context <- tool_node
"""
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph

from .nodes import llm_call, should_continue, tool_node, update_context
from .state import MediaQuery

agent_builder = StateGraph(MediaQuery)

# add nodes
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("update_context", update_context)

# add edges
agent_builder.add_edge(START, "llm_call")

# add conditional edges
agent_builder.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)

# after tool calls, update context, then go back to the LLM
agent_builder.add_edge("tool_node", "update_context")
agent_builder.add_edge("update_context", "llm_call")

# [Claude Code] The checkpointer is what gives the chat memory: it saves the graph state
# per thread_id and reloads it before every invoke, so each turn sees the full history.
saver = InMemorySaver()

media_agent = agent_builder.compile(checkpointer=saver)
