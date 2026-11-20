"""Luồng trạng thái đơn hàng và bảng chuyển trạng thái hợp lệ (T3D28D5).

Luồng chuẩn:
Chờ xác nhận (pending) -> Đã xác nhận (confirmed) -> Đang chuẩn bị (preparing)
-> Đang giao (delivering) -> Hoàn thành (completed), và Đã huỷ (cancelled).
"""

ORDER_STATUS_LABELS: dict[str, str] = {
    "pending": "Chờ xác nhận",
    "confirmed": "Đã xác nhận",
    "preparing": "Đang chuẩn bị",
    "delivering": "Đang giao",
    "completed": "Hoàn thành",
    "cancelled": "Đã huỷ",
}

# Bảng chuyển trạng thái hợp lệ
VALID_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "pending": ["confirmed", "cancelled"],
    "confirmed": ["preparing", "cancelled"],
    "preparing": ["delivering", "cancelled"],
    "delivering": ["completed"],
    "completed": [],
    "cancelled": [],
}

CUSTOMER_CANCELLABLE_STATUSES: set[str] = {"pending"}
STAFF_CANCELLABLE_STATUSES: set[str] = {"pending", "confirmed", "preparing"}
TERMINAL_STATUSES: set[str] = {"completed", "cancelled"}


def can_transition_status(old_status: str, new_status: str, actor_role: str = "admin") -> tuple[bool, str]:
    """Kiểm tra bước chuyển trạng thái có hợp lệ theo vai trò (customer / admin) hay không."""
    if old_status in TERMINAL_STATUSES:
        return False, f"Đơn hàng đã ở trạng thái kết thúc ({ORDER_STATUS_LABELS.get(old_status, old_status)}), không thể thay đổi."

    if actor_role == "customer":
        if new_status != "cancelled":
            return False, "Khách hàng chỉ có quyền yêu cầu huỷ đơn."
        if old_status not in CUSTOMER_CANCELLABLE_STATUSES:
            return False, "Khách hàng chỉ có thể huỷ đơn khi đơn đang ở trạng thái 'Chờ xác nhận'."
        return True, "Hợp lệ"

    allowed = VALID_STATUS_TRANSITIONS.get(old_status, [])
    if new_status not in allowed:
        return (
            False,
            f"Không thể chuyển trạng thái từ '{old_status}' sang '{new_status}'. Các trạng thái hợp lệ tiếp theo: {allowed}",
        )
    return True, "Hợp lệ"
