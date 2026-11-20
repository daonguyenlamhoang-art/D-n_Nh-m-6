"""Schemas cho Giỏ hàng (Cart, CartItem) - T3D25C2, T3D25F6, T3D262C"""
from datetime import datetime
from pydantic import BaseModel, Field


class CartItemCreate(BaseModel):
    dish_id: int
    quantity: int = Field(default=1, ge=1, le=99)
    dish_option_id: int | None = None
    selected_option_ids: list[int] | None = None
    note: str | None = Field(default=None, max_length=255)


class CartItemUpdate(BaseModel):
    quantity: int | None = Field(default=None, ge=0, le=99)
    dish_option_id: int | None = None
    selected_option_ids: list[int] | None = None
    note: str | None = Field(default=None, max_length=255)


class CartItemOut(BaseModel):
    id: int
    cart_id: int
    dish_id: int
    dish_name: str | None = None
    image_url: str | None = None
    dish_option_id: int | None = None
    option_name: str | None = None
    selected_options_json: str | None = None
    note: str | None = None
    quantity: int
    base_price: int = 0
    option_extra_price: int = 0
    unit_price: int = 0
    line_total: int = 0
    is_available: bool = True
    is_active: bool = True

    class Config:
        from_attributes = True


class CartCalculationOut(BaseModel):
    cart_id: int | None = None
    guest_token: str | None = None
    items: list[CartItemOut] = []
    subtotal: int = 0
    area: str = "Nội thành"
    shipping_fee: int = 0
    voucher_code: str | None = None
    discount_amount: int = 0
    total_amount: int = 0
    has_unavailable_item: bool = False
    warnings: list[str] = []
