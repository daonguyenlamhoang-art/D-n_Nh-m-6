"""Router Giỏ hàng (Cart & CartItem): Thêm, sửa, xoá giỏ hàng trên MySQL (T3D25F6)."""
import json
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.core.auth import SHIPPING_AREA_FEES, calculate_shipping_fee
from app.db.session import get_db
from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.dish import Dish, DishOption
from app.routers.vouchers import evaluate_voucher
from app.schemas.cart import (
    CartCalculationOut,
    CartItemCreate,
    CartItemOut,
    CartItemUpdate,
    CartPreviewRequest,
)

router = APIRouter(prefix="/cart", tags=["Cart"])


def _resolve_guest_token(guest_token: Optional[str], x_guest_token: Optional[str]) -> str:
    tok = (guest_token or x_guest_token or "").strip()
    if not tok:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "CART_TOKEN_REQUIRED",
                "message": "Vui lòng cung cấp X-Guest-Token hoặc guest_token để thao tác trên giỏ hàng của bạn",
                "details": {},
            },
        )
    return tok


def _get_or_create_active_cart(db: Session, tok: str) -> Cart:
    cart = (
        db.query(Cart)
        .filter(Cart.guest_token == tok, Cart.status == "active")
        .options(joinedload(Cart.items))
        .first()
    )
    if not cart:
        cart = db.query(Cart).filter(Cart.guest_token == tok).first()
        if cart:
            cart.status = "active"
            db.commit()
            db.refresh(cart)
        else:
            cart = Cart(guest_token=tok, status="active")
            db.add(cart)
            db.commit()
            db.refresh(cart)
    return cart


def _normalize_options(dish_option_id: Optional[int], selected_option_ids: Optional[list[int]]) -> tuple[Optional[int], str]:
    ids: list[int] = []
    if selected_option_ids:
        ids = sorted({int(x) for x in selected_option_ids if x})
    elif dish_option_id:
        ids = [int(dish_option_id)]
    primary = ids[0] if ids else None
    return primary, json.dumps(ids)


def _build_cart_item_out(ci: CartItem, dish: Optional[Dish]) -> CartItemOut:
    base_price = dish.price if dish else 0
    extra_price = 0
    opt_names: list[str] = []

    if dish and dish.options:
        opt_ids: list[int] = []
        if ci.selected_options_json:
            try:
                opt_ids = [int(x) for x in json.loads(ci.selected_options_json)]
            except Exception:
                opt_ids = []
        if not opt_ids and ci.dish_option_id:
            opt_ids = [ci.dish_option_id]

        for opt in dish.options:
            if opt.id in opt_ids and opt.is_active:
                extra_price += opt.extra_price
                opt_names.append(opt.option_name)

    unit_price = base_price + extra_price
    is_active = bool(dish and dish.is_active and (dish.category.is_active if dish.category else True) and dish.status != "HIDDEN")
    is_available = bool(is_active and dish and dish.is_available and dish.status != "OUT_OF_STOCK")

    return CartItemOut(
        id=ci.id,
        cart_id=ci.cart_id,
        dish_id=ci.dish_id,
        dish_name=dish.name if dish else f"Món #{ci.dish_id}",
        image_url=dish.image_url if dish else None,
        dish_option_id=ci.dish_option_id,
        option_name=", ".join(opt_names) if opt_names else None,
        selected_options_json=ci.selected_options_json,
        note=ci.note,
        quantity=ci.quantity,
        base_price=base_price,
        option_extra_price=extra_price,
        unit_price=unit_price,
        line_total=unit_price * ci.quantity,
        is_available=is_available,
        is_active=is_active,
    )


@router.get("/shipping-areas")
def get_shipping_areas():
    """Danh sách khu vực giao hàng và phí ship tương ứng (T3D262C)."""
    return [{"area": k, "shipping_fee": v} for k, v in SHIPPING_AREA_FEES.items()]


