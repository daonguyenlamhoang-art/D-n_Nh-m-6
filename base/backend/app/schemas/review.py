"""Schemas cho Đánh giá món ăn (Review) - T3D2A41, T3D2A75"""
from datetime import datetime
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    order_code: str = Field(..., min_length=1, max_length=30)
    phone: str | None = None
    guest_token: str | None = None
    dish_id: int
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)
    image_url: str | None = Field(default=None, max_length=500)


class ReviewReplyRequest(BaseModel):
    store_reply: str = Field(..., min_length=1, max_length=1000)


class ReviewVisibilityUpdate(BaseModel):
    is_visible: bool


class ReviewOut(BaseModel):
    id: int
    order_id: int | None = None
    user_id: int | None = None
    dish_id: int
    dish_name: str | None = None
    customer_name: str | None = "Khách hàng"
    rating: int
    comment: str | None = None
    image_url: str | None = None
    store_reply: str | None = None
    replied_at: datetime | None = None
    is_visible: bool = True
    created_at: datetime

    class Config:
        from_attributes = True
