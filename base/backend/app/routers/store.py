"""Router kiểm tra và quản lý trạng thái mở/đóng cửa quán ăn đêm (FR-14, TC-39)."""
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.config import settings
from app.core.auth import get_current_admin
from app.models.user import User

router = APIRouter(prefix="/store", tags=["Store"])

VN_TZ = timezone(timedelta(hours=7))


class StoreStatusOut(BaseModel):
    is_open: bool
    open_time: str
    close_time: str
    current_time: str
    status_text: str
    force_open: bool


def check_is_store_open() -> tuple[bool, str, datetime]:
    """Kiểm tra xem quán có đang mở cửa không.
    Mặc định: 18:00 đến 02:00 sáng hôm sau theo giờ Việt Nam (UTC+7).
    Nếu STORE_FORCE_OPEN = True trong cấu hình thì cho phép mở để phục vụ kiểm thử / demo ban ngày.
    """
    now = datetime.now(VN_TZ)
    hour = now.hour
    is_in_operating_hours = (hour >= settings.STORE_OPEN_HOUR or hour < settings.STORE_CLOSE_HOUR)

    if settings.STORE_FORCE_OPEN:
        is_open = True
        status_text = "Đang mở cửa (Chế độ hỗ trợ kiểm thử / demo)"
    elif is_in_operating_hours:
        is_open = True
        status_text = "Đang mở cửa đón khách (18:00 - 02:00)"
    else:
        is_open = False
        status_text = "Đã đóng cửa (Mở cửa từ 18:00 đến 02:00 sáng)"

    return is_open, status_text, now


@router.get("/status", response_model=StoreStatusOut)
def get_store_status():
    """Lấy trạng thái mở/đóng cửa hiện tại của quán."""
    is_open, status_text, now = check_is_store_open()
    return StoreStatusOut(
        is_open=is_open,
        open_time=f"{settings.STORE_OPEN_HOUR:02d}:00",
        close_time=f"{settings.STORE_CLOSE_HOUR:02d}:00",
        current_time=now.strftime("%H:%M:%S %d/%m/%Y"),
        status_text=status_text,
        force_open=settings.STORE_FORCE_OPEN,
    )


@router.post("/toggle-force-open")
def toggle_store_force_open(current_admin: User = Depends(get_current_admin)):
    """Admin có thể bật/tắt cờ FORCE_OPEN để kiểm thử kịch bản mở/đóng cửa (TC-39)."""
    settings.STORE_FORCE_OPEN = not settings.STORE_FORCE_OPEN
    is_open, status_text, _ = check_is_store_open()
    return {
        "message": f"Đã chuyển trạng thái FORCE_OPEN sang {settings.STORE_FORCE_OPEN}",
        "force_open": settings.STORE_FORCE_OPEN,
        "is_open": is_open,
        "status_text": status_text,
    }
