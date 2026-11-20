"""Router Đơn hàng & Tra cứu đơn cho khách hàng (FR-06, FR-07, BR-01..18, TC-09..13, TC-23..24, TC-27..31, TC-33, TC-39)."""
import random
import time
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.rate_limit import check_order_lookup_rate_limit, record_order_lookup_failure
from app.db.session import get_db
from app.models.category import Category
from app.models.dish import Dish, DishOption
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.routers.store import check_is_store_open
from app.schemas.order import (
    OrderCreate,
    OrderItemOut,
    OrderLookupOut,
    OrderLookupRequest,
    OrderStatusHistoryOut,
)

router = APIRouter(prefix="/orders", tags=["Orders"])

STATUS_MAP = {
    "pending": "Chờ xác nhận",
    "confirmed": "Đã xác nhận",
    "preparing": "Đang chuẩn bị",
    "delivering": "Đang giao",
    "completed": "Hoàn thành",
    "cancelled": "Đã hủy",
}


def mask_address(addr: str) -> str:
    """Ẩn bớt thông tin chi tiết địa chỉ khi tra cứu để bảo vệ riêng tư (3.7)."""
    parts = addr.split(",")
    if len(parts) > 1:
        return f"*** {parts[-1].strip()}"
    return "*** (Địa chỉ đã được bảo mật)"


def generate_unique_order_code(db: Session) -> str:
    """Sinh mã đơn duy nhất định dạng NF + 6 số ngẫu nhiên."""
    for _ in range(10):
        code = f"NF{random.randint(100000, 999999)}"
        exists = db.query(Order.id).filter(Order.order_code == code).first()
        if not exists:
            return code
    # Fallback timestamp
    return f"NF{int(time.time()) % 1000000:06d}"


@router.post("", status_code=status.HTTP_201_CREATED)
def create_order(
    order_in: OrderCreate,
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Đặt hàng trực tuyến (FR-06, BR-01..07, BR-14, BR-17)."""
    # 1. Kiểm tra giờ mở cửa (FR-14, TC-39)
    is_open, status_text, _ = check_is_store_open()
    if not is_open:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "STORE_CLOSED",
                "message": f"Quán hiện đang đóng cửa ({status_text}). Quý khách vui lòng đặt hàng trong khung giờ 18:00 - 02:00.",
                "details": {},
            },
        )

    # 2. Kiểm tra danh sách món không được rỗng
    if not order_in.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_CART", "message": "Giỏ hàng không có sản phẩm nào", "details": {}},
        )

    # 3. Gom và kiểm tra các món
    dish_ids = [item.dish_id for item in order_in.items]
    if len(dish_ids) != len(set(dish_ids)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DUPLICATE_ITEMS", "message": "Giỏ hàng có món bị lặp lại, vui lòng kiểm tra lại", "details": {}},
        )

    dishes_db = (
        db.query(Dish)
        .join(Category, Dish.category_id == Category.id)
        .filter(Dish.id.in_(dish_ids))
        .options(joinedload(Dish.category), joinedload(Dish.options))
        .all()
    )
    dish_map = {d.id: d for d in dishes_db}

    items_to_save = []
    price_check_items = []
    calculated_total = 0

    for item in order_in.items:
        if item.quantity < 1 or item.quantity > 99:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_QUANTITY", "message": f"Số lượng món phải từ 1 đến 99 (nhận: {item.quantity})", "details": {}},
            )

        dish = dish_map.get(item.dish_id)
        if not dish:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DISH_NOT_FOUND", "message": f"Món ăn có mã ID={item.dish_id} không tồn tại", "details": {}},
            )

        # Kiểm tra trạng thái món và danh mục (BR-06, BR-16, TC-12, TC-30)
        if not dish.is_active or not dish.category.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DISH_INACTIVE", "message": f"Món '{dish.name}' đã ngừng kinh doanh hoặc danh mục bị ẩn", "details": {}},
            )

        if not dish.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DISH_OUT_OF_STOCK", "message": f"Món '{dish.name}' hiện đã hết hàng", "details": {}},
            )

        # Tính đơn giá thực tế từ DB
        unit_price = dish.price
        option_name = None

        if item.dish_option_id:
            opt = next((o for o in dish.options if o.id == item.dish_option_id and o.is_active), None)
            if opt:
                unit_price += opt.extra_price
                option_name = opt.option_name

        item_subtotal = unit_price * item.quantity
        calculated_total += item_subtotal

        items_to_save.append({
            "dish_id": dish.id,
            "dish_option_id": item.dish_option_id,
            "dish_name": dish.name,
            "option_name": option_name,
            "quantity": item.quantity,
            "unit_price": unit_price,
            "subtotal": item_subtotal,
        })

        price_check_items.append({
            "dish_id": dish.id,
            "unit_price": unit_price,
            "quantity": item.quantity,
        })

    # 4. Kiểm tra giá thay đổi lúc đặt hàng (BR-05, BR-17, TC-29)
    if order_in.expected_total is not None and order_in.expected_total != calculated_total:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PRICE_CHANGED",
                "message": "Giá một số món đã thay đổi, vui lòng kiểm tra lại",
                "details": {
                    "total_amount": calculated_total,
                    "items": price_check_items,
                },
            },
        )

    # 5. Lưu đơn trong transaction cơ sở dữ liệu (BR-14, TC-09, TC-26)
    try:
        order_code = generate_unique_order_code(db)
        guest_tok = order_in.guest_token or x_guest_token
        new_order = Order(
            order_code=order_code,
            guest_token=guest_tok,
            customer_name=order_in.customer_name,
            phone=order_in.phone,
            customer_email=order_in.customer_email,
            address=order_in.address,
            area=order_in.area or "Nội thành",
            note=order_in.note,
            desired_delivery_time=order_in.desired_delivery_time,
            subtotal=calculated_total,
            shipping_fee=0,
            discount_amount=0,
            total_amount=calculated_total,
            payment_method=order_in.payment_method or "COD",
            status="pending",
        )
        db.add(new_order)
        db.flush()  # Sinh ID đơn

        for it in items_to_save:
            order_item = OrderItem(
                order_id=new_order.id,
                dish_id=it["dish_id"],
                dish_option_id=it["dish_option_id"],
                dish_name=it["dish_name"],
                option_name=it["option_name"],
                quantity=it["quantity"],
                unit_price=it["unit_price"],
                subtotal=it["subtotal"],
            )
            db.add(order_item)

        # Lưu lịch sử trạng thái ban đầu
        history = OrderStatusHistory(
            order_id=new_order.id,
            old_status=None,
            new_status="pending",
            note="Khách đặt hàng trực tuyến (COD)",
        )
        db.add(history)

        db.commit()
        db.refresh(new_order)

        return {
            "order_code": new_order.order_code,
            "total_amount": new_order.total_amount,
            "payment_method": "COD",
            "status": "pending",
            "message": "Đặt hàng thành công",
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "DB_ERROR", "message": f"Không thể hoàn tất đặt hàng: {str(e)}", "details": {}},
        )


def _build_order_lookup_out(order: Order) -> OrderLookupOut:
    histories = sorted(order.status_histories or [], key=lambda h: h.changed_at or order.created_at)
    return OrderLookupOut(
        id=order.id,
        order_code=order.order_code,
        status=order.status,
        status_display=STATUS_MAP.get(order.status, order.status),
        created_at=order.created_at,
        subtotal=order.subtotal,
        shipping_fee=order.shipping_fee or 0,
        discount_amount=order.discount_amount or 0,
        total_amount=order.total_amount,
        payment_method=order.payment_method,
        payment_confirmed=bool(order.payment_confirmed),
        desired_delivery_time=order.desired_delivery_time,
        area=order.area,
        customer_name=order.customer_name,
        masked_address=mask_address(order.address),
        items=[OrderItemOut.model_validate(it) for it in order.items],
        status_histories=[OrderStatusHistoryOut.model_validate(h) for h in histories],
    )


@router.get("/my", response_model=list[OrderLookupOut])
def get_my_orders(
    status_filter: Optional[str] = Query(None, alias="status"),
    phone: Optional[str] = Query(None, description="Số điện thoại của khách"),
    guest_token: Optional[str] = Query(None, description="Guest token định danh khách"),
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Khách xem danh sách đơn của mình theo trạng thái kèm món, tuỳ chọn và lịch sử trạng thái (T3D28EF)."""
    eff_token = (guest_token or x_guest_token or "").strip()
    eff_phone = (phone or "").strip()

    if not eff_token and not eff_phone:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "OWNER_REQUIRED",
                "message": "Vui lòng cung cấp số điện thoại hoặc phiên khách hàng để xem đơn của bạn",
                "details": {},
            },
        )

    query = db.query(Order).options(joinedload(Order.items), joinedload(Order.status_histories))
    if eff_token and eff_phone:
        query = query.filter((Order.guest_token == eff_token) | (Order.phone == eff_phone))
    elif eff_token:
        query = query.filter(Order.guest_token == eff_token)
    else:
        query = query.filter(Order.phone == eff_phone)

    if status_filter:
        query = query.filter(Order.status == status_filter.strip())

    orders = query.order_by(Order.created_at.desc()).limit(50).all()
    return [_build_order_lookup_out(o) for o in orders]


