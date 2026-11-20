"""Module quản lý giới hạn số lần thử (Rate Limiting) trong bộ nhớ (NFR-15, FR-07, FR-08)."""
import time
from typing import Dict, Tuple

# Lưu trữ: key -> (failed_count, lock_until_timestamp, last_attempt_timestamp)
_admin_login_attempts: Dict[str, Tuple[int, float, float]] = {}
_order_lookup_attempts: Dict[str, Tuple[int, float, float]] = {}

LOCK_DURATION_SECONDS = 15 * 60  # 15 phút
WINDOW_SECONDS = 15 * 60         # Khung thời gian 15 phút


def check_admin_login_rate_limit(key: str) -> Tuple[bool, int]:
    """Kiểm tra xem IP + username có đang bị khóa đăng nhập không.
    Trả về (is_allowed, seconds_remaining).
    """
    now = time.time()
    if key in _admin_login_attempts:
        count, lock_until, last_time = _admin_login_attempts[key]
        if now < lock_until:
            return False, int(lock_until - now)
        # Nếu đã hết thời gian khóa hoặc quá cửa sổ 15p
        if now - last_time > WINDOW_SECONDS:
            del _admin_login_attempts[key]
    return True, 0


def record_admin_login_failure(key: str) -> int:
    """Ghi nhận đăng nhập thất bại. Trả về số lần còn lại trước khi khóa."""
    now = time.time()
    count = 1
    lock_until = 0.0

    if key in _admin_login_attempts:
        prev_count, prev_lock, last_time = _admin_login_attempts[key]
        if now - last_time <= WINDOW_SECONDS:
            count = prev_count + 1
        else:
            count = 1

    if count >= 5:
        lock_until = now + LOCK_DURATION_SECONDS

    _admin_login_attempts[key] = (count, lock_until, now)
    return max(0, 5 - count)


def reset_admin_login_failure(key: str):
    """Xóa lịch sử thất bại khi đăng nhập thành công."""
    if key in _admin_login_attempts:
        del _admin_login_attempts[key]


def check_order_lookup_rate_limit(ip: str) -> Tuple[bool, int]:
    """Kiểm tra IP có bị khóa tra cứu đơn không (tối đa 10 lần sai trong 15 phút)."""
    now = time.time()
    if ip in _order_lookup_attempts:
        count, lock_until, last_time = _order_lookup_attempts[ip]
        if now < lock_until:
            return False, int(lock_until - now)
        if now - last_time > WINDOW_SECONDS:
            del _order_lookup_attempts[ip]
    return True, 0


def record_order_lookup_failure(ip: str) -> int:
    """Ghi nhận tra cứu đơn thất bại."""
    now = time.time()
    count = 1
    lock_until = 0.0

    if ip in _order_lookup_attempts:
        prev_count, prev_lock, last_time = _order_lookup_attempts[ip]
        if now - last_time <= WINDOW_SECONDS:
            count = prev_count + 1
        else:
            count = 1

    if count >= 10:
        lock_until = now + LOCK_DURATION_SECONDS

    _order_lookup_attempts[ip] = (count, lock_until, now)
    return max(0, 10 - count)
