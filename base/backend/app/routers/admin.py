"""Router Quản trị viên (Admin) (FR-08..12, FR-15, BR-08..11, TC-14..22, TC-32, TC-34..35)."""
import json
import os
import time
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.auth import (
    clear_session_cookie,
    create_session,
    get_current_admin,
    invalidate_session,
    set_session_cookie,
    verify_password,
    SESSION_COOKIE_NAME,
)
from app.core.rate_limit import (
    check_admin_login_rate_limit,
    record_admin_login_failure,
    reset_admin_login_failure,
)
from app.db.session import get_db
from app.models.category import Category
from app.models.dish import Dish, DishOption
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.review import Review
from app.models.user import User
from app.models.voucher import Voucher
from app.routers.dishes import enrich_dishes_list
from app.schemas.admin import AdminLoginRequest, AdminUserOut, DashboardStatsOut
from app.schemas.category import CategoryCreate, CategoryOut, CategoryReorderItem, CategoryUpdate
from app.schemas.dish import (
    DishCreate,
    DishOptionCreate,
    DishOptionOut,
    DishOptionUpdate,
    DishOut,
    DishUpdate,
)
from app.schemas.order import OrderCancelRequest, OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/admin", tags=["Admin"])

# Ma trận chuyển trạng thái hợp lệ theo mục 4.1
VALID_TRANSITIONS = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["preparing", "cancelled"],
    "preparing": ["delivering", "cancelled"],
    "delivering": ["completed"],
    "completed": [],
    "cancelled": [],
}


# ----------------- XÁC THỰC ADMIN (FR-08) -----------------
@router.post("/login")
def admin_login(
    login_in: AdminLoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    """Đăng nhập Admin có chống tấn công dò mật khẩu Rate Limit (FR-08, TC-14, TC-15, TC-32)."""
    client_ip = request.client.host if request.client else "unknown"
    rate_key = f"{client_ip}:{login_in.username}"

    # 1. Kiểm tra rate limit
    is_allowed, remaining_sec = check_admin_login_rate_limit(rate_key)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "TOO_MANY_REQUESTS",
                "message": f"Tài khoản hoặc IP của bạn đã bị tạm khóa 15 phút do nhập sai 5 lần liên tiếp. Vui lòng thử lại sau {remaining_sec} giây.",
                "details": {"retry_after_seconds": remaining_sec},
            },
        )

    # 2. Tìm user trong bảng users
    user = (
        db.query(User)
        .filter(User.username == login_in.username, User.role == "admin")
        .first()
    )

    # 3. Đối chiếu mật khẩu băm
    if not user or not user.is_active or not verify_password(login_in.password, user.password_hash or ""):
        remaining_attempts = record_admin_login_failure(rate_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Sai tên đăng nhập hoặc mật khẩu",
                "details": {"remaining_attempts": remaining_attempts},
            },
        )

    # Đăng nhập thành công -> Reset số lần thử sai
    reset_admin_login_failure(rate_key)

    # Tạo phiên và gắn Cookie HttpOnly
    token = create_session(user.id, user.username or "")
    set_session_cookie(response, token)

    return {
        "message": "Đăng nhập thành công",
        "token": token,
        "user": AdminUserOut.model_validate(user),
    }


