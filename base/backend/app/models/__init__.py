"""Tổng hợp các models để SQLAlchemy nhận diện bảng."""
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.chat import ChatMessage
from app.models.dish import Dish, DishOption
from app.models.item import Item
from app.models.order import Order, OrderItem, OrderStatusHistory
from app.models.review import Review
from app.models.user import User
from app.models.voucher import Voucher

__all__ = [
    "User",
    "Address",
    "Category",
    "Dish",
    "DishOption",
    "Item",
    "Cart",
    "CartItem",
    "Voucher",
    "Order",
    "OrderItem",
    "OrderStatusHistory",
    "Review",
    "ChatMessage",
]