@router.get("", response_model=CartCalculationOut)
def get_my_cart_and_calculate(
    area: Optional[str] = Query("Nội thành"),
    voucher_code: Optional[str] = Query(None),
    expected_subtotal: Optional[int] = Query(None),
    guest_token: Optional[str] = Query(None),
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """API xem giỏ hàng và tính tiền tại server (T3D262C):
    - Thành tiền từng dòng (giá món + tuỳ chọn) * số lượng.
    - Tạm tính (subtotal), phí ship theo khu vực (module Tài khoản), giảm giá (module Khuyến mãi), tổng tiền.
    - Cảnh báo khi món đã hết hàng, ngừng bán hoặc thay đổi giá.
    """
    tok = _resolve_guest_token(guest_token, x_guest_token)
    cart = _get_or_create_active_cart(db, tok)

    dish_ids = [ci.dish_id for ci in cart.items]
    dishes = (
        db.query(Dish)
        .filter(Dish.id.in_(dish_ids))
        .options(joinedload(Dish.category), joinedload(Dish.options))
        .all()
        if dish_ids
        else []
    )
    dish_map = {d.id: d for d in dishes}

    items_out: list[CartItemOut] = []
    warnings: list[str] = []
    subtotal = 0
    has_unavailable = False

    for ci in cart.items:
        dish = dish_map.get(ci.dish_id)
        dto = _build_cart_item_out(ci, dish)
        items_out.append(dto)
        if not dto.is_active:
            has_unavailable = True
            warnings.append(f"Món '{dto.dish_name}' đã ngừng kinh doanh (ẩn).")
        elif not dto.is_available:
            has_unavailable = True
            warnings.append(f"Món '{dto.dish_name}' hiện đã hết món.")
        else:
            subtotal += dto.line_total

    price_changed = False
    if expected_subtotal is not None and expected_subtotal != subtotal:
        price_changed = True
        warnings.append(f"Giá món ăn trong giỏ đã thay đổi (tạm tính mới: {subtotal:,}đ).")

    shipping_fee = calculate_shipping_fee(area) if subtotal > 0 else 0
    discount_amount = 0
    applied_code = None

    if voucher_code and voucher_code.strip() and subtotal > 0:
        v_obj, disc, v_msg = evaluate_voucher(db, voucher_code, subtotal)
        if v_obj:
            discount_amount = disc
            applied_code = v_obj.code
        else:
            warnings.append(v_msg)

    total_amount = max(0, subtotal + shipping_fee - discount_amount)

    return CartCalculationOut(
        cart_id=cart.id,
        guest_token=tok,
        items=items_out,
        subtotal=subtotal,
        area=area or "Nội thành",
        shipping_fee=shipping_fee,
        voucher_code=applied_code,
        discount_amount=discount_amount,
        total_amount=total_amount,
        has_unavailable_item=has_unavailable,
        price_changed=price_changed,
        warnings=warnings,
    )


@router.post("/calculate", response_model=CartCalculationOut)
def calculate_cart_preview(
    req: CartPreviewRequest,
    guest_token: Optional[str] = Query(None),
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """API tính tiền giỏ hàng tại server từ danh sách món gửi lên hoặc từ giỏ DB (T3D262C)."""
    if req.items is None:
        return get_my_cart_and_calculate(
            area=req.area,
            voucher_code=req.voucher_code,
            expected_subtotal=req.expected_subtotal,
            guest_token=guest_token,
            x_guest_token=x_guest_token,
            db=db,
        )

    dish_ids = [it.dish_id for it in req.items]
    dishes = (
        db.query(Dish)
        .filter(Dish.id.in_(dish_ids))
        .options(joinedload(Dish.category), joinedload(Dish.options))
        .all()
        if dish_ids
        else []
    )
    dish_map = {d.id: d for d in dishes}

    items_out: list[CartItemOut] = []
    warnings: list[str] = []
    subtotal = 0
    has_unavailable = False
    price_changed = False

    for idx, it in enumerate(req.items, start=1):
        dish = dish_map.get(it.dish_id)
        primary_opt, norm_json = _normalize_options(it.dish_option_id, it.selected_option_ids)
        temp_ci = CartItem(
            id=idx,
            cart_id=0,
            dish_id=it.dish_id,
            dish_option_id=primary_opt,
            selected_options_json=norm_json,
            note=it.note,
            quantity=it.quantity,
        )
        dto = _build_cart_item_out(temp_ci, dish)
        items_out.append(dto)

        if not dto.is_active:
            has_unavailable = True
            warnings.append(f"Món '{dto.dish_name}' đã ngừng kinh doanh.")
        elif not dto.is_available:
            has_unavailable = True
            warnings.append(f"Món '{dto.dish_name}' hiện đã hết món.")
        else:
            subtotal += dto.line_total

        if it.expected_unit_price is not None and it.expected_unit_price != dto.unit_price:
            price_changed = True
            warnings.append(f"Đơn giá món '{dto.dish_name}' đã thay đổi thành {dto.unit_price:,}đ.")

    if req.expected_subtotal is not None and req.expected_subtotal != subtotal:
        price_changed = True
        warnings.append(f"Tạm tính giỏ hàng đã thay đổi thành {subtotal:,}đ.")

    shipping_fee = calculate_shipping_fee(req.area) if subtotal > 0 else 0
    discount_amount = 0
    applied_code = None

    if req.voucher_code and req.voucher_code.strip() and subtotal > 0:
        v_obj, disc, v_msg = evaluate_voucher(db, req.voucher_code, subtotal)
        if v_obj:
            discount_amount = disc
            applied_code = v_obj.code
        else:
            warnings.append(v_msg)

    total_amount = max(0, subtotal + shipping_fee - discount_amount)

    return CartCalculationOut(
        cart_id=None,
        guest_token=(guest_token or x_guest_token),
        items=items_out,
        subtotal=subtotal,
        area=req.area or "Nội thành",
        shipping_fee=shipping_fee,
        voucher_code=applied_code,
        discount_amount=discount_amount,
        total_amount=total_amount,
        has_unavailable_item=has_unavailable,
        price_changed=price_changed,
        warnings=warnings,
    )


@router.post("/items", response_model=CartItemOut, status_code=status.HTTP_201_CREATED)
def add_item_to_cart(
    item_in: CartItemCreate,
    guest_token: Optional[str] = Query(None),
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Thêm món vào giỏ hàng:
    - Chặn món hết hàng hoặc đã ẩn.
    - Cùng món nhưng khác tuỳ chọn hoặc khác ghi chú là dòng riêng.
    - Trùng hoàn toàn (món + tuỳ chọn + ghi chú) thì cộng dồn số lượng.
    """
    tok = _resolve_guest_token(guest_token, x_guest_token)
    cart = _get_or_create_active_cart(db, tok)

    dish = (
        db.query(Dish)
        .join(Category, Dish.category_id == Category.id)
        .filter(Dish.id == item_in.dish_id)
        .options(joinedload(Dish.category), joinedload(Dish.options))
        .first()
    )
    if not dish or not dish.is_active or not dish.category.is_active or dish.status == "HIDDEN":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DISH_INACTIVE",
                "message": "Món ăn không tồn tại hoặc đã ngừng kinh doanh (ẩn)",
                "details": {},
            },
        )

    if not dish.is_available or dish.status == "OUT_OF_STOCK":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "DISH_OUT_OF_STOCK",
                "message": f"Món '{dish.name}' hiện đã hết hàng, không thể thêm vào giỏ",
                "details": {},
            },
        )

    primary_opt_id, norm_opts_json = _normalize_options(item_in.dish_option_id, item_in.selected_option_ids)
    norm_note = (item_in.note or "").strip() or None

    # Kiểm tra dòng trùng hoàn toàn (cùng dish_id, cùng selected_options_json, cùng note)
    existing = next(
        (
            ci
            for ci in cart.items
            if ci.dish_id == dish.id
            and (ci.selected_options_json or "[]") == norm_opts_json
            and ((ci.note or "").strip() or None) == norm_note
        ),
        None,
    )

    if existing:
        existing.quantity = min(99, existing.quantity + item_in.quantity)
        db.commit()
        db.refresh(existing)
        return _build_cart_item_out(existing, dish)

    new_ci = CartItem(
        cart_id=cart.id,
        dish_id=dish.id,
        dish_option_id=primary_opt_id,
        selected_options_json=norm_opts_json,
        note=norm_note,
        quantity=item_in.quantity,
    )
    db.add(new_ci)
    db.commit()
    db.refresh(new_ci)
    return _build_cart_item_out(new_ci, dish)


@router.put("/items/{item_id}")
def update_cart_item(
    item_id: int,
    item_in: CartItemUpdate,
    guest_token: Optional[str] = Query(None),
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Sửa số lượng, tuỳ chọn hoặc ghi chú dòng giỏ hàng (chỉ thao tác trên giỏ của mình)."""
    tok = _resolve_guest_token(guest_token, x_guest_token)
    cart = _get_or_create_active_cart(db, tok)

    ci = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not ci:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CART_ITEM_NOT_FOUND", "message": "Không tìm thấy dòng món trong giỏ hàng", "details": {}},
        )
    if ci.cart_id != cart.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN_CART", "message": "Bạn chỉ được thao tác trên giỏ hàng của chính mình", "details": {}},
        )

    if item_in.quantity is not None:
        if item_in.quantity <= 0:
            db.delete(ci)
            db.commit()
            return {"deleted": True, "item_id": item_id, "message": "Đã xoá món khỏi giỏ hàng"}
        ci.quantity = item_in.quantity

    if item_in.note is not None:
        ci.note = item_in.note.strip() or None

    if item_in.dish_option_id is not None or item_in.selected_option_ids is not None:
        primary_opt_id, norm_opts_json = _normalize_options(item_in.dish_option_id, item_in.selected_option_ids)
        ci.dish_option_id = primary_opt_id
        ci.selected_options_json = norm_opts_json

    db.commit()
    db.refresh(ci)
    dish = db.query(Dish).filter(Dish.id == ci.dish_id).options(joinedload(Dish.category), joinedload(Dish.options)).first()
    return _build_cart_item_out(ci, dish)


@router.delete("/items/{item_id}")
def delete_cart_item(
    item_id: int,
    guest_token: Optional[str] = Query(None),
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Xoá 1 dòng khỏi giỏ hàng của mình."""
    tok = _resolve_guest_token(guest_token, x_guest_token)
    cart = _get_or_create_active_cart(db, tok)

    ci = db.query(CartItem).filter(CartItem.id == item_id).first()
    if not ci:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CART_ITEM_NOT_FOUND", "message": "Không tìm thấy dòng món trong giỏ", "details": {}},
        )
    if ci.cart_id != cart.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN_CART", "message": "Bạn chỉ được thao tác trên giỏ hàng của chính mình", "details": {}},
        )

    db.delete(ci)
    db.commit()
    return {"deleted": True, "item_id": item_id, "message": "Đã xoá món khỏi giỏ hàng"}


@router.delete("")
def clear_my_cart(
    guest_token: Optional[str] = Query(None),
    x_guest_token: Optional[str] = Header(None, alias="X-Guest-Token"),
    db: Session = Depends(get_db),
):
    """Làm trống toàn bộ giỏ hàng của mình."""
    tok = _resolve_guest_token(guest_token, x_guest_token)
    cart = _get_or_create_active_cart(db, tok)
    db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
    db.commit()
    return {"cleared": True, "message": "Đã xoá toàn bộ giỏ hàng"}
