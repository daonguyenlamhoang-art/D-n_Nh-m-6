"""Xác thực người dùng, băm mật khẩu bcrypt và quản lý phiên Admin (FR-08, NFR-03, NFR-04, NFR-16)."""
import secrets
import time
from typing import Dict, Optional

import bcrypt
from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

# Bộ nhớ phiên (token -> {user_id: int, username: str, expires_at: float})
_active_sessions: Dict[str, dict] = {}


def hash_password(password: str) -> str:
    """Băm mật khẩu bằng bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu khớp với chuỗi băm."""
    if not hashed_password:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_session(user_id: int, username: str) -> str:
    """Tạo token phiên mới có thời hạn."""
    token = secrets.token_urlsafe(32)
    expires_at = time.time() + (settings.SESSION_EXPIRE_HOURS * 3600)
    _active_sessions[token] = {
        "user_id": user_id,
        "username": username,
        "expires_at": expires_at,
    }
    return token


def invalidate_session(token: str):
    """Xóa phiên khi đăng xuất."""
    if token in _active_sessions:
        del _active_sessions[token]


def get_session_data(token: Optional[str]) -> Optional[dict]:
    """Lấy dữ liệu phiên nếu token hợp lệ và chưa hết hạn."""
    if not token or token not in _active_sessions:
        return None
    session_data = _active_sessions[token]
    if time.time() > session_data["expires_at"]:
        del _active_sessions[token]
        return None
    return session_data


SESSION_COOKIE_NAME = "nightfood_session"


def set_session_cookie(response: Response, token: str):
    """Đặt cookie HttpOnly cho phiên đăng nhập."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_EXPIRE_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=False,  # Bật True khi có HTTPS
        path="/",
    )


def clear_session_cookie(response: Response):
    """Xóa cookie phiên."""
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")


def get_current_admin(request: Request, db: Session = Depends(get_db)):
    """Dependency bảo vệ các API Admin (trả 401 nếu chưa đăng nhập hoặc không phải admin)."""
    # 1. Lấy token từ Cookie hoặc Authorization Header
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    session_data = get_session_data(token)
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Vui lòng đăng nhập quyền quản trị viên",
                "details": {},
            },
        )

    # 2. Truy vấn user từ Database để đảm bảo trạng thái còn active
    from app.models.user import User

    user = db.query(User).filter(User.id == session_data["user_id"]).first()
    if not user or not user.is_active or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Tài khoản không hợp lệ hoặc đã bị vô hiệu hóa",
                "details": {},
            },
        )
    return user
