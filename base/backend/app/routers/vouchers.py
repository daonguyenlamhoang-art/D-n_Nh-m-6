"""Router Mã giảm giá (Vouchers) cho Khách hàng & Admin (T3D2A5B)."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.auth import get_current_admin
from app.db.session import get_db
from app.models.user import User
from app.models.voucher import Voucher
from app.schemas.voucher import (
    VoucherCheckOut,
    VoucherCheckRequest,
    VoucherCreate,
    VoucherOut,
    VoucherUpdate,
)

router = APIRouter(tags=["Vouchers"])


def evaluate_voucher(db: Session, code: str, subtotal: int) -> tuple[Voucher | None, int, str]:
    """Kiểm tra mã giảm giá (không phân biệt hoa thường): còn hoạt động, còn hạn, còn lượt, đủ đơn tối thiểu."""
    clean_code = (code or "").strip().upper()
    if not clean_code:
        return None, 0, "Vui lòng nhập mã giảm giá"

    voucher = db.query(Voucher).filter(func.upper(Voucher.code) == clean_code).first()
    if not voucher or not voucher.is_active:
        return None, 0, "Mã giảm giá không tồn tại hoặc đã ngừng áp dụng"

    now = datetime.now()
    if voucher.start_at and now < voucher.start_at:
        return None, 0, "Mã giảm giá chưa đến thời gian có hiệu lực"
    if voucher.end_at and now > voucher.end_at:
        return None, 0, "Mã giảm giá đã hết hạn sử dụng"

    if voucher.usage_limit is not None and (voucher.used_count or 0) >= voucher.usage_limit:
        return None, 0, "Mã giảm giá đã hết lượt sử dụng"

    if subtotal < (voucher.min_order_amount or 0):
        return (
            None,
            0,
            f"Đơn hàng tối thiểu để áp dụng mã '{voucher.code}' là {voucher.min_order_amount:,}đ",
        )

    if voucher.discount_type == "percent":
        disc = int(round(subtotal * voucher.discount_value / 100.0))
    else:
        disc = int(voucher.discount_value)

    if voucher.max_discount_amount is not None and voucher.max_discount_amount > 0:
        disc = min(disc, voucher.max_discount_amount)

    disc = max(0, min(disc, subtotal))
    return voucher, disc, f"Áp dụng mã '{voucher.code}' thành công (-{disc:,}đ)"


@router.get("/vouchers/active", response_model=list[VoucherOut])
def get_active_vouchers(db: Session = Depends(get_db)):
    """Lấy danh sách mã giảm giá đang hoạt động cho khách hàng."""
    now = datetime.now()
    vouchers = (
        db.query(Voucher)
        .filter(Voucher.is_active == True, Voucher.end_at >= now)
        .order_by(Voucher.id.asc())
        .all()
    )
    return [
        VoucherOut.model_validate(v)
        for v in vouchers
        if v.usage_limit is None or (v.used_count or 0) < v.usage_limit
    ]


@router.post("/vouchers/check", response_model=VoucherCheckOut)
def check_voucher_post(req: VoucherCheckRequest, db: Session = Depends(get_db)):
    """API kiểm tra mã giảm giá (POST) trả số tiền giảm cho module Giỏ hàng (T3D2A5B)."""
    voucher, disc, msg = evaluate_voucher(db, req.code, req.subtotal)
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_VOUCHER", "message": msg, "details": {}},
        )
    return VoucherCheckOut(
        valid=True,
        voucher_id=voucher.id,
        code=voucher.code,
        discount_type=voucher.discount_type,
        discount_value=voucher.discount_value,
        discount_amount=disc,
        final_subtotal=max(0, req.subtotal - disc),
        message=msg,
    )


@router.get("/vouchers/check", response_model=VoucherCheckOut)
def check_voucher_get(
    code: str = Query(..., min_length=1),
    subtotal: int = Query(..., ge=0),
    db: Session = Depends(get_db),
):
    """API kiểm tra mã giảm giá (GET) không phân biệt hoa thường (T3D2A5B)."""
    return check_voucher_post(VoucherCheckRequest(code=code, subtotal=subtotal), db=db)


# ----------------- ADMIN QUẢN LÝ MÃ GIẢM GIÁ (T3D2A5B) -----------------
@router.get("/admin/vouchers", response_model=list[VoucherOut])
def admin_list_vouchers(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Admin xem danh sách tất cả mã giảm giá."""
    return db.query(Voucher).order_by(Voucher.id.desc()).all()


@router.post("/admin/vouchers", response_model=VoucherOut, status_code=status.HTTP_201_CREATED)
def admin_create_voucher(
    v_in: VoucherCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Admin tạo mã giảm giá mới."""
    code_clean = v_in.code.strip().upper()
    exists = db.query(Voucher).filter(func.upper(Voucher.code) == code_clean).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "VOUCHER_EXISTS", "message": f"Mã giảm giá '{code_clean}' đã tồn tại", "details": {}},
        )
    if v_in.end_at <= v_in.start_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_DATES", "message": "Thời gian kết thúc phải sau thời gian bắt đầu", "details": {}},
        )
    if v_in.discount_type == "percent" and v_in.discount_value > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PERCENT", "message": "Phần trăm giảm giá không được vượt quá 100%", "details": {}},
        )

    voucher = Voucher(
        code=code_clean,
        discount_type=v_in.discount_type,
        discount_value=v_in.discount_value,
        min_order_amount=v_in.min_order_amount,
        max_discount_amount=v_in.max_discount_amount,
        start_at=v_in.start_at,
        end_at=v_in.end_at,
        usage_limit=v_in.usage_limit,
        used_count=0,
        is_active=v_in.is_active,
    )
    db.add(voucher)
    db.commit()
    db.refresh(voucher)
    return voucher


@router.put("/admin/vouchers/{voucher_id}", response_model=VoucherOut)
def admin_update_voucher(
    voucher_id: int,
    v_in: VoucherUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Admin sửa hoặc ngừng mã giảm giá."""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "VOUCHER_NOT_FOUND", "message": "Không tìm thấy mã giảm giá", "details": {}},
        )

    if v_in.code is not None:
        code_clean = v_in.code.strip().upper()
        dup = db.query(Voucher).filter(func.upper(Voucher.code) == code_clean, Voucher.id != voucher_id).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "VOUCHER_EXISTS", "message": "Mã giảm giá đã tồn tại", "details": {}},
            )
        voucher.code = code_clean

    for field in [
        "discount_type",
        "discount_value",
        "min_order_amount",
        "max_discount_amount",
        "start_at",
        "end_at",
        "usage_limit",
        "is_active",
    ]:
        val = getattr(v_in, field)
        if val is not None:
            setattr(voucher, field, val)

    db.commit()
    db.refresh(voucher)
    return voucher


@router.patch("/admin/vouchers/{voucher_id}/toggle", response_model=VoucherOut)
def admin_toggle_voucher(
    voucher_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Admin bật/tắt (ngừng) mã giảm giá nhanh."""
    voucher = db.query(Voucher).filter(Voucher.id == voucher_id).first()
    if not voucher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "VOUCHER_NOT_FOUND", "message": "Không tìm thấy mã giảm giá", "details": {}},
        )
    voucher.is_active = not voucher.is_active
    db.commit()
    db.refresh(voucher)
    return voucher
