from typing import AsyncGenerator
from starlette.concurrency import iterate_in_threadpool
from movie_chatbot.agent.graph import media_agent
from langchain_core.messages import HumanMessage
import json


# functions takes values from chat.py which comes from frontend users input
# thread_id is the id of the current message
# content is usrs message
async def run_agent(thread_id: str, content: str) -> AsyncGenerator[str, None]:
    # config and messages are shapes langgraph needs to invoke the agent.
    # messages is a list because it grows over time as conversation history accumulates.
    config = { 'configurable': { 'thread_id': thread_id }}
    messages = {'messages': [HumanMessage(content=content)]}

    """
    .stream is telling langgraph to start ruuning,
    similar to llm_call -> tool_node -> update_context -> llm_call in a loop until the agent decides to stop (see graph.py).
    stream_mode says which of the two categores below (messages, updates) the chunks belong to
    "messages" chunks from llm_call, the tokens (the literal words) that the LLM is generating as it generates them.
    "updates" chunks from nodes when graph is done. basically when lllm_call, tool_node,
    and update_context are done, langgraph says here is what this node did (snapshot of what changed).
    """
    # The sync .stream is used rather than .astream because the graph is
    # compiled with SqliteSaver, which is sync-only -- .astream calls its
    # aget_tuple and raises NotImplementedError mid-response, which the client
    # sees as the connection dropping. iterate_in_threadpool runs the sync
    # iterator on a worker thread and hands the chunks back as an async
    # iterator, so the event loop is never blocked and the CLI, which calls the
    # same compiled agent synchronously, keeps working unchanged.
    stream = media_agent.stream(messages, config, stream_mode=['messages', 'updates'])

    async for stream_mode, chunk in iterate_in_threadpool(stream):
        """
        1. when stream_mode is messages, langgraph returns a pair
            (actual text chunk containing .content, and metadata (which node generated it, etc.) about the chunk)
        2. when stram_node is updates, the chunk is a dict looking like:
            {'tool_node': {...the new state...}} (the key says which node ran)
            so we can iterate over the keys to check if it was tool_node,
            if yes, we yield a tool_call event to the frontend so it can display the tool call in the chat window.
        """
        if stream_mode == 'messages':
            message_chunk, metadata = chunk
            # stream_mode='messages' carries every node's messages, tool_node's
            # ToolMessage included -- without this the raw tool output ("Director:
            # Christopher Nolan") is streamed as if the assistant had said it, and
            # lands glued to the front of the real reply.
            if metadata.get('langgraph_node') == 'llm_call' and message_chunk.content:
                yield f"data: {json.dumps({
                    'type': 'token',
                    'content': message_chunk.content,
                })}\n\n"
        elif stream_mode == 'updates':
            for node_name in chunk:
                if node_name == 'tool_node':
                    yield f"data: {json.dumps({
                        'type': 'tool_call',
                        'node': node_name,
                    })}\n\n"
