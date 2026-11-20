"""Model Dish và DishOption (dishes, dish_options) - T3D1F81"""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Dish(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey("categories.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    # Trạng thái món: AVAILABLE (ĐANG BÁN), OUT_OF_STOCK (HẾT MÓN), HIDDEN (ẨN)
    status: Mapped[str] = mapped_column(String(20), default="AVAILABLE", nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_combo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    combo_items_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("Category", back_populates="dishes")
    options = relationship("DishOption", back_populates="dish", cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="dish")

    def sync_status_flags(self):
        """Đồng bộ giữa cột status (ĐANG BÁN / HẾT MÓN / ẨN) và cặp cờ is_available / is_active."""
        if not self.is_active or self.status in ("HIDDEN", "ẨN"):
            self.is_active = False
            self.status = "HIDDEN"
        elif not self.is_available or self.status in ("OUT_OF_STOCK", "HẾT MÓN"):
            self.is_active = True
            self.is_available = False
            self.status = "OUT_OF_STOCK"
        else:
            self.is_active = True
            self.is_available = True
            self.status = "AVAILABLE"


class DishOption(Base):
    __tablename__ = "dish_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    dish_id: Mapped[int] = mapped_column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    option_group: Mapped[str] = mapped_column(String(50), default="Topping", nullable=False)
    option_name: Mapped[str] = mapped_column(String(100), nullable=False)
    extra_price: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_select: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    dish = relationship("Dish", back_populates="options")
