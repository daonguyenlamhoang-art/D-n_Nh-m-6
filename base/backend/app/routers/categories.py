"""Router Danh mục món ăn cho khách hàng (FR-01, FR-03)."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.category import Category
from app.schemas.category import CategoryOut

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def get_public_categories(db: Session = Depends(get_db)):
    """Lấy danh sách các danh mục đang hoạt động (is_active = True)."""
    return db.query(Category).filter(Category.is_active == True).order_by(Category.id.asc()).all()
