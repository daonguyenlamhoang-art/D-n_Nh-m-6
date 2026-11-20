"""Dịch vụ gửi Email xác nhận đơn hàng và thông báo đổi trạng thái qua SMTP chạy nền bằng FastAPI BackgroundTasks (T3D2F7B)."""
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import smtplib
from typing import Optional

from app.core.config import settings
from app.core.order_workflow import ORDER_STATUS_LABELS

# Nhật ký email đã gửi phục vụ kiểm tra & giám sát
_sent_email_logs: list[dict] = []


def send_order_notification_email(
    recipient_email: Optional[str],
    order_code: str,
    customer_name: str,
    status_key: str,
    total_amount: int,
    event_type: str = "ORDER_CREATED",
) -> None:
    """Hàm chạy nền trong FastAPI BackgroundTasks gửi email qua SMTP (Gmail App Password)."""
    status_label = ORDER_STATUS_LABELS.get(status_key, status_key)
    target_email = (recipient_email or "").strip() or "customer@nightfood.local"

    if event_type == "ORDER_CREATED":
        subject = f"[NightFood] Xác nhận đặt món thành công - Mã đơn #{order_code}"
        heading = f"Cảm ơn {customer_name} đã đặt món tại NightFood!"
    else:
        subject = f"[NightFood] Đơn hàng #{order_code} đã chuyển sang: {status_label}"
        heading = f"Cập nhật trạng thái đơn hàng #{order_code}"

    html_body = f"""
    <div style="font-family: Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 10px;">
      <h2 style="color: #F97316; margin-top: 0;">🌙 NightFood - Đồ Ăn Đêm Nóng Hổi</h2>
      <h3>{heading}</h3>
      <p><strong>Mã đơn hàng:</strong> {order_code}</p>
      <p><strong>Khách hàng:</strong> {customer_name}</p>
      <p><strong>Trạng thái hiện tại:</strong> <span style="color: #16a34a; font-weight: bold;">{status_label}</span></p>
      <p><strong>Tổng thanh toán:</strong> {total_amount:,}đ</p>
      <hr style="border: none; border-top: 1px solid #cbd5e1; margin: 16px 0;">
      <p style="font-size: 12px; color: #64748b;">Email được gửi tự động từ hệ thống NightFood (FastAPI BackgroundTasks).</p>
    </div>
    """

    delivery_status = "simulated_smtp"
    if settings.SMTP_USER and settings.SMTP_APP_PASSWORD and recipient_email:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.SMTP_FROM_EMAIL or settings.SMTP_USER
            msg["To"] = recipient_email
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_APP_PASSWORD)
                server.sendmail(msg["From"], [recipient_email], msg.as_string())
            delivery_status = "sent_via_smtp"
        except Exception as exc:
            delivery_status = f"smtp_fallback ({exc})"

    _sent_email_logs.append({
        "order_code": order_code,
        "recipient_email": target_email,
        "subject": subject,
        "status_key": status_key,
        "status_label": status_label,
        "event_type": event_type,
        "delivery_status": delivery_status,
        "sent_at": datetime.now().isoformat(),
    })


def get_sent_email_logs() -> list[dict]:
    return list(reversed(_sent_email_logs[-50:]))
