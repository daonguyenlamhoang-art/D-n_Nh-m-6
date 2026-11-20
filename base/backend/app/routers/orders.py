"""Router Đơn hàng & Tra cứu đơn cho khách hàng (FR-06, FR-07, BR-01..18, TC-09..13, TC-23..24, TC-27..31, TC-33, TC-39)."""
import json
import random
import re
import time
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy.orm import Session, joinedload

from app.core.auth import calculate_shipping_fee
from app.core.config import settings
from app.core.rate_limit import check_order_lookup_rate_limit, record_order_lookup_failure
from app.db.session import get_db
from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.dish import Dish, DishOption
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.voucher import Voucher
from app.routers.store import check_is_store_open
from app.routers.vouchers import evaluate_voucher
from app.schemas.order import (
    OrderCancelRequest,
    OrderCreate,
    OrderItemOut,
    OrderLookupOut,
    OrderLookupRequest,
    OrderStatusHistoryOut,
)

router = APIRouter(prefix="/orders", tags=["Orders"])

# Bộ nhớ chống bấm đặt món 2 lần liên tiếp (Double-submit protection - T3D286D)
_recent_order_locks: dict[str, float] = {}


def validate_desired_delivery_time(desired_time: Optional[str]) -> None:
    """Kiểm tra giờ giao mong muốn phải nằm trong khung giờ mở cửa (18:00 - 02:00) (T3D286D)."""
    if not desired_time:
        return
    clean = desired_time.strip()
    if not clean or clean.lower() in ("ngay", "giao ngay", "immediate", "asap"):
        return

    match = re.search(r"(\d{1,2}):(\d{2})", clean)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        if hour > 23 or minute > 59:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_DELIVERY_TIME", "message": "Định dạng giờ giao không hợp lệ", "details": {}},
            )
        in_open_window = (
            hour >= settings.STORE_OPEN_HOUR
            or hour < settings.STORE_CLOSE_HOUR
            or (hour == settings.STORE_CLOSE_HOUR and minute == 0)
        )
        if not in_open_window:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "code": "DELIVERY_TIME_OUTSIDE_HOURS",
                    "message": f"Giờ giao mong muốn ({clean}) nằm ngoài khung giờ mở cửa của quán (18:00 - 02:00).",
                    "details": {"open_hour": settings.STORE_OPEN_HOUR, "close_hour": settings.STORE_CLOSE_HOUR},
                },
            )

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
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db),
):
    """Đặt hàng trực tuyến trong 1 transaction: kiểm tra món còn bán, lưu snapshot giá & tuỳ chọn, xoá giỏ, chống bấm 2 lần (T3D286D)."""
    # 1. Kiểm tra giờ mở cửa (FR-14, TC-39) và giờ giao mong muốn (T3D286D)
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

    validate_desired_delivery_time(order_in.desired_delivery_time)

    # 2. Kiểm tra danh sách món không được rỗng
    if not order_in.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "EMPTY_CART", "message": "Giỏ hàng không có sản phẩm nào", "details": {}},
        )

    # 2b. Chống bấm đặt hàng 2 lần liên tiếp (Idempotency Key)
    if x_idempotency_key:
        now_ts = time.time()
        last_ts = _recent_order_locks.get(x_idempotency_key)
        if last_ts and (now_ts - last_ts) < 30.0:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "DUPLICATE_ORDER_SUBMISSION",
                    "message": "Đơn hàng đang được xử lý, vui lòng không bấm đặt món 2 lần.",
                    "details": {},
                },
            )
        _recent_order_locks[x_idempotency_key] = now_ts

    # 3. Gom và kiểm tra các món
    line_signatures = []
    for item in order_in.items:
        opt_tuple = tuple(sorted(item.selected_option_ids or ([item.dish_option_id] if item.dish_option_id else [])))
        note_norm = (item.note or "").strip()
        line_signatures.append((item.dish_id, opt_tuple, note_norm))

    if len(line_signatures) != len(set(line_signatures)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "DUPLICATE_ITEMS", "message": "Giỏ hàng có dòng món bị lặp lại, vui lòng kiểm tra lại", "details": {}},
        )

    dish_ids = list({item.dish_id for item in order_in.items})
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
        if not dish.is_active or not dish.category.is_active or dish.status == "HIDDEN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DISH_INACTIVE", "message": f"Món '{dish.name}' đã ngừng kinh doanh hoặc danh mục bị ẩn", "details": {}},
            )

        if not dish.is_available or dish.status == "OUT_OF_STOCK":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "DISH_OUT_OF_STOCK", "message": f"Món '{dish.name}' hiện đã hết hàng", "details": {}},
            )

        # Tính đơn giá thực tế từ DB (cộng tất cả tuỳ chọn đã chọn)
        unit_price = dish.price
        opt_ids = sorted(set(item.selected_option_ids or ([item.dish_option_id] if item.dish_option_id else [])))
        opt_names = []
        opt_snapshots = []

        for oid in opt_ids:
            opt = next((o for o in dish.options if o.id == oid and o.is_active), None)
            if opt:
                unit_price += opt.extra_price
                opt_names.append(opt.option_name)
                opt_snapshots.append({"id": opt.id, "group": opt.option_group, "name": opt.option_name, "extra_price": opt.extra_price})

        option_name = ", ".join(opt_names) if opt_names else None
        primary_opt_id = opt_ids[0] if opt_ids else None
        item_subtotal = unit_price * item.quantity
        calculated_total += item_subtotal

        items_to_save.append({
            "dish_id": dish.id,
            "dish_option_id": primary_opt_id,
            "dish_name": dish.name,
            "option_name": option_name,
            "options_json": json.dumps(opt_snapshots, ensure_ascii=False) if opt_snapshots else None,
            "note": (item.note or "").strip() or None,
            "quantity": item.quantity,
            "unit_price": unit_price,
            "subtotal": item_subtotal,
        })

        price_check_items.append({
            "dish_id": dish.id,
            "unit_price": unit_price,
            "quantity": item.quantity,
        })

    # 4. Kiểm tra mã giảm giá và phí ship theo khu vực
    shipping_fee = calculate_shipping_fee(order_in.area)
    applied_voucher = None
    discount_amount = 0
    if order_in.voucher_code:
        applied_voucher, discount_amount, v_msg = evaluate_voucher(db, order_in.voucher_code, calculated_total)
        if not applied_voucher:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_VOUCHER", "message": v_msg, "details": {}},
            )

    final_total = max(0, calculated_total + shipping_fee - discount_amount)

    # 4b. Kiểm tra giá thay đổi lúc đặt hàng (BR-05, BR-17, TC-29)
    if order_in.expected_total is not None and order_in.expected_total not in (
        calculated_total,
        calculated_total - discount_amount,
        final_total,
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "PRICE_CHANGED",
                "message": "Giá một số món đã thay đổi, vui lòng kiểm tra lại",
                "details": {
                    "total_amount": final_total,
                    "items": price_check_items,
                },
            },
        )

    # 5. Lưu đơn + chi tiết + trừ voucher + xoá giỏ trong 1 transaction cơ sở dữ liệu (T3D286D)
    try:
        order_code = generate_unique_order_code(db)
        guest_tok = (order_in.guest_token or x_guest_token or "").strip() or None
        new_order = Order(
            order_code=order_code,
            guest_token=guest_tok,
            voucher_id=applied_voucher.id if applied_voucher else None,
            customer_name=order_in.customer_name,
            phone=order_in.phone,
            customer_email=order_in.customer_email,
            address=order_in.address,
            area=order_in.area or "Nội thành",
            note=order_in.note,
            desired_delivery_time=order_in.desired_delivery_time or "Giao ngay",
            subtotal=calculated_total,
            shipping_fee=shipping_fee,
            discount_amount=discount_amount,
            total_amount=final_total,
            payment_method=order_in.payment_method or "COD",
            status="pending",
        )
        db.add(new_order)
        if applied_voucher:
            applied_voucher.used_count = (applied_voucher.used_count or 0) + 1
        db.flush()  # Sinh ID đơn

        for it in items_to_save:
            order_item = OrderItem(
                order_id=new_order.id,
                dish_id=it["dish_id"],
                dish_option_id=it["dish_option_id"],
                dish_name=it["dish_name"],
                option_name=it["option_name"],
                options_json=it["options_json"],
                note=it["note"],
                quantity=it["quantity"],
                unit_price=it["unit_price"],
                subtotal=it["subtotal"],
            )
            db.add(order_item)

        # Lưu lịch sử trạng thái ban đầu: Chờ xác nhận (pending)
        history = OrderStatusHistory(
            order_id=new_order.id,
            old_status=None,
            new_status="pending",
            note=f"Khách đặt hàng trực tuyến ({new_order.payment_method})",
        )
        db.add(history)

        # Xoá giỏ hàng DB của khách trong cùng 1 transaction (T3D286D)
        if guest_tok:
            active_carts = db.query(Cart).filter(Cart.guest_token == guest_tok, Cart.status == "active").all()
            for c in active_carts:
                db.query(CartItem).filter(CartItem.cart_id == c.id).delete()
                c.status = "checked_out"

        db.commit()
        db.refresh(new_order)

        return {
            "id": new_order.id,
            "order_code": new_order.order_code,
            "subtotal": new_order.subtotal,
            "shipping_fee": new_order.shipping_fee,
            "discount_amount": new_order.discount_amount,
            "total_amount": new_order.total_amount,
            "payment_method": new_order.payment_method,
            "desired_delivery_time": new_order.desired_delivery_time,
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


@router.post("/{order_code}/cancel", response_model=OrderLookupOut)
def customer_cancel_order(
    order_code: str,
    cancel_in: OrderCancelRequest,
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Khách hàng huỷ đơn: chỉ cho phép khi đơn còn ở trạng thái 'Chờ xác nhận' (pending) và ghi lịch sử (T3D2909)."""
    code_clean = order_code.strip().upper()
    eff_token = (cancel_in.guest_token or x_guest_token or "").strip()
    eff_phone = (cancel_in.phone or "").strip()

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
            detail={"code": "FORBIDDEN_ORDER", "message": "Bạn chỉ có thể huỷ đơn hàng của chính mình", "details": {}},
        )

    if order.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CANNOT_CANCEL_ORDER",
                "message": f"Không thể huỷ đơn hàng ở trạng thái '{STATUS_MAP.get(order.status, order.status)}'. Khách chỉ được huỷ khi đơn còn 'Chờ xác nhận'.",
                "details": {"current_status": order.status},
            },
        )

    old_st = order.status
    order.status = "cancelled"
    reason_text = (cancel_in.reason or "Khách yêu cầu huỷ đơn").strip()

    if order.voucher_id:
        voucher = db.query(Voucher).filter(Voucher.id == order.voucher_id).first()
        if voucher and (voucher.used_count or 0) > 0:
            voucher.used_count -= 1

    history = OrderStatusHistory(
        order_id=order.id,
        changed_by=None,
        old_status=old_st,
        new_status="cancelled",
        note=f"Khách huỷ đơn: {reason_text}",
    )
    db.add(history)
    db.commit()
    db.refresh(order)
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


@router.post("/{order_code}/reorder")
def reorder_from_past_order(
    order_code: str,
    db: Session = Depends(get_db),
):
    """Lấy danh sách món còn bán từ đơn cũ để khách bấm 'Đặt lại' thêm nhanh vào giỏ (T3D2587)."""
    code_clean = order_code.strip().upper()
    order = (
        db.query(Order)
        .filter(Order.order_code == code_clean)
        .options(joinedload(Order.items))
        .first()
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORDER_NOT_FOUND", "message": "Không tìm thấy đơn hàng cũ", "details": {}},
        )

    dish_ids = [it.dish_id for it in order.items]
    dishes = db.query(Dish).filter(Dish.id.in_(dish_ids), Dish.is_active == True, Dish.is_available == True).all()
    avail_ids = {d.id for d in dishes}

    reorder_items = []
    skipped_items = []
    for it in order.items:
        if it.dish_id in avail_ids:
            reorder_items.append({
                "dish_id": it.dish_id,
                "dish_name": it.dish_name,
                "quantity": it.quantity,
                "dish_option_id": it.dish_option_id,
                "option_name": it.option_name,
                "note": it.note,
            })
        else:
            skipped_items.append(it.dish_name)

    return {
        "order_code": order.order_code,
        "items": reorder_items,
        "skipped_items": skipped_items,
        "message": "Đã chuẩn bị danh sách món để đặt lại",
    }


@router.get("/{order_code}/vietqr")
def get_order_vietqr_info(order_code: str, db: Session = Depends(get_db)):
    """Thông tin mã QR VietQR theo tổng tiền và nội dung = mã đơn (T3D2F61)."""
    code_clean = order_code.strip().upper()
    order = db.query(Order).filter(Order.order_code == code_clean).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "ORDER_NOT_FOUND", "message": "Không tìm thấy đơn hàng", "details": {}},
        )
    qr_url = (
        f"https://img.vietqr.io/image/MB-0988888999-compact2.png"
        f"?amount={order.total_amount}&addInfo={order.order_code}&accountName=NIGHTFOOD%20HA%20NOI"
    )
    return {
        "order_code": order.order_code,
        "total_amount": order.total_amount,
        "payment_method": order.payment_method,
        "payment_confirmed": bool(order.payment_confirmed),
        "status": order.status,
        "bank_id": "MB",
        "account_no": "0988888999",
        "account_name": "NIGHTFOOD HA NOI",
        "transfer_memo": order.order_code,
        "qr_image_url": qr_url,
    }
