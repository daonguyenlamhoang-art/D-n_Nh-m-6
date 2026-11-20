# Đặc Tả Module Giỏ Hàng & Đặt Món + Ghép ERD Chung 13 Bảng (T3D1B9D)

## 1. Đặc tả chức năng Module Giỏ hàng & Đặt món (Cart & Checkout)
- **Quản lý Giỏ hàng (`carts`, `cart_items`)**:
  - Thêm món kèm tuỳ chọn đã chọn (`dish_option_id`, `selected_options_json`), ghi chú riêng từng dòng (`note`), số lượng (`quantity` từ 1..99).
  - Quy tắc gộp dòng: Cùng món nhưng khác tuỳ chọn hoặc khác ghi chú sẽ tách thành dòng riêng; trùng hoàn toàn cả món, tuỳ chọn và ghi chú thì cộng dồn số lượng.
  - Chặn thêm món đã hết (`OUT_OF_STOCK`) hoặc đã ẩn (`HIDDEN`); mỗi khách chỉ thao tác trên giỏ của mình (`user_id` hoặc `guest_token`).
- **Tính tiền Giỏ hàng tại Server**:
  - Tính thành tiền từng dòng = `(giá món gốc + tổng giá tuỳ chọn) * số lượng`.
  - Tính tạm tính (`subtotal`), phí vận chuyển theo khu vực (`shipping_fee`), giảm giá từ mã khuyến mãi (`discount_amount`), tổng thanh toán (`total_amount`).
  - Cảnh báo ngay khi trong giỏ có món vừa hết hàng hoặc vừa thay đổi giá.
- **Đặt món trong Transaction (`orders`, `order_items`)**:
  - Kiểm tra giờ mở cửa của quán (18:00 - 02:00) và giờ giao mong muốn (`desired_delivery_time`).
  - Kiểm tra toàn bộ món còn bán, lưu snapshot giá bán và tuỳ chọn lúc đặt vào `order_items`, tạo `orders`, ghi lịch sử trạng thái đầu tiên `Chờ xác nhận` (`pending`), trừ lượt dùng `vouchers`, và xoá giỏ hàng trong **một transaction nguyên tử**.
  - Chống bấm đặt hàng 2 lần liên tiếp (Idempotency / Double-submit protection).

## 2. Thiết kế bảng của Module
### Bảng `carts` & `cart_items`
- `carts`: `id` (PK), `user_id` (FK -> `users.id`), `guest_token` (UNIQUE), `status` (`active` / `checked_out`), `created_at`, `updated_at`.
- `cart_items`: `id` (PK), `cart_id` (FK -> `carts.id`), `dish_id` (FK -> `dishes.id`), `dish_option_id` (FK -> `dish_options.id`), `selected_options_json` (TEXT), `note` (VARCHAR(255)), `quantity` (INT).

### Bảng `orders` & `order_items`
- `orders`: `id` (PK), `order_code` (UNIQUE), `user_id` (FK), `guest_token`, `address_id` (FK), `voucher_id` (FK), `customer_name`, `phone`, `customer_email`, `address`, `area`, `note`, `desired_delivery_time`, `subtotal`, `shipping_fee`, `discount_amount`, `total_amount`, `payment_method` (`COD` / `CHUYEN_KHOAN`), `payment_confirmed`, `status`, `created_at`, `updated_at`.
- `order_items`: `id` (PK), `order_id` (FK -> `orders.id`), `dish_id` (FK -> `dishes.id`), `dish_option_id` (FK -> `dish_options.id`), `dish_name`, `option_name`, `options_json`, `note`, `quantity`, `unit_price`, `subtotal`.

## 3. Liên kết vào ERD Chung 13 Bảng
- `users (1) --- (n) carts (1) --- (n) cart_items (n) --- (1) dishes / dish_options`
- `users / addresses / vouchers (1) --- (n) orders (1) --- (n) order_items / order_status_histories / reviews / chat_messages`
- Chi tiết mã DBML đầy đủ tại: `base/database/nightfood_erd.dbml`.
