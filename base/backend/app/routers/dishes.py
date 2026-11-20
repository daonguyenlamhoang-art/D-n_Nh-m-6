"""Router Món ăn & Menu cho khách hàng (T3D232C, FR-01, FR-02, FR-03, BR-06, BR-16)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.category import Category
from app.models.dish import Dish
from app.models.order import Order, OrderItem
from app.models.review import Review
from app.schemas.dish import DishOut

router = APIRouter(prefix="/dishes", tags=["Dishes"])


def enrich_dishes_list(db: Session, dishes: list[Dish]) -> list[DishOut]:
    """Bổ sung category_name, avg_rating, review_count, sold_count cho danh sách món ăn."""
    if not dishes:
        return []

    dish_ids = [d.id for d in dishes]

    rating_rows = (
        db.query(Review.dish_id, func.avg(Review.rating), func.count(Review.id))
        .filter(Review.dish_id.in_(dish_ids), Review.is_visible == True)
        .group_by(Review.dish_id)
        .all()
    )
    rating_map = {r[0]: (round(float(r[1] or 5.0), 1), int(r[2] or 0)) for r in rating_rows}

    sold_rows = (
        db.query(OrderItem.dish_id, func.sum(OrderItem.quantity))
        .join(Order, OrderItem.order_id == Order.id)
        .filter(OrderItem.dish_id.in_(dish_ids), Order.status != "cancelled")
        .group_by(OrderItem.dish_id)
        .all()
    )
    sold_map = {r[0]: int(r[1] or 0) for r in sold_rows}

    result: list[DishOut] = []
    for d in dishes:
        dto = DishOut.model_validate(d)
        dto.category_name = d.category.name if d.category else None
        avg_r, cnt_r = rating_map.get(d.id, (5.0, 0))
        dto.avg_rating = avg_r
        dto.review_count = cnt_r
        dto.sold_count = sold_map.get(d.id, 0)
        result.append(dto)
    return result


@router.get("/menu")
def get_customer_menu(db: Session = Depends(get_db)):
    """API Menu tổng hợp cho khách chưa đăng nhập (T3D232C):
    - Danh sách món theo từng danh mục đang bán (bỏ món ẩn và danh mục ẩn).
    - Danh sách món nổi bật (featured_dishes).
    - Danh sách món bán chạy (bestseller_dishes).
    """
    categories = (
        db.query(Category)
        .filter(Category.is_active == True)
        .order_by(Category.sort_order.asc(), Category.id.asc())
        .all()
    )
    dishes = (
        db.query(Dish)
        .join(Category, Dish.category_id == Category.id)
        .filter(Dish.is_active == True, Dish.status != "HIDDEN", Category.is_active == True)
        .options(joinedload(Dish.category), joinedload(Dish.options))
        .order_by(Dish.id.asc())
        .all()
    )
    enriched = enrich_dishes_list(db, dishes)

    cat_groups = []
    for c in categories:
        cat_dishes = [d for d in enriched if d.category_id == c.id]
        cat_groups.append({
            "id": c.id,
            "name": c.name,
            "sort_order": c.sort_order,
            "dish_count": len(cat_dishes),
            "dishes": cat_dishes,
        })

    featured_dishes = [d for d in enriched if d.is_featured]
    bestseller_dishes = sorted(
        enriched,
        key=lambda x: (x.sold_count, 1 if x.is_featured else 0, -x.id),
        reverse=True,
    )[:6]

    return {
        "categories": cat_groups,
        "featured_dishes": featured_dishes,
        "bestseller_dishes": bestseller_dishes,
    }


@router.get("/featured", response_model=list[DishOut])
def get_featured_dishes(db: Session = Depends(get_db)):
    """Lấy danh sách món ăn nổi bật cho trang chủ (T3D232C)."""
    dishes = (
        db.query(Dish)
        .join(Category, Dish.category_id == Category.id)
        .filter(
            Dish.is_active == True,
            Dish.status != "HIDDEN",
            Category.is_active == True,
            Dish.is_featured == True,
        )
        .options(joinedload(Dish.category), joinedload(Dish.options))
        .order_by(Dish.id.asc())
        .all()
    )
    return enrich_dishes_list(db, dishes)


@router.get("/bestsellers", response_model=list[DishOut])
def get_bestseller_dishes(limit: int = Query(6, ge=1, le=30), db: Session = Depends(get_db)):
    """Lấy danh sách món bán chạy dựa trên số lượng đặt hàng (T3D232C, T3D228F)."""
    dishes = (
        db.query(Dish)
        .join(Category, Dish.category_id == Category.id)
        .filter(Dish.is_active == True, Dish.status != "HIDDEN", Category.is_active == True)
        .options(joinedload(Dish.category), joinedload(Dish.options))
        .all()
    )
    enriched = enrich_dishes_list(db, dishes)
    return sorted(
        enriched,
        key=lambda x: (x.sold_count, 1 if x.is_featured else 0, -x.id),
        reverse=True,
    )[:limit]


@router.get("", response_model=list[DishOut])
def get_dishes(
    search: Optional[str] = Query(None, max_length=100),
    category_id: Optional[int] = None,
    ids: Optional[str] = Query(None, description="Danh sách ID cách nhau bởi dấu phẩy để kiểm tra lại giỏ hàng"),
    db: Session = Depends(get_db),
):
    """Lấy danh sách món ăn công khai (bỏ món ẩn và danh mục ẩn)."""
    query = (
        db.query(Dish)
        .join(Category, Dish.category_id == Category.id)
        .filter(Dish.is_active == True, Dish.status != "HIDDEN", Category.is_active == True)
        .options(joinedload(Dish.category), joinedload(Dish.options))
    )

    if category_id is not None:
        query = query.filter(Dish.category_id == category_id)

    if search:
        clean_search = search.strip()
        if clean_search:
            query = query.filter(Dish.name.ilike(f"%{clean_search}%"))

    if ids:
        try:
            id_list = [int(i.strip()) for i in ids.split(",") if i.strip()]
            if id_list:
                query = query.filter(Dish.id.in_(id_list))
        except ValueError:
            pass

    dishes = query.order_by(Dish.id.asc()).all()
    return enrich_dishes_list(db, dishes)


@router.get("/{dish_id}", response_model=DishOut)
def get_dish_detail(dish_id: int, db: Session = Depends(get_db)):
    """Xem chi tiết món ăn (FR-02). Nếu món đã ẩn hoặc thuộc danh mục ẩn thì trả HTTP 404."""
    dish = (
        db.query(Dish)
        .join(Category, Dish.category_id == Category.id)
        .filter(
            Dish.id == dish_id,
            Dish.is_active == True,
            Dish.status != "HIDDEN",
            Category.is_active == True,
        )
        .options(joinedload(Dish.category), joinedload(Dish.options))
        .first()
    )

    if not dish:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "DISH_NOT_FOUND",
                "message": "Không tìm thấy món ăn hoặc món ăn đã ngừng kinh doanh",
                "details": {},
            },
        )

    return enrich_dishes_list(db, [dish])[0]
