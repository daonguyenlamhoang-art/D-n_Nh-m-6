# Đặc Tả Module Tài Khoản, Địa Chỉ & Thống Kê + Ghép ERD Chung 13 Bảng (T3D1B9B)

## 1. Đặc tả chức năng Module Tài khoản, Địa chỉ & Thống kê
- **Xác thực & Phân quyền (`users`)**:
  - Hỗ trợ phân quyền `admin` (Quản trị viên / Nhân viên) và `customer` (Khách hàng).
  - Băm mật khẩu an toàn bằng `bcrypt`, quản lý phiên qua Cookie `HttpOnly` + Bearer Token, tích hợp Rate Limit chống brute-force.
- **Sổ địa chỉ & Tính phí vận chuyển theo khu vực (`addresses`)**:
  - Quản lý danh sách địa chỉ nhận hàng của khách (`recipient_name`, `phone`, `address_line`, `area`, `is_default`).
  - Cung cấp hàm tính phí giao hàng theo khu vực (`calculate_shipping_fee(area)`) cho module Giỏ hàng và Thanh toán.
- **Thống kê Dashboard Admin & Xuất báo cáo**:
  - Thống kê doanh thu theo ngày/tháng, số lượng đơn theo từng trạng thái, danh sách món bán chạy, điểm đánh giá trung bình, số lượt mã giảm giá đã sử dụng (biểu đồ Chart.js + bộ lọc khoảng thời gian) và xuất CSV.

## 2. Thiết kế bảng của Module
- **`users`**: `id` (PK), `full_name`, `username` (UNIQUE), `phone`, `password_hash`, `role` (`admin`/`customer`), `is_active`, `created_at`.
- **`addresses`**: `id` (PK), `user_id` (FK -> `users.id`), `recipient_name`, `phone`, `address_line`, `area`, `is_default`.

## 3. Ghép vào ERD Chung 13 Bảng
- Kết nối trực tiếp với `carts`, `orders`, `order_status_histories`, `reviews`, `chat_messages` trong `base/database/nightfood_erd.dbml`.
