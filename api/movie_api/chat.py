from fastapi.responses import StreamingResponse
from fastapi import APIRouter
from .schemas import ChatRequest
from .agent_client import run_agent

router = APIRouter()

# Without these an SSE stream can be buffered and delivered in one lump at the
# end, which looks exactly like the agent hanging. no-cache stops the browser
# caching a stream, and X-Accel-Buffering tells nginx-style proxies to pass
# bytes straight through.
SSE_HEADERS = {
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'X-Accel-Buffering': 'no',
}


@router.post('/chat')
async def chat(req: ChatRequest):
    # run_agent is an async *generator*, not a coroutine: calling it returns the
    # generator that StreamingResponse iterates. Awaiting it raises TypeError.
    return StreamingResponse(
        run_agent(req.thread_id, req.content),
        media_type='text/event-stream',
        headers=SSE_HEADERS,
    )
