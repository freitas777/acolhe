from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=4000)
    conversation_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationCreate(BaseModel):
    title: Optional[str] = "Nova conversa"


class ConversationResponse(BaseModel):
    id: str
    title: str
    messages: List[ChatMessageResponse]
    created_at: datetime
    user_id: int

    model_config = {"from_attributes": True}


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    user_message: ChatMessageResponse
    assistant_message: Optional[ChatMessageResponse] = None
    conversation_id: str
