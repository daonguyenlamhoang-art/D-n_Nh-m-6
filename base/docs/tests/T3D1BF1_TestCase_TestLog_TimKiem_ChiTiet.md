# Test Case & Test Log Module Tìm Kiếm, Lọc & Chi Tiết Món - T3D1BF1

| Mã TC | Chức năng | Loại kiểm thử | Đầu vào / Các bước | Kết quả mong đợi | Kết quả thực tế | Trạng thái | Bug phát hiện & Trạng thái sửa |
|---|---|---|---|---|---|---|---|
| TC-S01 | Tìm kiếm món theo từ khoá (`GET /api/dishes/search?q=mi`) | Đúng dữ liệu | Nhập từ khoá `"mi"` | Trả danh sách các món mì đang bán, không phân biệt hoa thường | HTTP 200, tìm thấy 3 món mì | **PASS** | Không |
| TC-S02 | Tìm kiếm với chuỗi SQL Injection | Sai dữ liệu / Bảo mật | Nhập `q=' OR 1=1 --` | Không lỗi SQL, trả danh sách rỗng an toàn | HTTP 200, `total=0` | **PASS** | Không |
| TC-S03 | Lọc theo khoảng giá & còn bán | Đúng dữ liệu | `min_price=25000&max_price=45000&available_only=true` | Tất cả món trả về có giá trong đoạn `[25000, 45000]` và `is_available=true` | HTTP 200, thoả mãn 100% điều kiện lọc | **PASS** | Không |
| TC-S04 | Sắp xếp theo giá tăng/giảm, bán chạy, đánh giá | Đúng dữ liệu | `sort_by=price_asc`, `price_desc`, `bestseller`, `rating` | Thứ tự danh sách đúng tiêu chí sắp xếp | HTTP 200, thứ tự chính xác | **PASS** | Không |
| TC-S05 | Phân trang sai tham số (`page=0` hoặc `page_size=-5`) | Sai dữ liệu | Gửi `GET /api/dishes/search?page=0` | Trả HTTP 422 `VALIDATION_ERROR` | HTTP 422 `VALIDATION_ERROR` | **PASS** | Không |
| TC-S06 | Xem chi tiết món kèm nhóm tuỳ chọn (`GET /api/dishes/1`) | Chưa đăng nhập | Khách truy cập trang chi tiết món ID=1 | Hiển thị ảnh, mô tả, nhóm `Size` (bắt buộc) và `Topping` (chọn nhiều), điểm đánh giá | HTTP 200, `option_groups` gồm 2 nhóm | **PASS** | Đã bổ sung `option_groups` gom nhóm chuẩn (Fixed) |
| TC-S07 | Xem chi tiết món đã ẩn hoặc không tồn tại | Sai dữ liệu | Gửi `GET /api/dishes/9999` | Trả HTTP 404 `DISH_NOT_FOUND` | HTTP 404 `DISH_NOT_FOUND` | **PASS** | Không |
