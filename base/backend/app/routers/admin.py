"""Router Quản trị viên (Admin) (FR-08..12, FR-15, BR-08..11, TC-14..22, TC-32, TC-34..35)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
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
from app.models.dish import Dish
from app.models.order import Order, OrderStatusHistory
from app.models.user import User
from app.schemas.admin import AdminLoginRequest, AdminUserOut, DashboardStatsOut
from app.schemas.category import CategoryCreate, CategoryOut, CategoryReorderItem, CategoryUpdate
from app.schemas.dish import DishCreate, DishOut, DishUpdate
from app.schemas.order import OrderOut, OrderStatusUpdate

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


# ----------------- QUẢN LÝ MÓN ĂN (FR-09) -----------------
@router.get("/dishes")
def admin_get_dishes(
    search: Optional[str] = Query(None, max_length=100),
    category_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Xem toàn bộ món ăn (kể cả món đã ẩn) kèm phân trang và tìm kiếm (FR-09)."""
    query = db.query(Dish).options(joinedload(Dish.category), joinedload(Dish.options))

    if category_id:
        query = query.filter(Dish.category_id == category_id)

    if search:
        clean = search.strip()
        if clean:
            query = query.filter(Dish.name.ilike(f"%{clean}%"))

    total = query.count()
    dishes = query.order_by(Dish.id.desc()).offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for d in dishes:
        dto = DishOut.model_validate(d)
        dto.category_name = d.category.name if d.category else None
        items.append(dto)

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.post("/dishes", response_model=DishOut, status_code=status.HTTP_201_CREATED)
def admin_create_dish(
    dish_in: DishCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Thêm món ăn mới vào thực đơn (FR-09, TC-17, TC-18)."""
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
        is_available=dish_in.is_available,
        is_active=dish_in.is_active,
    )
    db.add(new_dish)
    db.commit()
    db.refresh(new_dish)

    dto = DishOut.model_validate(new_dish)
    dto.category_name = cat.name
    return dto


@router.put("/dishes/{dish_id}", response_model=DishOut)
def admin_update_dish(
    dish_id: int,
    dish_in: DishUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Cập nhật thông tin món ăn hoặc ẩn món (soft delete) (FR-09, TC-19)."""
    dish = db.query(Dish).filter(Dish.id == dish_id).first()
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
    if dish_in.is_available is not None:
        dish.is_available = dish_in.is_available
    if dish_in.is_active is not None:
        dish.is_active = dish_in.is_active

    db.commit()
    db.refresh(dish)

    dto = DishOut.model_validate(dish)
    dto.category_name = dish.category.name if dish.category else None
    return dto


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


# ----------------- QUẢN LÝ ĐƠN HÀNG (FR-11, FR-12) -----------------
@router.get("/orders")
def admin_get_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None, description="Tìm theo mã đơn, SĐT hoặc tên"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    """Xem danh sách đơn hàng có lọc trạng thái và phân trang (FR-11, TC-20)."""
    query = db.query(Order).options(joinedload(Order.items), joinedload(Order.status_histories))

    if status_filter:
        query = query.filter(Order.status == status_filter.strip())

    if search:
        s = f"%{search.strip()}%"
        query = query.filter((Order.order_code.ilike(s)) | (Order.phone.ilike(s)) | (Order.customer_name.ilike(s)))

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
