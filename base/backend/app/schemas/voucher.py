"""Schemas cho Mã giảm giá (Voucher) - T3D2A41, T3D2A5B"""
from datetime import datetime
from pydantic import BaseModel, Field


class VoucherBase(BaseModel):
    code: str = Field(..., min_length=2, max_length=30)
    discount_type: str = Field(..., pattern="^(fixed|percent)$")
    discount_value: int = Field(..., gt=0)
    min_order_amount: int = Field(default=0, ge=0)
    max_discount_amount: int | None = Field(default=None, ge=0)
    start_at: datetime
    end_at: datetime
    usage_limit: int | None = Field(default=None, ge=1)
    is_active: bool = True


class VoucherCreate(VoucherBase):
    pass


class VoucherUpdate(BaseModel):
    code: str | None = Field(None, min_length=2, max_length=30)
    discount_type: str | None = Field(None, pattern="^(fixed|percent)$")
    discount_value: int | None = Field(None, gt=0)
    min_order_amount: int | None = Field(None, ge=0)
    max_discount_amount: int | None = Field(None, ge=0)
    start_at: datetime | None = None
    end_at: datetime | None = None
    usage_limit: int | None = Field(None, ge=1)
    is_active: bool | None = None


class VoucherOut(VoucherBase):
    id: int
    used_count: int = 0

    class Config:
        from_attributes = True


class VoucherCheckRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=30)
    subtotal: int = Field(..., ge=0)


class VoucherCheckOut(BaseModel):
    valid: bool
    voucher_id: int | None = None
    code: str
    discount_type: str | None = None
    discount_value: int = 0
    discount_amount: int = 0
    final_subtotal: int = 0
    message: str