@router.post("/logout")
def admin_logout(
    request: Request,
    response: Response,
    current_admin: User = Depends(get_current_admin),
):
    """Đăng xuất Admin, hủy phiên."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        invalidate_session(token)
    clear_session_cookie(response)
    return {"message": "Đăng xuất thành công"}


@router.get("/me", response_model=AdminUserOut)
def get_current_admin_info(current_admin: User = Depends(get_current_admin)):
    """Kiểm tra phiên đăng nhập của Admin."""
    return AdminUserOut.model_validate(current_admin)


# ----------------- THỐNG KÊ DASHBOARD (FR-15) -----------------
@router.get("/dashboard/stats", response_model=DashboardStatsOut)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Lấy số liệu thống kê đơn hàng, doanh thu và món ăn cho Admin Dashboard (FR-15)."""
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    pending_orders = db.query(func.count(Order.id)).filter(Order.status == "pending").scalar() or 0
    confirmed_orders = db.query(func.count(Order.id)).filter(Order.status == "confirmed").scalar() or 0
    delivering_orders = db.query(func.count(Order.id)).filter(Order.status == "delivering").scalar() or 0
    completed_orders = db.query(func.count(Order.id)).filter(Order.status == "completed").scalar() or 0
    cancelled_orders = db.query(func.count(Order.id)).filter(Order.status == "cancelled").scalar() or 0

    total_revenue = (
        db.query(func.sum(Order.total_amount))
        .filter(Order.status == "completed")
        .scalar()
        or 0
    )

    active_dishes_count = db.query(func.count(Dish.id)).filter(Dish.is_active == True).scalar() or 0
    active_categories_count = db.query(func.count(Category.id)).filter(Category.is_active == True).scalar() or 0

    return DashboardStatsOut(
        total_orders=total_orders,
        pending_orders=pending_orders,
        confirmed_orders=confirmed_orders,
        delivering_orders=delivering_orders,
        completed_orders=completed_orders,
        cancelled_orders=cancelled_orders,
        total_revenue=total_revenue,
        active_dishes_count=active_dishes_count,
        active_categories_count=active_categories_count,
    )


