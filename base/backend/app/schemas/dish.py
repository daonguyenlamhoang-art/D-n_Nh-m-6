"""Schemas cho Món ăn và Tùy chọn (T3D1F81, T3D1FB5, T3D2354)"""
from datetime import datetime
from pydantic import BaseModel, Field


class DishOptionBase(BaseModel):
    option_group: str = Field(default="Topping", min_length=1, max_length=50)
    option_name: str = Field(..., min_length=1, max_length=100)
    extra_price: int = Field(default=0, ge=0)
    is_required: bool = False
    max_select: int = Field(default=1, ge=1)
    is_active: bool = True


class DishOptionCreate(DishOptionBase):
    pass


class DishOptionUpdate(BaseModel):
    option_group: str | None = Field(None, min_length=1, max_length=50)
    option_name: str | None = Field(None, min_length=1, max_length=100)
    extra_price: int | None = Field(None, ge=0)
    is_required: bool | None = None
    max_select: int | None = Field(None, ge=1)
    is_active: bool | None = None


class DishOptionOut(DishOptionBase):
    id: int
    dish_id: int

    class Config:
        from_attributes = True


class OptionGroupOut(BaseModel):
    group_name: str
    is_required: bool = False
    max_select: int = 1
    options: list[DishOptionOut] = []


class DishBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    category_id: int
    price: int = Field(..., gt=0)
    description: str | None = None
    image_url: str | None = None
    status: str = "AVAILABLE"
    is_available: bool = True
    is_active: bool = True
    is_featured: bool = False
    is_combo: bool = False
    combo_items_json: str | None = None


class DishCreate(DishBase):
    options: list[DishOptionCreate] | None = None


class DishUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=150)
    category_id: int | None = None
    price: int | None = Field(None, gt=0)
    description: str | None = None
    image_url: str | None = None
    status: str | None = None
    is_available: bool | None = None
    is_active: bool | None = None
    is_featured: bool | None = None
    is_combo: bool | None = None
    combo_items_json: str | None = None
    options: list[DishOptionCreate] | None = None


class DishOut(DishBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category_name: str | None = None
    avg_rating: float = 5.0
    review_count: int = 0
    sold_count: int = 0
    options: list[DishOptionOut] = []
    option_groups: list[OptionGroupOut] = []

    class Config:
        from_attributes = True
