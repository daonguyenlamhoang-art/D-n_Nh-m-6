# Test Case & Test Log Module Giỏ Hàng & Đặt Món (Cart & Checkout Transaction) - T3D1BF3

| Mã TC | Chức năng | Loại kiểm thử | Đầu vào / Các bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bug phát hiện & Trạng thái sửa |
|---|---|---|---|---|---|---|---|
| TC-C01 | Thêm cùng món + cùng tuỳ chọn + cùng ghi chú (`POST /api/cart/items`) | Đúng dữ liệu | Gửi 2 lần món ID=1, option=[1], note="Ít cay" | Cộng dồn số lượng trên cùng 1 dòng | HTTP 201, cộng dồn `quantity` chính xác | **PASS** | Không |
| TC-C02 | Thêm cùng món nhưng khác tuỳ chọn hoặc ghi chú | Đúng dữ liệu | Gửi món ID=1, option=[2], note="Nhiều cay" | Tách thành dòng `CartItem` riêng biệt | HTTP 201, tạo dòng mới có ID khác | **PASS** | Đã cập nhật logic phân biệt theo `(dish_id, options, note)` (Fixed) |
| TC-C03 | Xoá/sửa dòng giỏ hàng của người khác | Sai quyền | Dùng `X-Guest-Token` khác gọi `DELETE /api/cart/items/{id}` | Trả HTTP 403 `FORBIDDEN_CART` | HTTP 403 `FORBIDDEN_CART` | **PASS** | Không |
| TC-C04 | Tính tiền giỏ hàng tại Server (`GET /api/cart`, `POST /api/cart/calculate`) | Đúng dữ liệu | Khu vực `"Ngoại thành"`, mã `"demkhuya10"` | Tính đúng đơn giá + tuỳ chọn, phí ship 25.000đ, giảm 10% | HTTP 200, số liệu khớp 100% | **PASS** | Không |
| TC-C05 | Đặt món với giờ giao ngoài khung 18:00 - 02:00 | Sai dữ liệu | `desired_delivery_time="10:30"` | Trả HTTP 400 `DELIVERY_TIME_OUTSIDE_HOURS` | HTTP 400 `DELIVERY_TIME_OUTSIDE_HOURS` | **PASS** | Đã bổ sung `validate_desired_delivery_time` (Fixed) |
| TC-C06 | Đặt món hợp lệ trong Transaction (`POST /api/orders`) | Đúng dữ liệu | Đầy đủ tên, SĐT 10 số, địa chỉ, danh sách món | Tạo đơn `pending`, lưu snapshot giá/tuỳ chọn, trừ lượt voucher, xoá giỏ trong 1 transaction | HTTP 201, giỏ được làm trống, đơn ở trạng thái `pending` | **PASS** | Không |
| TC-C07 | Chống bấm đặt hàng 2 lần liên tiếp | Ràng buộc nghiệp vụ | Gửi 2 request cùng `X-Idempotency-Key` | Request thứ 2 bị chặn với HTTP 409 `DUPLICATE_ORDER_SUBMISSION` | HTTP 409 `DUPLICATE_ORDER_SUBMISSION` | **PASS** | Không |
