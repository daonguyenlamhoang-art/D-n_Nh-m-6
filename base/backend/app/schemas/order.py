"""Schemas cho Đơn hàng, Chi tiết đơn và Tra cứu đơn (FR-06, FR-07, BR-01..18)."""
import re
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class OrderItemCreate(BaseModel):
    dish_id: int
    quantity: int = Field(..., ge=1, le=99)
    dish_option_id: int | None = None


class OrderCreate(BaseModel):
    customer_name: str = Field(..., min_length=1, max_length=100)
    phone: str = Field(..., min_length=10, max_length=10)
    address: str = Field(..., min_length=1, max_length=255)
    note: str | None = Field(None, max_length=500)
    expected_total: int | None = None
    items: list[OrderItemCreate] = Field(..., min_length=1, max_length=30)

    @field_validator("customer_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        val = v.strip()
        if not val:
            raise ValueError("Họ tên người nhận không được để trống")
        return val

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        val = v.strip()
        if not re.match(r"^0[0-9]{9}$", val):
            raise ValueError("Số điện thoại không hợp lệ (phải đúng 10 số và bắt đầu bằng số 0)")
        return val

    @field_validator("address")
    @classmethod
    def clean_address(cls, v: str) -> str:
        val = v.strip()
        if not val:
            raise ValueError("Địa chỉ nhận hàng không được để trống")
        return val


class OrderLookupRequest(BaseModel):
    order_code: str = Field(..., min_length=1, max_length=30)
    phone: str = Field(..., min_length=10, max_length=10)

    @field_validator("order_code")
    @classmethod
    def clean_code(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("phone")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        val = v.strip()
        if not re.match(r"^0[0-9]{9}$", val):
            raise ValueError("Số điện thoại không hợp lệ")
        return val


class OrderStatusUpdate(BaseModel):
    status: str
    expected_current_status: str | None = None
    note: str | None = None


class OrderItemOut(BaseModel):
    id: int
    dish_id: int
    dish_name: str
    option_name: str | None = None
    quantity: int
    unit_price: int
    subtotal: int

    class Config:
        from_attributes = True


class OrderStatusHistoryOut(BaseModel):
    id: int
    old_status: str | None = None
    new_status: str
    note: str | None = None
    changed_at: datetime

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    order_code: str
    customer_name: str
    phone: str
    address: str
    note: str | None = None
    subtotal: int
    discount_amount: int
    total_amount: int
    payment_method: str
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemOut] = []
    status_histories: list[OrderStatusHistoryOut] = []

    class Config:
        from_attributes = True


class OrderLookupOut(BaseModel):
    order_code: str
    status: str
    status_display: str
    created_at: datetime
    total_amount: int
    payment_method: str
    customer_name: str
    masked_address: str
    items: list[OrderItemOut] = []