@router.get("/dashboard/analytics")
def get_dashboard_analytics(
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    group_by: str = Query("day", pattern="^(day|month)$"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """API Thống kê Dashboard Admin chi tiết theo khoảng thời gian cho Chart.js (T3D2E11):
    - Doanh thu theo ngày / tháng.
    - Số đơn theo từng trạng thái.
    - Món bán chạy nhất.
    - Điểm đánh giá trung bình toàn quán.
    - Tổng số lượt mã giảm giá đã sử dụng.
    """
    order_query = db.query(Order)
    if date_from:
        try:
            dt_from = datetime.strptime(date_from.strip(), "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            order_query = order_query.filter(Order.created_at >= dt_from)
        except ValueError:
            pass
    if date_to:
        try:
            dt_to = datetime.strptime(date_to.strip(), "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            order_query = order_query.filter(Order.created_at <= dt_to)
        except ValueError:
            pass

    orders_in_range = order_query.options(joinedload(Order.items)).order_by(Order.created_at.asc()).all()

    status_counts = {
        "pending": 0,
        "confirmed": 0,
        "preparing": 0,
        "delivering": 0,
        "completed": 0,
        "cancelled": 0,
    }
    revenue_buckets: dict[str, dict] = {}
    dish_sales: dict[int, dict] = {}
    total_revenue = 0

    for o in orders_in_range:
        st = o.status or "pending"
        status_counts[st] = status_counts.get(st, 0) + 1

        dt = o.created_at or datetime.now()
        period_key = dt.strftime("%Y-%m") if group_by == "month" else dt.strftime("%Y-%m-%d")
        if period_key not in revenue_buckets:
            revenue_buckets[period_key] = {"period": period_key, "revenue": 0, "orders_count": 0}
        revenue_buckets[period_key]["orders_count"] += 1

        if st != "cancelled":
            rev = int(o.total_amount or 0)
            if st == "completed":
                total_revenue += rev
            revenue_buckets[period_key]["revenue"] += rev

            for it in (o.items or []):
                if it.dish_id not in dish_sales:
                    dish_sales[it.dish_id] = {
                        "dish_id": it.dish_id,
                        "dish_name": it.dish_name,
                        "sold_quantity": 0,
                        "revenue": 0,
                    }
                dish_sales[it.dish_id]["sold_quantity"] += int(it.quantity or 0)
                dish_sales[it.dish_id]["revenue"] += int(it.subtotal or 0)

    avg_rating_val = db.query(func.avg(Review.rating)).filter(Review.is_visible == True).scalar()
    avg_rating = round(float(avg_rating_val or 5.0), 2)
    total_reviews = db.query(func.count(Review.id)).filter(Review.is_visible == True).scalar() or 0
    vouchers_used_count = db.query(func.sum(Voucher.used_count)).scalar() or 0

    top_dishes = sorted(dish_sales.values(), key=lambda x: (-x["sold_quantity"], -x["revenue"]))[:6]
    revenue_series = sorted(revenue_buckets.values(), key=lambda x: x["period"])

    return {
        "total_orders": len(orders_in_range),
        "total_revenue": total_revenue,
        "avg_rating": avg_rating,
        "total_reviews": total_reviews,
        "vouchers_used_count": int(vouchers_used_count),
        "orders_by_status": status_counts,
        "revenue_series": revenue_series,
        "top_dishes": top_dishes,
    }


# ----------------- QUẢN LÝ MÓN ĂN & TUỲ CHỌN (FR-09, T3D1FB5) -----------------
@router.post("/upload-image")
async def admin_upload_dish_image(
    file: UploadFile = File(...),
    current_admin: User = Depends(get_current_admin),
):
    """Upload file ảnh món ăn lưu vào frontend/assets/uploads (T3D1FB5)."""
    ext = os.path.splitext(file.filename or "image.png")[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_IMAGE_TYPE", "message": "Định dạng ảnh không hợp lệ (chỉ hỗ trợ PNG, JPG, WEBP, GIF, SVG)", "details": {}},
        )
    uploads_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "frontend", "assets", "uploads")
    )
    os.makedirs(uploads_dir, exist_ok=True)
    safe_name = f"dish_{int(time.time())}_{uuid.uuid4().hex[:6]}{ext}"
    file_path = os.path.join(uploads_dir, safe_name)
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    return {"image_url": f"/assets/uploads/{safe_name}", "filename": safe_name}


@router.get("/dishes")
def admin_get_dishes(
    search: Optional[str] = Query(None, max_length=100),
    category_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Xem toàn bộ món ăn (kể cả món đã ẩn) kèm phân trang, lọc trạng thái và tìm kiếm (FR-09, T3D1FB5)."""
    query = db.query(Dish).options(joinedload(Dish.category), joinedload(Dish.options))

    if category_id:
        query = query.filter(Dish.category_id == category_id)

    if status_filter:
        st = status_filter.strip().upper()
        if st == "HIDDEN":
            query = query.filter((Dish.is_active == False) | (Dish.status == "HIDDEN"))
        elif st == "OUT_OF_STOCK":
            query = query.filter(Dish.is_active == True, (Dish.is_available == False) | (Dish.status == "OUT_OF_STOCK"))
        elif st == "AVAILABLE":
            query = query.filter(Dish.is_active == True, Dish.is_available == True)

    if search:
        clean = search.strip()
        if clean:
            query = query.filter(Dish.name.ilike(f"%{clean}%"))

    total = query.count()
    dishes = query.order_by(Dish.id.desc()).offset((page - 1) * page_size).limit(page_size).all()
    items = enrich_dishes_list(db, dishes)

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.post("/dishes", response_model=DishOut, status_code=status.HTTP_201_CREATED)
def admin_create_dish(
    dish_in: DishCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Thêm món ăn mới kèm cấu hình nhóm tuỳ chọn (Size, Topping) (FR-09, T3D1FB5)."""
    cat = db.query(Category).filter(Category.id == dish_in.category_id).first()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CATEGORY_NOT_FOUND", "message": "Danh mục đã chọn không tồn tại", "details": {}},
        )

    if dish_in.price <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "INVALID_PRICE", "message": "Giá món ăn phải là số nguyên dương lớn hơn 0", "details": {}},
        )

    new_dish = Dish(
        category_id=dish_in.category_id,
        name=dish_in.name.strip(),
        description=dish_in.description.strip() if dish_in.description else None,
        price=dish_in.price,
        image_url=dish_in.image_url.strip() if dish_in.image_url else None,
        status=dish_in.status or "AVAILABLE",
        is_available=dish_in.is_available,
        is_active=dish_in.is_active,
        is_featured=dish_in.is_featured,
        is_combo=dish_in.is_combo,
        combo_items_json=dish_in.combo_items_json,
    )
    new_dish.sync_status_flags()
    db.add(new_dish)
    db.flush()

    if dish_in.options:
        for opt_in in dish_in.options:
            opt = DishOption(
                dish_id=new_dish.id,
                option_group=opt_in.option_group.strip() or "Topping",
                option_name=opt_in.option_name.strip(),
                extra_price=opt_in.extra_price,
                is_required=opt_in.is_required,
                max_select=opt_in.max_select,
                is_active=opt_in.is_active,
            )
            db.add(opt)

    db.commit()
    db.refresh(new_dish)
    return enrich_dishes_list(db, [new_dish])[0]


