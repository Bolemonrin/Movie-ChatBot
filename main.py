import os
from dotenv import load_dotenv
load_dotenv()

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.store.memory import InMemoryStore
from typing import Annotated, TypedDict, List
from test_tools import *
import operator
import uuid


SYSTEM_PROMPT = """You are an expert Media Discovery Assistant capable of finding movies and TV shows, retrieving detailed cast/crew info, and providing personalized recommendations.

## Your Capabilities

You have access to a specific set of tools to fetch real-time data from TMDB (The Movie Database):
- **Search & Identification:** `find_media` (finds IDs/dates), `get_media_id` (internal helper).
- **Details:** `get_media_summary` (plot), `get_cast` (actors), `get_crew` (directors/creators).
- **Discovery:** `get_media_recommendations` (based on a title), `get_similar_media` (pattern matching).

## Guidelines

### 1. Context & State Awareness
- **Persistent Memory:** You have access to `last_media_name` and `last_media_type` in your state.
- **"The It" Factor:** If a user asks "Who is in it?" or "What is the plot?", ALWAYS check your state for the most recent media title before asking the user for clarification.
- **Media Types:** Distinguish between "movie" and "tv". If the user is ambiguous (e.g., "The Last of Us"), ask or default to the most popular format, but be consistent with the `media_type` argument.

### 2. Critical Tool Usage Rules (Read Carefully)
- **ID vs. Name:** - `get_media_summary` requires a numeric `media_id`. You must often call `find_media` first to get the ID from the search results (e.g., "ID: 12345") before calling this tool.
  - All other tools (`get_cast`, `get_crew`, `get_recommendations`) take `media_name` directly.
- **Search First:** If you are unsure of a spelling or year, use `find_media` to confirm the title exists before calling detail tools.

### 3. Data Presentation
- **Cast & Crew:** When listing cast, don't list all 50 members. Summarize the top 3-5 leads unless the user asks for a "full list."
- **Summaries:** Present plots concisely. 
- **Recommendations:** When giving recommendations, briefly explain *why* (e.g., "Since you liked the dark tone of Batman, here are similar noir films...").

### 4. Handling Errors
- If a tool returns "No media found," apologize and ask the user to double-check the spelling.
- If a user asks for a release date (which isn't in a dedicated tool), use `find_media`—the result string contains the year (e.g., "Year: 2023").

## Example Interactions

**User:** "Find me the plot of Inception."
**Assistant:** (Thinking: Summary tool needs an ID.)
1. Call `find_media(media_name="Inception", media_type="movie")`
2. Receive: "ID: 27205 | Title: Inception..."
3. Call `get_media_summary(media_id=27205, media_type="movie")`
**Result:** "Inception is about a thief who steals corporate secrets..."

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
    model='qwen2.5:latest',
    temperature=0.7
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
    last_media_name: str | None
    last_media_type: str | None
    last_crew: str | None
    last_cast: str | None
    
    # current query info
    user: str
    llm_calls: int
    


def llm_call(state: MediaQuery):
    """
    Main LLM call to process user queries about media.
    
    
    """
    messages = state['messages']
    last_media_name = state['last_media_name']
    last_media_type = state['last_media_type']
    last_crew = state['last_crew']
    last_cast = state['last_cast']
    user = state['user']
    
    context = []
    if last_media_name:
        context.append(f"{user} is interested in '{last_media_name}', which is a {last_media_type}.")
    if last_crew:
        context.append(f"The last crew information retrieved was: {last_crew}.")
    if last_cast:
        context.append(f"The last cast information retrieved was: {last_cast}.")
        
    system_context = SYSTEM_PROMPT
    if context:
        system_context += "\n\n## Current Context\n" + \
            "\n".join(f"- {line}" for line in context)
    
    # Prepare messages: system prompt + full conversation history
    # This is crucial - the LLM sees ALL previous messages, not just the current one
    llm_messages = [SystemMessage(content=system_context)] + messages
    
    # call the model with tools
    response = model_with_tools.invoke(
        llm_messages
    )
    
    return {'messages': [response]}


def tool_node(state: MediaQuery):
    """Perform tool calls based on LLM requests."""
    
    messages = state['messages']
    last_message = messages[-1]
    
    results = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call['name']
        tool_args = tool_call['args']
        
        tool = tools_with_names.get(tool_name)
        tool_result = tool.invoke(tool_args)
        
        results.append(
            ToolMessage(
                content=tool_result,
                tool_call_id=tool_call['id'],
                name=tool_name
            )
        )
    
    # return all tool result, 
    # they will be added to the conversation state['messages'] for next LLM call    
    return {'messages': results}


def update_context(state: MediaQuery):
    """Update the context based on the user's intent."""
    
    messages = state['messages']
    updates = {}
    
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                args = tool_call.get('args', {})
                
                # Extract player name if present and not already captured
                if 'media_name' in args and args['media_name'] and 'last_media_name' not in updates:
                    updates['last_media_name'] = args['media_name']
                    
                # Extract media type if present and not already captured
                if 'media_type' in args and args['media_type'] and 'last_media_type' not in updates:
                    updates['last_media_type'] = args['media_type']
                
                # Extract crew info if present and not already captured
                if 'get_crew' in args and args['get_crew'] and 'last_crew' not in updates:
                    updates['last_crew'] = args['get_crew']
                
                # Extract cast info if present and not already captured
                if 'get_cast' in args and args['get_cast'] and 'last_cast' not in updates:
                    updates['last_cast'] = args['get_cast']
            
            break  # Stop after processing the most recent tool call with relevant info
    
    return updates


def should_continue(state: MediaQuery):
    """deciding whether we continue to the next node"""
    
    messages = state['messages']
    last_message = messages[-1]
    
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tool_node"  # there are tool calls to process
    
    return END


agent = StateGraph(MediaQuery)

# add nodes
agent.add_node("llm_call", llm_call)
agent.add_node("tool_node", tool_node)
agent.add_node("update_context", update_context)

# add edges
agent.add_edge(START, "llm_call")

# add conditional edges
agent.add_conditional_edges(
    "llm_call",
    should_continue,
    ["tool_node", END]
)

# after tool calls, update context
agent.add_edge("tool_node", "update_context")

# after context update, go back to LLM call
agent.add_edge("update_context", "llm_call")

# setup memory saver and store
saver = InMemorySaver()
store = InMemoryStore()

# compile the agent
media_agent = agent.compile(
    store=store,
    checkpointer=saver
)


thread_id = "media_query_1"
user_id = str(uuid.uuid4())

config = {
    'configurable': {
        'thread_id': thread_id,
        'user_id': user_id,
    }
}


while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ['exit', 'quit', 'q']:
            print("Exiting...")
            break
        
        # create new human message
        human_message = HumanMessage(content=user_input)
        results = media_agent.invoke(
            {
                'messages': [human_message],
                'last_media_name': None,  # ← Add default
                'last_media_type': None,  # ← Add default
                'last_crew': None,        # ← Add default
                'last_cast': None,        # ← Add default
                'user': user_id,          # ← Add user
                'llm_calls': 0            # ← Add counter
            },
            config=config
        )
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()  # ← Helpful for debugging
        break
    
    for msg in results['messages']:
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            print(f"AI: {msg.content}")
            break
        
               
        
    