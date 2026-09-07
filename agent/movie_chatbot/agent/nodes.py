"""The graph's node functions -- what actually happens at each step.

Each function takes the state and returns a partial state update. The wiring
that connects them is in graph.py; keeping the two apart means you can read the
graph's shape without scrolling past the bodies.
"""
from langchain_core.messages import AIMessage, SystemMessage, ToolMessage
from langgraph.graph import END

from .model import model_with_tools, tools_with_names
from .prompt import SYSTEM_PROMPT
from .state import MediaQuery


def llm_call(state: MediaQuery):
    """Main LLM call to process user queries about media."""
    messages = state['messages']
    last_media_name = state.get('last_media_name')
    last_media_type = state.get('last_media_type')

    context = []
    if last_media_name:
        context.append(f"The user is currently interested in '{last_media_name}', which is a {last_media_type}.")

    system_context = SYSTEM_PROMPT
    if context:
        system_context += "\n\n## Current Context\n" + \
            "\n".join(f"- {line}" for line in context)

    # Prepare messages: system prompt + full conversation history
    # This is crucial - the LLM sees ALL previous messages, not just the current one
    llm_messages = [SystemMessage(content=system_context)] + messages

    # call the model with tools
    response = model_with_tools.invoke(llm_messages)

    return {
        'messages': [response],
        'llm_calls': state.get('llm_calls', 0) + 1,
    }


def tool_node(state: MediaQuery):
    """Perform tool calls based on LLM requests."""
    last_message = state['messages'][-1]
    assert isinstance(last_message, AIMessage)

    results = []
    for tool_call in last_message.tool_calls:
        tool = tools_with_names[tool_call['name']]
        # [Claude Code] A malformed tool call (bad/missing args) used to raise and kill
        # the whole program. Feeding the error back as the tool result instead lets the
        # model read it and retry with corrected arguments on the next loop turn.
        try:
            observation = tool.invoke(tool_call['args'])
        except Exception as e:
            observation = f"Tool call failed: {e}"

        results.append(
            ToolMessage(
                content=str(observation),
                tool_call_id=tool_call['id'],
                name=tool_call['name'],
            )
        )

    # return all tool results,
    # they will be added to the conversation state['messages'] for next LLM call
    return {'messages': results}


def update_context(state: MediaQuery):
    """Remember the most recently discussed title so follow-ups like "who is in it?" work."""
    updates = {}

    # [Claude Code] The old version also checked `'get_crew' in args` / `'get_cast' in
    # args — tool call args only ever contain parameter names (media_name, media_type,
    # ...), never tool names, so those branches could never run and were removed.
    for msg in reversed(state['messages']):
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tool_call in msg.tool_calls:
                args = tool_call.get('args', {})

                if args.get('media_name') and 'last_media_name' not in updates:
                    updates['last_media_name'] = args['media_name']

                if args.get('media_type') and 'last_media_type' not in updates:
                    updates['last_media_type'] = args['media_type']

            break  # Stop after the most recent AI message that made tool calls

    return updates


def should_continue(state: MediaQuery):
    """Decide whether to run tools or finish the turn."""
    last_message = state['messages'][-1]

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tool_node"  # there are tool calls to process

    return END
