# Test Case & Test Log Module Menu (Danh Mục, Món Ăn, Tuỳ Chọn) - T3D1BEF

| Mã TC | Chức năng | Loại kiểm thử | Đầu vào / Các bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bug phát hiện & Trạng thái sửa |
|---|---|---|---|---|---|---|---|
| TC-M01 | Lấy menu cho khách (`GET /api/dishes/menu`) | Chưa đăng nhập (Public) | Gọi API không cần token | Trả HTTP 200 kèm 6 danh mục, món nổi bật, món bán chạy (bỏ món ẩn) | HTTP 200 OK, đầy đủ 6 danh mục & 30 món | **PASS** | Không |
| TC-M02 | Thêm danh mục mới (`POST /api/admin/categories`) | Đúng dữ liệu (Admin) | Admin gửi `name="Đồ lẩu đêm", sort_order=7` | Trả HTTP 201 Created | HTTP 201 Created | **PASS** | Không |
| TC-M03 | Thêm danh mục trùng tên | Sai dữ liệu | Admin gửi tên danh mục đã tồn tại | Trả HTTP 400 `CATEGORY_EXISTS` | HTTP 400 `CATEGORY_EXISTS` | **PASS** | Không |
| TC-M04 | Xoá danh mục đang còn món (`DELETE /api/admin/categories/1`) | Ràng buộc dữ liệu | Admin gọi xoá danh mục ID=1 (đang có 5 món) | Chặn xoá, trả HTTP 400 `CATEGORY_HAS_DISHES` | HTTP 400 `CATEGORY_HAS_DISHES` | **PASS** | Đã phát hiện thiếu chặn xoá ở bản đầu -> Đã sửa (Fixed) |
| TC-M05 | Gọi API thêm món khi chưa đăng nhập | Chưa đăng nhập / Sai quyền | Gửi `POST /api/admin/dishes` không có token Admin | Trả HTTP 401 `UNAUTHORIZED` | HTTP 401 `UNAUTHORIZED` | **PASS** | Không |
| TC-M06 | Thêm món với giá <= 0 | Sai dữ liệu | Admin gửi `price = -5000` hoặc `0` | Trả HTTP 422 / 400 báo lỗi giá > 0 | HTTP 422 `VALIDATION_ERROR` | **PASS** | Không |
| TC-M07 | Xoá món đã có trong đơn hàng (`DELETE /api/admin/dishes/1`) | Ràng buộc toàn vẹn | Admin bấm xoá món ID=1 đã từng được khách đặt | Không xoá cứng; tự chuyển sang trạng thái `HIDDEN` (`is_active=false`) | HTTP 200 `action="hidden"` | **PASS** | Đã bổ sung cơ chế tự chuyển sang Ẩn (Fixed) |
| TC-M08 | Báo hết món nhanh (`PATCH /api/admin/dishes/{id}/availability`) | Đúng dữ liệu | Nhân viên tắt còn bán trong ngày | Món chuyển sang `OUT_OF_STOCK`, khách không đặt được | HTTP 200 `status="OUT_OF_STOCK"` | **PASS** | Không |
