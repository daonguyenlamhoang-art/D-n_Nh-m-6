"""Schemas cho Danh mục món ăn (T3D1F81, T3D1F9B)"""
from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sort_order: int = 0
    is_active: bool = True


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    sort_order: int | None = None
    is_active: bool | None = None


class CategoryReorderItem(BaseModel):
    id: int
    sort_order: int


class CategoryOut(CategoryBase):
    id: int
    dish_count: int = 0

    class Config:
        from_attributes = True
