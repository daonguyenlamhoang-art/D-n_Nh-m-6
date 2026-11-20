# Test Case & Test Log Module Đơn Hàng, Theo Dõi & Xử Lý Đơn - T3D1BF5

| Mã TC | Chức năng | Loại kiểm thử | Đầu vào / Các bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bug phát hiện & Trạng thái sửa |
|---|---|---|---|---|---|---|---|
| TC-O01 | Xem danh sách đơn của tôi (`GET /api/orders/my`) | Đúng dữ liệu | Gửi kèm `X-Guest-Token` hoặc `phone` của khách | Trả danh sách đơn của chính khách đó kèm món, tuỳ chọn, dòng thời gian trạng thái | HTTP 200, đầy đủ thông tin | **PASS** | Không |
| TC-O02 | Xem chi tiết đơn của người khác (`GET /api/orders/{code}/track`) | Sai quyền | Dùng `X-Guest-Token` không khớp chủ đơn | Trả HTTP 403 `FORBIDDEN_ORDER` | HTTP 403 `FORBIDDEN_ORDER` | **PASS** | Không |
| TC-O03 | Khách huỷ đơn khi đang `Chờ xác nhận` (`pending`) | Đúng dữ liệu | `POST /api/orders/{code}/cancel` | Đơn chuyển sang `cancelled`, ghi `order_status_histories` | HTTP 200 `status="cancelled"` | **PASS** | Không |
| TC-O04 | Khách huỷ đơn khi đã sang `Đã xác nhận` (`confirmed`) | Sai điều kiện | `POST /api/orders/{code}/cancel` | Chặn huỷ, trả HTTP 400 `CANNOT_CANCEL_ORDER` | HTTP 400 `CANNOT_CANCEL_ORDER` | **PASS** | Không |
| TC-O05 | Nhân viên huỷ đơn trước `Đang giao` kèm lý do | Đúng dữ liệu | `POST /api/admin/orders/{id}/cancel` với `reason="Hết món"` | Đơn chuyển sang `cancelled`, hoàn lại lượt voucher, ghi lịch sử | HTTP 200 `status="cancelled"` | **PASS** | Không |
| TC-O06 | Nhân viên huỷ đơn nhưng để trống lý do | Sai dữ liệu | `reason=""` | Trả HTTP 400 `CANCEL_REASON_REQUIRED` | HTTP 400 `CANCEL_REASON_REQUIRED` | **PASS** | Không |
| TC-O07 | Nhân viên chuyển trạng thái nhảy cóc (`pending` -> `delivering`) | Sai quy trình | `PATCH /api/admin/orders/{id}/status` | Trả HTTP 400 `INVALID_TRANSITION` | HTTP 400 `INVALID_TRANSITION` | **PASS** | Không |
| TC-O08 | Gọi API xử lý đơn nhân viên khi chưa đăng nhập | Chưa đăng nhập | `GET /api/admin/orders/board` không token | Trả HTTP 401 `UNAUTHORIZED` | HTTP 401 `UNAUTHORIZED` | **PASS** | Không |
