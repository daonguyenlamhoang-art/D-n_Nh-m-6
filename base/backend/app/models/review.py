"""Model Review (reviews) - T3D2A41"""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    dish_id: Mapped[int] = mapped_column(Integer, ForeignKey("dishes.id", ondelete="CASCADE"), nullable=False)
    customer_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    store_reply: Mapped[str | None] = mapped_column(Text, nullable=True)
    replied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    dish = relationship("Dish", back_populates="reviews")
