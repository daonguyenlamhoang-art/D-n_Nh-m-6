# Đặc Tả Module Đơn Hàng & Lịch Sử Trạng Thái + Ghép ERD Chung 13 Bảng (T3D1BA3)

## 1. Đặc tả chức năng Module Đơn hàng & Lịch sử trạng thái
- **Đơn của tôi & Theo dõi đơn (`orders`, `order_items`, `order_status_histories`)**:
  - Khách xem danh sách đơn của mình theo tab trạng thái, xem chi tiết đơn kèm danh sách món, tuỳ chọn lúc đặt và dòng thời gian chuyển trạng thái.
  - Tự động làm mới tiến trình mỗi 15 giây trên giao diện theo dõi đơn.
- **Luồng chuyển trạng thái hợp lệ**:
  - `pending` (Chờ xác nhận) → `confirmed` (Đã xác nhận) → `preparing` (Đang chuẩn bị) → `delivering` (Đang giao) → `completed` (Hoàn thành).
  - Huỷ đơn (`cancelled`): Khách chỉ được huỷ khi đơn còn ở `pending` (Chờ xác nhận); Nhân viên/Admin được huỷ trước khi sang `delivering` (Đang giao) kèm lý do bắt buộc.
  - Mọi thao tác đổi trạng thái đều tự động ghi vết vào `order_status_histories` (trạng thái cũ, trạng thái mới, người đổi, ghi chú/lý do, thời điểm).
- **Xử lý đơn cho Nhân viên & In phiếu**:
  - Màn hình xử lý đơn theo cột trạng thái (Mới, Đang chuẩn bị, Đang giao), âm báo đơn mới, lọc theo ngày/trạng thái, tìm theo mã đơn/SĐT, in phiếu bếp/shipper bằng `window.print()`.

## 2. Thiết kế bảng của Module
- **`orders`**: `id` (PK), `order_code` (UNIQUE), `user_id` (FK), `guest_token`, `address_id` (FK), `voucher_id` (FK), `customer_name`, `phone`, `customer_email`, `address`, `area`, `note`, `desired_delivery_time`, `subtotal`, `shipping_fee`, `discount_amount`, `total_amount`, `payment_method`, `payment_confirmed`, `status`, `created_at`, `updated_at`.
- **`order_items`**: `id` (PK), `order_id` (FK -> `orders.id`), `dish_id` (FK -> `dishes.id`), `dish_option_id` (FK -> `dish_options.id`), `dish_name`, `option_name`, `options_json`, `note`, `quantity`, `unit_price`, `subtotal`.
- **`order_status_histories`**: `id` (PK), `order_id` (FK -> `orders.id`), `changed_by` (FK -> `users.id`), `old_status`, `new_status`, `note`, `changed_at`.

## 3. Ghép vào ERD Chung 13 Bảng
- Kết nối trực tiếp với `users`, `addresses`, `vouchers`, `dishes`, `dish_options`, `reviews`, `chat_messages` trong `base/database/nightfood_erd.dbml`.
