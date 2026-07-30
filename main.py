import operator
import uuid

from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from typing import Annotated, List
from typing_extensions import TypedDict, NotRequired

# [Claude Code] Was `from tests.test_tools import *`: that file was a stale pre-fix copy
# of the real tools (it still told the model to pass IDs, the bug behind the pydantic
# ValidationError). The agent must import the maintained tools from tools.py; the tests
# folder now contains actual tests.
from tools import (
    find_media,
    get_media_summary,
    get_media_recommendations,
    get_similar_media,
    get_cast,
    get_crew,
)


SYSTEM_PROMPT = """You are an expert Media Discovery Assistant capable of finding movies and TV shows, retrieving detailed cast/crew info, and providing personalized recommendations.

## Your Capabilities

You have access to a specific set of tools to fetch real-time data from TMDB (The Movie Database):
- **Search & Identification:** `find_media` (search for titles, IDs, years, ratings).
- **Details:** `get_media_summary` (plot), `get_cast` (actors), `get_crew` (directors/creators).
- **Discovery:** `get_media_recommendations` (based on a title), `get_similar_media` (pattern matching).

## Guidelines

### 1. Context & State Awareness
- **"The It" Factor:** If a user asks "Who is in it?" or "What is the plot?", ALWAYS check the conversation history for the most recent media title before asking the user for clarification.
- **Media Types:** Distinguish between "movie" and "tv". If the user is ambiguous (e.g., "The Last of Us"), ask or default to the most popular format, but be consistent with the `media_type` argument.

### 2. Critical Tool Usage Rules (Read Carefully)
- **Names, never IDs:** Every tool takes the full title as `media_name` plus a `media_type` of exactly "movie" or "tv". Never pass numeric IDs to any tool.
- **Expand nicknames:** Convert abbreviations and nicknames to the full official title before calling a tool (e.g., "GoT" -> "Game of Thrones", "nemo" -> "Finding Nemo", "LOTR" -> "The Lord of the Rings").
- **Search First:** If you are unsure of a spelling or year, use `find_media` to confirm the title exists before calling detail tools.

### 3. Data Presentation
- **Cast & Crew:** When listing cast, don't list all 50 members. Summarize the top 3-5 leads unless the user asks for a "full list."
- **Summaries:** Present plots concisely.
- **Recommendations:** When giving recommendations, briefly explain *why* (e.g., "Since you liked the dark tone of Batman, here are similar noir films...").

### 4. Handling Errors
- If a tool returns "No media found," apologize and ask the user to double-check the spelling.
- If a tool call fails, read the error message and retry with corrected arguments.
- If a user asks for a release date (which isn't in a dedicated tool), use `find_media` — the result string contains the year (e.g., "Year: 2023").

## Example Interactions

**User:** "Find me the plot of Inception."
**Assistant:** Call `get_media_summary(media_name="Inception", media_type="movie")`

**User:** "Who starred in it?"
**Assistant:** (Thinking: Context is 'Inception'. Cast tool accepts names.)
Call `get_cast(media_name="Inception", media_type="movie")`

**User:** "Suggest some shows like Breaking Bad."
**Assistant:** Call `get_media_recommendations(media_name="Breaking Bad", media_type="tv")`

**User:** "Who directed the first one you mentioned?"
**Assistant:** (Thinking: The user refers to the first recommendation from the previous turn.)
Call `get_crew(media_name="[Insert Name from prev turn]", media_type="tv")`
"""


model = ChatOllama(
    model="qwen3:8b",
    temperature=0,
    base_url="http://dabolu:11434",
    # [Claude Code] Dropped validate_model_on_init=True: it pings the Ollama server at
    # import time, so simply importing this module (e.g. from the tests) failed whenever
    # the server was unreachable. Connection problems now surface on the first real call.
)

# Define the available tools
tools = [
    find_media,
    get_media_summary,
    get_media_recommendations,
    get_similar_media,
    get_cast,
    get_crew,
]

# Create a dictionary for easy tool lookup by name
# This allows us to quickly find the right tool when the LLM requests one
tools_with_names = {tool.name: tool for tool in tools}

# Bind tools to the model so it knows what functions it can call
# This teaches the LLM about available tools and their parameters
model_with_tools = model.bind_tools(tools)


class MediaQuery(TypedDict):
    # conversation history
    messages: Annotated[List[AnyMessage], operator.add]

    # persistent context
    # [Claude Code] NotRequired lets the REPL invoke with just {"messages": [...]}. The
    # old loop passed last_media_name=None etc. on every turn, which overwrote whatever
    # the checkpointer had remembered with None — one of the reasons follow-up questions
    # forgot the movie being discussed.
    last_media_name: NotRequired[str | None]
    last_media_type: NotRequired[str | None]
    llm_calls: NotRequired[int]


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
# agenttest.py had no checkpointer, which is why it forgot everything between questions.
saver = InMemorySaver()

media_agent = agent_builder.compile(checkpointer=saver)


# [Claude Code] The REPL is now guarded by __main__ so tests (and other modules) can
# import media_agent without launching an interactive input loop.
if __name__ == "__main__":
    config = {
        'configurable': {
            'thread_id': str(uuid.uuid4()),
        }
    }

    while True:
        try:
            user_input = input("🎬 Ask about a movie (or 'quit'): ")
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Exiting...")
                break

            results = media_agent.invoke(
                {'messages': [HumanMessage(content=user_input)]},
                config=config,
            )
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
            break

        # [Claude Code] The old loop printed the FIRST non-tool AIMessage in the history,
        # which once the checkpointer accumulates turns is the OLDEST reply — every turn
        # re-printed the first answer. The newest reply is simply the last message.
        print(f"\nAI: {results['messages'][-1].content}\n")
