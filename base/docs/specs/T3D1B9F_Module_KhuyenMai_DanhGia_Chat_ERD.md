# Đặc Tả Module Khuyến Mãi, Đánh Giá & Chat + Ghép ERD Chung 13 Bảng (T3D1B9F)

## 1. Đặc tả chức năng Module Khuyến mãi, Đánh giá & Chat
- **Mã giảm giá (`vouchers`)**:
  - Admin tạo, sửa, bật/tắt mã giảm giá theo phần trăm (`percent`) hoặc số tiền cố định (`fixed`), đơn tối thiểu (`min_order_amount`), giảm tối đa (`max_discount_amount`), thời hạn (`start_at`, `end_at`), giới hạn lượt dùng (`usage_limit`) và số lượt đã dùng (`used_count`).
  - API kiểm tra mã không phân biệt hoa thường, trả về số tiền giảm cho Giỏ hàng; tự động trừ lượt khi đặt món thành công.
- **Đánh giá món ăn (`reviews`)**:
  - Khách có đơn ở trạng thái `Hoàn thành` (`completed`) được chấm sao (1..5), viết nhận xét và đính kèm ảnh cho từng món trong đơn đúng 1 lần.
  - Tính điểm trung bình của từng món; Cửa hàng trả lời đánh giá (`store_reply`); Admin ẩn đánh giá vi phạm (`is_visible = false`).
- **Chat trực tuyến (`chat_messages`)**:
  - Khách gửi tin nhắn hỗ trợ từ khung chat nổi (polling tin mới mỗi 3 giây qua tham số `since = id tin cuối`); Nhân viên xem danh sách hội thoại, số tin chưa đọc (`is_read = false`) và phản hồi.

## 2. Thiết kế bảng của Module
- **`vouchers`**: `id` (PK), `code` (UNIQUE), `discount_type` (`fixed`/`percent`), `discount_value`, `min_order_amount`, `max_discount_amount`, `start_at`, `end_at`, `usage_limit`, `used_count`, `is_active`.
- **`reviews`**: `id` (PK), `order_id` (FK -> `orders.id`), `user_id` (FK -> `users.id`), `dish_id` (FK -> `dishes.id`), `customer_name`, `rating` (TINYINT 1..5), `comment`, `image_url`, `store_reply`, `replied_at`, `is_visible`, `created_at`.
- **`chat_messages`**: `id` (PK), `user_id` (FK -> `users.id`), `order_id` (FK -> `orders.id`), `sender_type` (`customer`/`admin`), `guest_token`, `customer_name`, `message`, `is_read`, `created_at`.

## 3. Ghép vào ERD Chung 13 Bảng
- Kết nối trực tiếp với `users`, `orders`, `dishes` trong `base/database/nightfood_erd.dbml`.
