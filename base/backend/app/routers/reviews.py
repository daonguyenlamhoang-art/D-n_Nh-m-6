"""Router Đánh giá món ăn (Reviews) cho Khách hàng & Admin (T3D2A75)."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.auth import get_current_admin
from app.db.session import get_db
from app.models.dish import Dish
from app.models.order import Order
from app.models.review import Review
from app.models.user import User
from app.schemas.review import (
    ReviewCreate,
    ReviewOut,
    ReviewReplyRequest,
    ReviewVisibilityUpdate,
)

router = APIRouter(tags=["Reviews"])


def _to_review_out(r: Review) -> ReviewOut:
    dto = ReviewOut.model_validate(r)
    if not dto.customer_name:
        dto.customer_name = r.user.full_name if (r.user and r.user.full_name) else "Khách hàng"
    dto.dish_name = r.dish.name if r.dish else None
    return dto


@router.get("/dishes/{dish_id}/reviews")
def get_dish_reviews(dish_id: int, db: Session = Depends(get_db)):
    """Lấy danh sách đánh giá hiển thị của 1 món kèm điểm trung bình (T3D2A75)."""
    reviews = (
        db.query(Review)
        .filter(Review.dish_id == dish_id, Review.is_visible == True)
        .options(joinedload(Review.user), joinedload(Review.dish))
        .order_by(Review.created_at.desc())
        .all()
    )
    total = len(reviews)
    avg_rating = round(sum(r.rating for r in reviews) / total, 1) if total > 0 else 5.0
    return {
        "dish_id": dish_id,
        "avg_rating": avg_rating,
        "total_reviews": total,
        "items": [_to_review_out(r) for r in reviews],
    }


@router.post("/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_dish_review(
    rev_in: ReviewCreate,
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Khách có đơn Hoàn thành chấm sao, nhận xét và ảnh từng món 1 lần duy nhất (T3D2A75)."""
    code_clean = rev_in.order_code.strip().upper()
    eff_token = (rev_in.guest_token or x_guest_token or "").strip()
    eff_phone = (rev_in.phone or "").strip()

    order = (
        db.query(Order)
        .filter(Order.order_code == code_clean)
        .options(joinedload(Order.items))
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORDER_NOT_FOUND", "message": "Không tìm thấy đơn hàng", "details": {}},
        )

    is_owner = False
    if eff_phone and order.phone == eff_phone:
        is_owner = True
    if eff_token and order.guest_token and order.guest_token == eff_token:
        is_owner = True

    if not is_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN_ORDER", "message": "Bạn chỉ được đánh giá đơn hàng của chính mình", "details": {}},
        )

    if order.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ORDER_NOT_COMPLETED",
                "message": "Chỉ đơn hàng đã ở trạng thái 'Hoàn thành' mới được đánh giá món",
                "details": {"current_status": order.status},
            },
        )

    in_order = any(it.dish_id == rev_in.dish_id for it in order.items)
    if not in_order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DISH_NOT_IN_ORDER", "message": "Món ăn này không thuộc đơn hàng của bạn", "details": {}},
        )

    already = (
        db.query(Review)
        .filter(Review.order_id == order.id, Review.dish_id == rev_in.dish_id)
        .first()
    )
    if already:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "ALREADY_REVIEWED",
                "message": "Bạn đã đánh giá món ăn này trong đơn hàng rồi (mỗi món trong đơn chỉ đánh giá 1 lần)",
                "details": {},
            },
        )

    new_rev = Review(
        order_id=order.id,
        user_id=order.user_id,
        dish_id=rev_in.dish_id,
        customer_name=order.customer_name,
        rating=rev_in.rating,
        comment=(rev_in.comment or "").strip() or None,
        image_url=(rev_in.image_url or "").strip() or None,
        is_visible=True,
    )
    db.add(new_rev)
    db.commit()
    db.refresh(new_rev)
    return _to_review_out(new_rev)


# ----------------- ADMIN QUẢN LÝ & TRẢ LỜI ĐÁNH GIÁ (T3D2A75) -----------------
@router.get("/admin/reviews", response_model=list[ReviewOut])
def admin_list_reviews(
    dish_id: Optional[int] = None,
    is_visible: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Admin xem toàn bộ danh sách đánh giá (kể cả đánh giá đã ẩn)."""
    query = db.query(Review).options(joinedload(Review.user), joinedload(Review.dish))
    if dish_id is not None:
        query = query.filter(Review.dish_id == dish_id)
    if is_visible is not None:
        query = query.filter(Review.is_visible == is_visible)
    reviews = query.order_by(Review.created_at.desc()).all()
    return [_to_review_out(r) for r in reviews]


@router.post("/admin/reviews/{review_id}/reply", response_model=ReviewOut)
def admin_reply_review(
    review_id: int,
    rep_in: ReviewReplyRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Cửa hàng / Admin trả lời đánh giá của khách (T3D2A75)."""
    rev = db.query(Review).filter(Review.id == review_id).options(joinedload(Review.user), joinedload(Review.dish)).first()
    if not rev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REVIEW_NOT_FOUND", "message": "Không tìm thấy đánh giá", "details": {}},
        )
    rev.store_reply = rep_in.store_reply.strip()
    rev.replied_at = datetime.utcnow()
    db.commit()
    db.refresh(rev)
    return _to_review_out(rev)


@router.patch("/admin/reviews/{review_id}/visibility", response_model=ReviewOut)
def admin_toggle_review_visibility(
    review_id: int,
    vis_in: ReviewVisibilityUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Admin ẩn hoặc hiện đánh giá vi phạm (T3D2A75)."""
    rev = db.query(Review).filter(Review.id == review_id).options(joinedload(Review.user), joinedload(Review.dish)).first()
    if not rev:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "REVIEW_NOT_FOUND", "message": "Không tìm thấy đánh giá", "details": {}},
        )
    rev.is_visible = vis_in.is_visible
    db.commit()
    db.refresh(rev)
    return _to_review_out(rev)