@router.put("/dishes/{dish_id}", response_model=DishOut)
def admin_update_dish(
    dish_id: int,
    dish_in: DishUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Cập nhật thông tin món ăn, nhóm tuỳ chọn hoặc ẩn món (FR-09, T3D1FB5)."""
    dish = db.query(Dish).filter(Dish.id == dish_id).options(joinedload(Dish.options), joinedload(Dish.category)).first()
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DISH_NOT_FOUND", "message": "Không tìm thấy món ăn", "details": {}},
        )

    if dish_in.category_id is not None:
        cat = db.query(Category).filter(Category.id == dish_in.category_id).first()
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CATEGORY_NOT_FOUND", "message": "Danh mục không tồn tại", "details": {}},
            )
        dish.category_id = dish_in.category_id

    if dish_in.name is not None:
        dish.name = dish_in.name.strip()
    if dish_in.description is not None:
        dish.description = dish_in.description.strip() if dish_in.description else None
    if dish_in.price is not None:
        if dish_in.price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_PRICE", "message": "Giá phải lớn hơn 0", "details": {}},
            )
        dish.price = dish_in.price
    if dish_in.image_url is not None:
        dish.image_url = dish_in.image_url.strip() if dish_in.image_url else None
    if dish_in.is_featured is not None:
        dish.is_featured = dish_in.is_featured
    if dish_in.is_combo is not None:
        dish.is_combo = dish_in.is_combo
    if dish_in.combo_items_json is not None:
        dish.combo_items_json = dish_in.combo_items_json

    if dish_in.status is not None:
        dish.status = dish_in.status
        if dish.status == "HIDDEN":
            dish.is_active = False
        elif dish.status == "OUT_OF_STOCK":
            dish.is_active = True
            dish.is_available = False
        elif dish.status == "AVAILABLE":
            dish.is_active = True
            dish.is_available = True

    if dish_in.is_available is not None:
        dish.is_available = dish_in.is_available
    if dish_in.is_active is not None:
        dish.is_active = dish_in.is_active

    dish.sync_status_flags()

    if dish_in.options is not None:
        db.query(DishOption).filter(DishOption.dish_id == dish.id).delete()
        for opt_in in dish_in.options:
            db.add(
                DishOption(
                    dish_id=dish.id,
                    option_group=opt_in.option_group.strip() or "Topping",
                    option_name=opt_in.option_name.strip(),
                    extra_price=opt_in.extra_price,
                    is_required=opt_in.is_required,
                    max_select=opt_in.max_select,
                    is_active=opt_in.is_active,
                )
            )

    db.commit()
    db.refresh(dish)
    return enrich_dishes_list(db, [dish])[0]


@router.delete("/dishes/{dish_id}")
def admin_delete_or_hide_dish(
    dish_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Xoá món ăn: Nếu món đã từng có trong đơn hàng thì chỉ chuyển sang Ẩn (T3D1FB5)."""
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DISH_NOT_FOUND", "message": "Không tìm thấy món ăn", "details": {}},
        )

    order_ref_count = db.query(func.count(OrderItem.id)).filter(OrderItem.dish_id == dish_id).scalar() or 0
    if order_ref_count > 0:
        dish.is_active = False
        dish.status = "HIDDEN"
        db.commit()
        return {
            "action": "hidden",
            "dish_id": dish_id,
            "message": f"Món '{dish.name}' đã có trong {order_ref_count} dòng đơn hàng nên hệ thống chỉ chuyển sang trạng thái Ẩn.",
        }

    db.delete(dish)
    db.commit()
    return {
        "action": "deleted",
        "dish_id": dish_id,
        "message": f"Đã xoá hoàn toàn món '{dish.name}'",
    }


