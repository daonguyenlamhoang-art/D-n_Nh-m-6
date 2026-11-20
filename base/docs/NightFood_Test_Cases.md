# BẢNG KẾT QUẢ KIỂM THỬ HỆ THỐNG (TEST CASES) - NIGHTFOOD v1.2
**Dự án:** Quán bán đồ ăn đêm trực tuyến NightFood  
**Nhóm:** 6 thành viên | **Phạm vi:** 39 Test Cases bắt buộc  

| Mã TC | Tình huống kiểm thử | Các bước thực hiện | Kết quả mong đợi | Trạng thái |
|---|---|---|---|---|
| **TC-01** | Mở trang thực đơn | Truy cập `dishes.html` hoặc trang chủ | Hiển thị danh sách món ăn từ MySQL (`is_active = 1`) | **ĐẠT (PASS)** |
| **TC-02** | Tìm kiếm món ăn có tồn tại | Nhập từ khóa "mì trộn" hoặc "gà" | Hiển thị đúng các món có chứa từ khóa (không phân biệt hoa/thường) | **ĐẠT (PASS)** |
| **TC-03** | Tìm kiếm món không tồn tại | Nhập từ khóa "xyz999" | Hiển thị thông báo không tìm thấy kết quả phù hợp | **ĐẠT (PASS)** |
| **TC-04** | Lọc theo danh mục | Chọn tab danh mục "Combo ăn đêm" hoặc "Mì và cơm" | Chỉ hiển thị các món ăn thuộc đúng danh mục đã chọn | **ĐẠT (PASS)** |
| **TC-05** | Thêm món vào giỏ hàng | Bấm nút "+ Thêm" hoặc "Thêm vào giỏ" | Badge giỏ hàng trên header tăng lên, món lưu vào localStorage | **ĐẠT (PASS)** |
| **TC-06** | Tăng/giảm số lượng trong giỏ | Bấm nút "+" hoặc "-" tại `cart.html` | Số lượng thay đổi trong khoảng 1..99, thành tiền và tổng tạm tính tự động tính lại | **ĐẠT (PASS)** |
| **TC-07** | Xóa món khỏi giỏ hàng | Bấm nút "Xóa" tại `cart.html` | Món biến mất khỏi giỏ, cập nhật lại tổng tiền | **ĐẠT (PASS)** |
| **TC-08** | Tải lại trang (F5) | Tải lại trình duyệt sau khi thêm món | Giỏ hàng vẫn giữ nguyên dữ liệu trong localStorage | **ĐẠT (PASS)** |
| **TC-09** | Đặt hàng COD hợp lệ | Nhập tên, SĐT 10 số (0912345678), địa chỉ, bấm Đặt hàng | Tạo đơn hàng trong MySQL, sinh mã `NF...`, hiển thị trang thành công | **ĐẠT (PASS)** |
| **TC-10** | Thiếu số điện thoại khi đặt hàng | Để trống ô số điện thoại hoặc xóa SĐT | Báo lỗi tại trường SĐT, không cho gửi đơn lên Backend | **ĐẠT (PASS)** |
| **TC-11** | Đặt hàng khi giỏ rỗng | Mở `checkout.html` khi chưa có món | Chặn không cho đặt, thông báo giỏ rỗng và chuyển về thực đơn | **ĐẠT (PASS)** |
| **TC-12** | Đặt món đã hết hàng (`is_available = 0`) | Admin tắt còn hàng một món, khách bấm đặt món đó | Backend từ chối với mã lỗi `DISH_OUT_OF_STOCK`, thông báo rõ món cần đổi | **ĐẠT (PASS)** |
| **TC-13** | Sửa giá / tổng tiền giả mạo từ Frontend | Sửa request POST `/api/orders` gửi tổng tiền 100đ | Backend tự truy vấn giá từ MySQL và tính lại, không dùng giá từ trình duyệt | **ĐẠT (PASS)** |
| **TC-14** | Đăng nhập Admin đúng thông tin | Nhập `admin` / `admin123` tại `admin/login.html` | Cấp quyền truy cập, thiết lập cookie HttpOnly, chuyển vào Dashboard | **ĐẠT (PASS)** |
| **TC-15** | Đăng nhập Admin sai mật khẩu | Nhập mật khẩu sai | Từ chối truy cập, thông báo chung "Sai tên đăng nhập hoặc mật khẩu" | **ĐẠT (PASS)** |
| **TC-16** | Gọi API Admin khi chưa đăng nhập | Gửi GET tới `/api/admin/orders` không có phiên | Backend từ chối bằng HTTP 401 Unauthorized | **ĐẠT (PASS)** |
| **TC-17** | Thêm món ăn mới hợp lệ | Admin điền tên món, chọn danh mục, giá 45000đ, bấm Lưu | Món mới được lưu vào bảng `dishes` và xuất hiện trong thực đơn | **ĐẠT (PASS)** |
| **TC-18** | Nhập giá âm hoặc bằng 0 khi thêm món | Admin nhập giá -5000đ hoặc 0đ | Backend trả HTTP 400 báo lỗi "Giá món ăn phải lớn hơn 0" | **ĐẠT (PASS)** |
| **TC-19** | Ẩn sản phẩm (Soft delete) | Admin đổi trạng thái sang Ẩn (`is_active = 0`) | Món không còn hiển thị trên thực đơn khách, nhưng lịch sử đơn cũ không bị lỗi | **ĐẠT (PASS)** |
| **TC-20** | Admin xem danh sách đơn hàng | Truy cập `admin/orders.html` | Thấy toàn bộ đơn vừa đặt theo thứ tự mới nhất xếp trước | **ĐẠT (PASS)** |
| **TC-21** | Cập nhật trạng thái hợp lệ | Đổi từ `pending` sang `confirmed` rồi sang `preparing` | Lưu trạng thái mới, tự động ghi nhận vào bảng `order_status_histories` | **ĐẠT (PASS)** |
| **TC-22** | Chuyển đơn Đã hủy sang Hoàn thành | Cố tình chuyển trạng thái đơn `cancelled` | Bị từ chối bằng HTTP 400 "Đơn hàng đã ở trạng thái kết thúc" | **ĐẠT (PASS)** |
| **TC-23** | Tra cứu bằng mã đơn và SĐT đúng | Nhập mã `NF...` và đúng SĐT đặt hàng tại `order-lookup.html` | Hiển thị chi tiết trạng thái, timeline, danh sách món và tổng tiền | **ĐẠT (PASS)** |
| **TC-24** | Tra cứu bằng SĐT sai | Nhập mã đơn đúng nhưng số điện thoại sai | Trả về HTTP 404 với thông báo chung "Không tìm thấy đơn hàng phù hợp" | **ĐẠT (PASS)** |
| **TC-25** | Kiểm thử giao diện Mobile (375px) | Bật Responsive Mode 375px | Bố cục co giãn mượt mà, không xuất hiện thanh cuộn ngang do lỗi CSS | **ĐẠT (PASS)** |
| **TC-26** | Lỗi Database trong lúc tạo đơn | Gián đoạn kết nối DB giữa chừng | Giao dịch (Transaction) rollback hoàn toàn, không lưu đơn rác thiếu chi tiết | **ĐẠT (PASS)** |
| **TC-27** | Số lượng món là 0 hoặc 100 | Nhập số lượng 0 hoặc 100 | Bị chặn và báo lỗi số lượng món chỉ trong khoảng 1 đến 99 | **ĐẠT (PASS)** |
| **TC-28** | Số điện thoại sai định dạng (9 số, chứa chữ,...) | Nhập SĐT "091234" hoặc "091234abcd" | Form báo lỗi: "Số điện thoại phải đúng 10 số và bắt đầu bằng số 0" | **ĐẠT (PASS)** |
| **TC-29** | Đổi giá món trong lúc khách ở trang checkout | Giá món đổi trên DB khi khách đang mở checkout | Backend trả HTTP 409 `PRICE_CHANGED`, hiện modal giá mới và yêu cầu xác nhận | **ĐẠT (PASS)** |
| **TC-30** | Món thuộc danh mục bị ẩn | Admin ẩn một danh mục món | Toàn bộ món thuộc danh mục đó lập tức biến mất khỏi thực đơn và tìm kiếm | **ĐẠT (PASS)** |
| **TC-31** | Nhấn nút Đặt hàng liên tiếp nhiều lần | Bấm liên tục nút Xác nhận đặt hàng | Nút lập tức bị vô hiệu hóa (disabled), chỉ gửi 1 request duy nhất | **ĐẠT (PASS)** |
| **TC-32** | Đăng nhập sai 5 lần liên tiếp | Cố tình nhập sai mật khẩu admin 5 lần | Backend chặn bằng HTTP 429 Too Many Requests, khóa 15 phút | **ĐẠT (PASS)** |
| **TC-33** | Tra cứu không khớp quá 10 lần trong 15 phút | Cố tình tra cứu sai 10 lần liên tục | Backend chặn bằng HTTP 429 Too Many Requests | **ĐẠT (PASS)** |
| **TC-34** | Chuyển trạng thái nhảy cóc (pending sang delivering) | Gọi API đổi status sai quy trình | Backend từ chối bằng HTTP 400 Invalid Transition | **ĐẠT (PASS)** |
| **TC-35** | Hai Admin cùng đổi trạng thái một đơn cùng lúc | Admin A và B cùng mở đơn, A đổi trước | Backend từ chối thao tác của B bằng HTTP 409 Conflict | **ĐẠT (PASS)** |
| **TC-36** | Chống XSS (nhập thẻ `<script>` vào tên, ghi chú) | Khách nhập `<script>alert('xss')</script>` | Frontend dùng `escapeHtml()` hiển thị văn bản thuần, không thực thi mã | **ĐẠT (PASS)** |
| **TC-37** | Chống SQL Injection trong ô tìm kiếm | Nhập `' OR 1=1 --` vào ô tìm kiếm món | SQLAlchemy tham số hóa an toàn, không rò rỉ dữ liệu hay lỗi SQL | **ĐẠT (PASS)** |
| **TC-38** | Dữ liệu localStorage bị hỏng hoặc món đã ẩn | Sửa localStorage thành chuỗi rác | Hệ thống tự lọc bỏ dữ liệu hỏng, không gây lỗi trắng trang | **ĐẠT (PASS)** |
| **TC-39** | Đặt hàng ngoài giờ mở cửa (khi tắt FORCE_OPEN) | Đặt hàng ban ngày khi quán đóng cửa | Backend từ chối đơn với HTTP 409 mã `STORE_CLOSED` | **ĐẠT (PASS)** |
