"""Schemas cho Món ăn và Tùy chọn"""
from datetime import datetime
from pydantic import BaseModel, Field


class DishOptionOut(BaseModel):
    id: int
    dish_id: int
    option_name: str
    extra_price: int
    is_active: bool

    class Config:
        from_attributes = True


class DishBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    category_id: int
    price: int = Field(..., gt=0)
    description: str | None = None
    image_url: str | None = None
    is_available: bool = True
    is_active: bool = True


class DishCreate(DishBase):
    pass


class DishUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    category_id: int | None = None
    price: int | None = Field(None, gt=0)
    description: str | None = None
    image_url: str | None = None
    is_available: bool | None = None
    is_active: bool | None = None


class DishOut(DishBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category_name: str | None = None
    options: list[DishOptionOut] = []

    class Config:
        from_attributes = True