@router.patch("/dishes/{dish_id}/availability", response_model=DishOut)
def admin_quick_toggle_availability(
    dish_id: int,
    is_available: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Nhân viên bật/tắt báo hết món nhanh trong ngày (món hết không đặt được) (T3D228F)."""
    dish = db.query(Dish).filter(Dish.id == dish_id).options(joinedload(Dish.category), joinedload(Dish.options)).first()
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DISH_NOT_FOUND", "message": "Không tìm thấy món ăn", "details": {}},
        )
    dish.is_available = (not dish.is_available) if is_available is None else is_available
    dish.sync_status_flags()
    db.commit()
    db.refresh(dish)
    return enrich_dishes_list(db, [dish])[0]


@router.patch("/dishes/{dish_id}/featured", response_model=DishOut)
def admin_quick_toggle_featured(
    dish_id: int,
    is_featured: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Nhân viên đánh dấu / bỏ đánh dấu món nổi bật cho trang chủ (T3D228F)."""
    dish = db.query(Dish).filter(Dish.id == dish_id).options(joinedload(Dish.category), joinedload(Dish.options)).first()
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DISH_NOT_FOUND", "message": "Không tìm thấy món ăn", "details": {}},
        )
    dish.is_featured = (not dish.is_featured) if is_featured is None else is_featured
    db.commit()
    db.refresh(dish)
    return enrich_dishes_list(db, [dish])[0]


class ComboComponentItem(BaseModel):
    dish_id: int
    quantity: int = Field(default=1, ge=1)


class ComboCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    price: int = Field(..., gt=0)
    category_id: int = 5
    image_url: Optional[str] = None
    description: Optional[str] = None
    is_featured: bool = True
    components: list[ComboComponentItem] = Field(..., min_length=2)


@router.post("/combos", response_model=DishOut, status_code=status.HTTP_201_CREATED)
def admin_create_combo_dish(
    combo_in: ComboCreateRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Admin tạo Combo gồm nhiều món với giá ưu đãi; hiển thị và đặt như một món (T3D2E66)."""
    comp_ids = [c.dish_id for c in combo_in.components]
    comp_dishes = db.query(Dish).filter(Dish.id.in_(comp_ids)).all()
    dish_map = {d.id: d for d in comp_dishes}

    parts_desc = []
    original_total = 0
    comp_snapshots = []

    for c in combo_in.components:
        d = dish_map.get(c.dish_id)
        if not d:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "COMPONENT_DISH_NOT_FOUND", "message": f"Không tìm thấy món thành phần ID={c.dish_id}", "details": {}},
            )
        original_total += d.price * c.quantity
        parts_desc.append(f"{c.quantity:02d} {d.name}")
        comp_snapshots.append({"dish_id": d.id, "dish_name": d.name, "quantity": c.quantity, "unit_price": d.price})

    saved_amount = max(0, original_total - combo_in.price)
    auto_desc = f"Bao gồm: {' + '.join(parts_desc)}."
    if saved_amount > 0:
        auto_desc += f" Giá gốc {original_total:,}đ (Tiết kiệm {saved_amount:,}đ)."

    final_desc = (combo_in.description or "").strip() or auto_desc

    combo_dish = Dish(
        category_id=combo_in.category_id,
        name=combo_in.name.strip(),
        description=final_desc,
        price=combo_in.price,
        image_url=combo_in.image_url,
        status="AVAILABLE",
        is_available=True,
        is_active=True,
        is_featured=combo_in.is_featured,
        is_combo=True,
        combo_items_json=json.dumps(comp_snapshots, ensure_ascii=False),
    )
    db.add(combo_dish)
    db.commit()
    db.refresh(combo_dish)
    return enrich_dishes_list(db, [combo_dish])[0]


@router.post("/dishes/{dish_id}/options", response_model=DishOptionOut, status_code=status.HTTP_201_CREATED)
def admin_add_dish_option(
    dish_id: int,
    opt_in: DishOptionCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Thêm tuỳ chọn (Size / Topping) cho món ăn (T3D1FB5)."""
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "DISH_NOT_FOUND", "message": "Không tìm thấy món ăn", "details": {}},
        )
    opt = DishOption(
        dish_id=dish_id,
        option_group=opt_in.option_group.strip() or "Topping",
        option_name=opt_in.option_name.strip(),
        extra_price=opt_in.extra_price,
        is_required=opt_in.is_required,
        max_select=opt_in.max_select,
        is_active=opt_in.is_active,
    )
    db.add(opt)
    db.commit()
    db.refresh(opt)
    return DishOptionOut.model_validate(opt)


