# Test Case & Test Log Module Khuyến Mãi, Đánh Giá, Chat & Thống Kê Dashboard - T3D1BED

| Mã TC | Chức năng | Loại kiểm thử | Đầu vào / Các bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bug phát hiện & Trạng thái sửa |
|---|---|---|---|---|---|---|---|
| TC-V01 | Kiểm tra mã giảm giá không phân biệt hoa thường (`POST /api/vouchers/check`) | Đúng dữ liệu | `code="demkhuya10", subtotal=100000` | Trả về `discount_amount=10000, valid=true` | HTTP 200, giảm 10.000đ | **PASS** | Không |
| TC-V02 | Kiểm tra mã giảm giá chưa đủ đơn tối thiểu | Sai điều kiện | `code="DEMKHUYA10", subtotal=20000` | Trả HTTP 400 `INVALID_VOUCHER` | HTTP 400 `INVALID_VOUCHER` | **PASS** | Không |
| TC-R01 | Khách đánh giá món khi đơn chưa Hoàn thành (`POST /api/reviews`) | Sai điều kiện | Đơn đang ở `pending` | Trả HTTP 400 `ORDER_NOT_COMPLETED` | HTTP 400 `ORDER_NOT_COMPLETED` | **PASS** | Không |
| TC-R02 | Khách đánh giá 1 món trong đơn Hoàn thành lần thứ 2 | Ràng buộc dữ liệu | Gửi lại đánh giá cho cùng `(order_code, dish_id)` | Trả HTTP 400 `ALREADY_REVIEWED` | HTTP 400 `ALREADY_REVIEWED` | **PASS** | Không |
| TC-R03 | Cửa hàng trả lời đánh giá & Admin ẩn đánh giá vi phạm | Đúng dữ liệu (Admin) | `POST /api/admin/reviews/{id}/reply`, `PATCH /api/admin/reviews/{id}/visibility` | Lưu `store_reply` và cập nhật `is_visible=false` | HTTP 200 OK | **PASS** | Không |
| TC-H01 | Khách gửi tin nhắn và lấy tin mới qua `since` (`GET /api/chat/messages?since=...`) | Đúng dữ liệu | Khách gửi tin, nhân viên trả lời, khách gọi `since=id_cu` | Chỉ trả về các tin nhắn mới có `id > since` | HTTP 200, nhận đúng tin trả lời mới | **PASS** | Không |
| TC-D01 | Xem thống kê Dashboard khi chưa đăng nhập hoặc là khách | Chưa đăng nhập / Sai quyền | `GET /api/admin/dashboard/analytics` | Trả HTTP 401 / 403 | HTTP 401 / 403 | **PASS** | Không |
| TC-D02 | Xem thống kê Dashboard theo khoảng thời gian (Ngày/Tháng) | Đúng dữ liệu (Admin) | `GET /api/admin/dashboard/analytics?group_by=day` | Trả doanh thu, đơn theo trạng thái, món bán chạy, điểm đánh giá TB, số mã giảm đã dùng | HTTP 200, đầy đủ dữ liệu cho Chart.js | **PASS** | Không |
