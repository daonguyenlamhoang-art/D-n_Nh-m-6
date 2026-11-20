"""Schemas cho Admin Auth & Dashboard"""
from datetime import datetime
from pydantic import BaseModel, Field


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class AdminUserOut(BaseModel):
    id: int
    username: str | None
    full_name: str | None
    role: str

    class Config:
        from_attributes = True


class DashboardStatsOut(BaseModel):
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    delivering_orders: int
    completed_orders: int
    cancelled_orders: int
    total_revenue: int
    active_dishes_count: int
    active_categories_count: int