@router.put("/dishes/{dish_id}/options/{option_id}", response_model=DishOptionOut)
def admin_update_dish_option(
    dish_id: int,
    option_id: int,
    opt_in: DishOptionUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Cập nhật tuỳ chọn của món ăn (T3D1FB5)."""
    opt = db.query(DishOption).filter(DishOption.id == option_id, DishOption.dish_id == dish_id).first()
    if not opt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "OPTION_NOT_FOUND", "message": "Không tìm thấy tuỳ chọn", "details": {}},
        )
    for field in ["option_group", "option_name", "extra_price", "is_required", "max_select", "is_active"]:
        val = getattr(opt_in, field)
        if val is not None:
            setattr(opt, field, val.strip() if isinstance(val, str) else val)
    db.commit()
    db.refresh(opt)
    return DishOptionOut.model_validate(opt)


@router.delete("/dishes/{dish_id}/options/{option_id}")
def admin_delete_dish_option(
    dish_id: int,
    option_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Xoá tuỳ chọn của món ăn (T3D1FB5)."""
    opt = db.query(DishOption).filter(DishOption.id == option_id, DishOption.dish_id == dish_id).first()
    if not opt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "OPTION_NOT_FOUND", "message": "Không tìm thấy tuỳ chọn", "details": {}},
        )
    db.delete(opt)
    db.commit()
    return {"deleted": True, "option_id": option_id}


# ----------------- QUẢN LÝ DANH MỤC (FR-10, T3D1F9B) -----------------
@router.get("/categories", response_model=list[CategoryOut])
def admin_get_categories(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Xem danh sách toàn bộ danh mục kể cả danh mục đã ẩn, sắp theo sort_order (FR-10, T3D1F9B)."""
    cats = db.query(Category).order_by(Category.sort_order.asc(), Category.id.asc()).all()
    counts = dict(
        db.query(Dish.category_id, func.count(Dish.id))
        .group_by(Dish.category_id)
        .all()
    )
    result = []
    for c in cats:
        dto = CategoryOut.model_validate(c)
        dto.dish_count = counts.get(c.id, 0)
        result.append(dto)
    return result


@router.post("/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def admin_create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Thêm danh mục mới kèm thứ tự hiển thị (FR-10, T3D1F9B)."""
    name_clean = cat_in.name.strip()
    exists = db.query(Category).filter(Category.name == name_clean).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "CATEGORY_EXISTS", "message": "Tên danh mục đã tồn tại", "details": {}},
        )

    sort_order = cat_in.sort_order
    if sort_order <= 0:
        max_sort = db.query(func.max(Category.sort_order)).scalar() or 0
        sort_order = max_sort + 1

    new_cat = Category(name=name_clean, sort_order=sort_order, is_active=cat_in.is_active)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    dto = CategoryOut.model_validate(new_cat)
    dto.dish_count = 0
    return dto


@router.patch("/categories/reorder", response_model=list[CategoryOut])
def admin_reorder_categories(
    items: list[CategoryReorderItem],
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Sắp xếp lại thứ tự các danh mục (T3D1F9B)."""
    id_map = {item.id: item.sort_order for item in items}
    if id_map:
        cats = db.query(Category).filter(Category.id.in_(list(id_map.keys()))).all()
        for c in cats:
            c.sort_order = id_map[c.id]
        db.commit()
    return admin_get_categories(db=db, current_admin=current_admin)


@router.put("/categories/{cat_id}", response_model=CategoryOut)
def admin_update_category(
    cat_id: int,
    cat_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Sửa tên, thứ tự hoặc ẩn/hiện danh mục (FR-10, T3D1F9B)."""
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CATEGORY_NOT_FOUND", "message": "Không tìm thấy danh mục", "details": {}},
        )

    if cat_in.name is not None:
        name_clean = cat_in.name.strip()
        dup = db.query(Category).filter(Category.name == name_clean, Category.id != cat_id).first()
        if dup:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "CATEGORY_EXISTS", "message": "Tên danh mục này đã tồn tại", "details": {}},
            )
        cat.name = name_clean

    if cat_in.sort_order is not None:
        cat.sort_order = cat_in.sort_order

    if cat_in.is_active is not None:
        cat.is_active = cat_in.is_active

    db.commit()
    db.refresh(cat)
    dto = CategoryOut.model_validate(cat)
    dto.dish_count = db.query(func.count(Dish.id)).filter(Dish.category_id == cat.id).scalar() or 0
    return dto


