"""Schemas cho Tin nhắn hỗ trợ (ChatMessage) - T3D2A41, T3D2DC1"""
from datetime import datetime
from pydantic import BaseModel, Field


class ChatMessageCreate(BaseModel):
    guest_token: str = Field(..., min_length=3, max_length=64)
    customer_name: str | None = Field(default="Khách hàng", max_length=100)
    order_id: int | None = None
    message: str = Field(..., min_length=1, max_length=2000)


class AdminChatReply(BaseModel):
    guest_token: str = Field(..., min_length=3, max_length=64)
    customer_name: str | None = None
    message: str = Field(..., min_length=1, max_length=2000)


class ChatMessageOut(BaseModel):
    id: int
    user_id: int | None = None
    order_id: int | None = None
    sender_type: str
    guest_token: str | None = None
    customer_name: str | None = None
    message: str
    is_read: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
