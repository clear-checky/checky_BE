from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []


class ChatResponse(BaseModel):
    message: str
    conversation_history: List[ChatMessage]
    timestamp: datetime