@router.delete("/categories/{cat_id}")
def admin_delete_category(
    cat_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Xoá danh mục: chặn không cho xoá khi danh mục vẫn còn món ăn (T3D1F9B)."""
    cat = db.query(Category).filter(Category.id == cat_id).first()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CATEGORY_NOT_FOUND", "message": "Không tìm thấy danh mục", "details": {}},
        )

    dish_count = db.query(func.count(Dish.id)).filter(Dish.category_id == cat_id).scalar() or 0
    if dish_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CATEGORY_HAS_DISHES",
                "message": f"Không thể xoá danh mục '{cat.name}' vì đang có {dish_count} món ăn thuộc danh mục này. Vui lòng ẩn danh mục hoặc chuyển món sang danh mục khác.",
                "details": {"dish_count": dish_count},
            },
        )

    db.delete(cat)
    db.commit()
    return {"message": f"Đã xoá danh mục '{cat.name}' thành công"}


# ----------------- QUẢN LÝ ĐƠN HÀNG & XỬ LÝ ĐƠN CHO NHÂN VIÊN (FR-11, FR-12, T3D29D9) -----------------
@router.get("/orders/board")
def admin_get_orders_board(
    search: Optional[str] = Query(None, description="Tìm theo mã đơn hoặc SĐT"),
    date_filter: Optional[str] = Query(None, alias="date", description="YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Bảng đơn hàng theo cột trạng thái (Mới, Đang chuẩn bị, Đang giao) theo thời gian cho nhân viên xử lý (T3D29D9, T3D2A0D)."""
    query = db.query(Order).options(joinedload(Order.items), joinedload(Order.status_histories))
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Order.order_code.ilike(s)) | (Order.phone.ilike(s)) | (Order.customer_name.ilike(s)))
    if date_filter:
        try:
            dt = datetime.strptime(date_filter.strip(), "%Y-%m-%d")
            start_dt = dt.replace(hour=0, minute=0, second=0)
            end_dt = dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Order.created_at >= start_dt, Order.created_at <= end_dt)
        except ValueError:
            pass

    active_orders = (
        query.filter(Order.status.in_(["pending", "confirmed", "preparing", "delivering"]))
        .order_by(Order.created_at.asc())
        .all()
    )

    new_orders = [OrderOut.model_validate(o) for o in active_orders if o.status == "pending"]
    preparing_orders = [OrderOut.model_validate(o) for o in active_orders if o.status in ("confirmed", "preparing")]
    delivering_orders = [OrderOut.model_validate(o) for o in active_orders if o.status == "delivering"]
    latest_pending_id = max((o.id for o in new_orders), default=0)

    return {
        "new_orders": new_orders,
        "preparing_orders": preparing_orders,
        "delivering_orders": delivering_orders,
        "latest_pending_id": latest_pending_id,
        "counts": {
            "new": len(new_orders),
            "preparing": len(preparing_orders),
            "delivering": len(delivering_orders),
        },
    }


