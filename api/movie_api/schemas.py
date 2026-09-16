from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    thread_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)

class ChatResponse(BaseModel):
    content: str
