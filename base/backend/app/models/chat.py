"""Model ChatMessage (chat_messages) - T3D2A41"""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    order_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    sender_type: Mapped[str] = mapped_column(Enum("customer", "admin"), nullable=False)
    guest_token: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    customer_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