@router.get("/orders")
def admin_get_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None, description="Tìm theo mã đơn, SĐT hoặc tên"),
    date_filter: Optional[str] = Query(None, alias="date", description="Lọc theo ngày YYYY-MM-DD"),
    date_from: Optional[str] = Query(None, description="Từ ngày YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="Đến ngày YYYY-MM-DD"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Xem danh sách đơn hàng có lọc theo ngày/trạng thái, tìm theo mã/SĐT và phân trang (FR-11, T3D29D9)."""
    query = db.query(Order).options(joinedload(Order.items), joinedload(Order.status_histories))

    if status_filter:
        query = query.filter(Order.status == status_filter.strip())

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Order.order_code.ilike(s)) | (Order.phone.ilike(s)) | (Order.customer_name.ilike(s)))

    if date_filter:
        try:
            dt = datetime.strptime(date_filter.strip(), "%Y-%m-%d")
            query = query.filter(
                Order.created_at >= dt.replace(hour=0, minute=0, second=0),
                Order.created_at <= dt.replace(hour=23, minute=59, second=59),
            )
        except ValueError:
            pass

    if date_from:
        try:
            dt_from = datetime.strptime(date_from.strip(), "%Y-%m-%d").replace(hour=0, minute=0, second=0)
            query = query.filter(Order.created_at >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.strptime(date_to.strip(), "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(Order.created_at <= dt_to)
        except ValueError:
            pass

    total = query.count()
    orders = query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [OrderOut.model_validate(o) for o in orders],
    }


@router.get("/orders/{order_id}", response_model=OrderOut)
def admin_get_order_detail(
    order_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Xem chi tiết đơn hàng (FR-11)."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .options(joinedload(Order.items), joinedload(Order.status_histories))
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORDER_NOT_FOUND", "message": "Không tìm thấy đơn hàng", "details": {}},
        )
    return OrderOut.model_validate(order)


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
def admin_update_order_status(
    order_id: int,
    update_in: OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Cập nhật trạng thái đơn hàng theo đúng quy trình 4.1 (FR-12, BR-08, BR-09, BR-11, TC-21, TC-22, TC-34, TC-35)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORDER_NOT_FOUND", "message": "Không tìm thấy đơn hàng", "details": {}},
        )

    # Kiểm tra Optimistic Locking / Xung đột thao tác (TC-35)
    if update_in.expected_current_status and update_in.expected_current_status != order.status:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "STATUS_CONFLICT",
                "message": f"Đơn hàng đã được người khác chuyển sang '{order.status}'. Vui lòng tải lại dữ liệu.",
                "details": {"current_status": order.status},
            },
        )

    # Kiểm tra trạng thái kết thúc (BR-11, TC-22)
    if order.status in ["completed", "cancelled"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "TERMINAL_STATE",
                "message": f"Đơn hàng đã ở trạng thái '{order.status}', không thể thay đổi thêm",
                "details": {},
            },
        )

    # Kiểm tra tính hợp lệ của bước chuyển trạng thái (4.1, TC-34)
    allowed_next_states = VALID_TRANSITIONS.get(order.status, [])
    if update_in.status not in allowed_next_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_TRANSITION",
                "message": f"Không thể chuyển trạng thái từ '{order.status}' sang '{update_in.status}'. Các trạng thái tiếp theo hợp lệ: {allowed_next_states}",
                "details": {"allowed_next_states": allowed_next_states},
            },
        )

    old_status = order.status
    order.status = update_in.status

    # Ghi nhận lịch sử trạng thái
    history = OrderStatusHistory(
        order_id=order.id,
        changed_by=current_admin.id,
        old_status=old_status,
        new_status=update_in.status,
        note=update_in.note or f"Admin cập nhật từ {old_status} sang {update_in.status}",
    )
    db.add(history)

    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(order)


@router.post("/orders/{order_id}/cancel", response_model=OrderOut)
def admin_cancel_order_with_reason(
    order_id: int,
    cancel_in: OrderCancelRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Nhân viên/Admin huỷ đơn trước trạng thái 'Đang giao' (delivering) kèm lý do bắt buộc và ghi lịch sử (T3D2909)."""
    order = (
        db.query(Order)
        .filter(Order.id == order_id)
        .options(joinedload(Order.items), joinedload(Order.status_histories))
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORDER_NOT_FOUND", "message": "Không tìm thấy đơn hàng", "details": {}},
        )

    reason = (cancel_in.reason or "").strip()
    if not reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CANCEL_REASON_REQUIRED",
                "message": "Nhân viên huỷ đơn bắt buộc phải nhập lý do (VD: Hết món, khách đổi ý...)",
                "details": {},
            },
        )

    if order.status not in ["pending", "confirmed", "preparing"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CANNOT_CANCEL_AT_STAGE",
                "message": f"Không thể huỷ đơn khi đơn đã ở trạng thái '{order.status}'. Nhân viên chỉ được huỷ trước khi đơn chuyển sang 'Đang giao'.",
                "details": {"current_status": order.status},
            },
        )

    old_st = order.status
    order.status = "cancelled"

    if order.voucher_id:
        voucher = db.query(Voucher).filter(Voucher.id == order.voucher_id).first()
        if voucher and (voucher.used_count or 0) > 0:
            voucher.used_count -= 1

    history = OrderStatusHistory(
        order_id=order.id,
        changed_by=current_admin.id,
        old_status=old_st,
        new_status="cancelled",
        note=f"Nhân viên huỷ đơn: {reason}",
    )
    db.add(history)
    db.commit()
    db.refresh(order)
    return OrderOut.model_validate(order)
