"""Router Món ăn cho khách hàng (FR-01, FR-02, FR-03, BR-06, BR-16)."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.category import Category
from app.models.dish import Dish
from app.schemas.dish import DishOut

router = APIRouter(prefix="/dishes", tags=["Dishes"])


@router.get("", response_model=list[DishOut])
def get_dishes(
    search: Optional[str] = Query(None, max_length=100),
    category_id: Optional[int] = None,
    ids: Optional[str] = Query(None, description="Danh sách ID cách nhau bởi dấu phẩy để kiểm tra lại giỏ hàng"),
    db: Session = Depends(get_db),
):
    """Lấy danh sách món ăn công khai.
    Quy tắc (BR-06, BR-16): Chỉ trả các món có is_active = True VÀ thuộc danh mục có is_active = True.
    """
    query = (
        db.query(Dish)
        .join(Category, Dish.category_id == Category.id)
        .filter(Dish.is_active == True, Category.is_active == True)
        .options(joinedload(Dish.options))
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

    # Thêm category_name vào output
    result = []
    for d in dishes:
        dish_dict = DishOut.model_validate(d)
        dish_dict.category_name = d.category.name if d.category else None
        result.append(dish_dict)

    return result


@router.get("/{dish_id}", response_model=DishOut)
def get_dish_detail(dish_id: int, db: Session = Depends(get_db)):
    """Xem chi tiết món ăn (FR-02).
    Nếu món không tồn tại, đã ẩn hoặc thuộc danh mục đã ẩn thì trả HTTP 404.
    """
    dish = (
        db.query(Dish)
        .join(Category, Dish.category_id == Category.id)
        .filter(Dish.id == dish_id, Dish.is_active == True, Category.is_active == True)
        .options(joinedload(Dish.options))
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

    out = DishOut.model_validate(dish)
    out.category_name = dish.category.name if dish.category else None
    return out
