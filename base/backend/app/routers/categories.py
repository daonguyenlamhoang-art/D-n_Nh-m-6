"""Router Danh mục món ăn cho khách hàng (FR-01, FR-03, T3D1F9B)."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.category import Category
from app.models.dish import Dish
from app.schemas.category import CategoryOut

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def get_public_categories(db: Session = Depends(get_db)):
    """Lấy danh sách các danh mục đang hoạt động (is_active = True) theo thứ tự sort_order."""
    cats = (
        db.query(Category)
        .filter(Category.is_active == True)
        .order_by(Category.sort_order.asc(), Category.id.asc())
        .all()
    )
    counts = dict(
        db.query(Dish.category_id, func.count(Dish.id))
        .filter(Dish.is_active == True)
        .group_by(Dish.category_id)
        .all()
    )
    result = []
    for c in cats:
        dto = CategoryOut.model_validate(c)
        dto.dish_count = counts.get(c.id, 0)
        result.append(dto)
    return result