@router.get("/{order_code}/track", response_model=OrderLookupOut)
def track_my_order(
    order_code: str,
    phone: Optional[str] = Query(None),
    guest_token: Optional[str] = Query(None),
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Theo dõi chi tiết 1 đơn hàng của khách kèm dòng thời gian trạng thái; chỉ xem đơn của mình (T3D28EF)."""
    eff_token = (guest_token or x_guest_token or "").strip()
    eff_phone = (phone or "").strip()
    code_clean = order_code.strip().upper()

    order = (
        db.query(Order)
        .filter(Order.order_code == code_clean)
        .options(joinedload(Order.items), joinedload(Order.status_histories))
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
            detail={"code": "FORBIDDEN_ORDER", "message": "Bạn chỉ có quyền xem đơn hàng của chính mình", "details": {}},
        )

    return _build_order_lookup_out(order)


@router.post("/lookup", response_model=OrderLookupOut)
def lookup_order(
    lookup_in: OrderLookupRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Tra cứu đơn hàng bằng Mã đơn + Số điện thoại (FR-07, BR-12, TC-23, TC-24, TC-33, T3D28EF)."""
    client_ip = request.client.host if request.client else "unknown"

    # Kiểm tra giới hạn số lần thử tra cứu (TC-33)
    is_allowed, remaining_sec = check_order_lookup_rate_limit(client_ip)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "TOO_MANY_REQUESTS",
                "message": f"Bạn đã thử tra cứu sai quá số lần cho phép. Vui lòng chờ {remaining_sec} giây trước khi thử lại.",
                "details": {"retry_after_seconds": remaining_sec},
            },
        )

    # Đối chiếu đồng thời cả mã đơn và số điện thoại trong 1 câu lệnh SQL tham số hóa
    order = (
        db.query(Order)
        .filter(Order.order_code == lookup_in.order_code, Order.phone == lookup_in.phone)
        .options(joinedload(Order.items), joinedload(Order.status_histories))
        .first()
    )

    if not order:
        record_order_lookup_failure(client_ip)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "ORDER_NOT_FOUND",
                "message": "Không tìm thấy đơn hàng phù hợp",
                "details": {},
            },
        )

    return _build_order_lookup_out(order)
