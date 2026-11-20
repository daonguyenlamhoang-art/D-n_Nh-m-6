# 🌙 NightFood - Website Quán Bán Đồ Ăn Đêm Trực Tuyến

> **Dự án thực tập OJT / Đồ án nhóm:** Xây dựng website bán đồ ăn đêm trực tuyến NightFood  
> **Phiên bản SRS:** v1.2 (Đáp ứng đầy đủ 13 bảng theo ERD chung, 39 Test Cases và toàn bộ quy tắc nghiệp vụ BR-01 → BR-18)  
> **Công nghệ:** HTML5, CSS3, JavaScript ES6+, Python, FastAPI, MySQL / MariaDB  

---

## 🌟 1. Điểm nổi bật của hệ thống
- **Giao diện chuẩn Dark Mode Night-Food:** Tông màu nền tối `#111827` và `#1F2937`, màu nhấn cam neon `#F97316` và vàng rực rỡ `#FBBF24`. Chuẩn Responsive trên điện thoại (375px), máy tính bảng (768px) và màn hình lớn (1366px), không lỗi thanh cuộn ngang (NFR-02).
- **Thực đơn đêm hấp dẫn:** Mì trộn xúc xích lòng đào, Cơm gà sốt cay, Cháo sườn sụn, Nem chua rán, Chân gà sả tắc, Trà đào cam sả và các combo ăn đêm (Combo Cú Đêm, Combo Cày Deadline...).
- **Khách hàng đặt hàng COD nhanh chóng:** Đặt hàng chỉ với Tên, Số điện thoại (chuẩn 10 số `^0[0-9]{9}$`) và Địa chỉ nhận hàng, không bắt buộc đăng ký tài khoản (BR-01).
- **Giỏ hàng thông minh:** Lưu trữ tạm trong `localStorage`, tự động đối chiếu lại giá và trạng thái còn hàng với API khi mở giỏ hoặc thanh toán (FR-05).
- **Cơ chế chống gian lận & Xử lý giá thay đổi (`PRICE_CHANGED` - HTTP 409):** Tổng tiền được tính toán độc lập tại Backend từ Database. Khi giá món thay đổi lúc khách đang đặt, hệ thống trả về HTTP 409 cùng modal cập nhật giá mới để khách hàng xác nhận lại (BR-05, BR-17).
- **Kiểm tra giờ mở cửa ban đêm (`STORE_CLOSED` - HTTP 409):** Giờ hoạt động 18:00 đến 02:00 sáng hôm sau. Có nút toggle chế độ ép mở cửa trong Admin để phục vụ chấm điểm / demo ban ngày (FR-14, TC-39).
- **Tra cứu đơn hàng bảo mật (FR-07):** Tra cứu bằng **Mã đơn** + **Số điện thoại**, ẩn bớt địa chỉ giao hàng để bảo vệ riêng tư. Tích hợp Rate Limit tối đa 10 lần sai trong 15 phút chống dò đơn (HTTP 429).
- **Bảng điều khiển Admin bảo mật (FR-08 → FR-12, FR-15):**
  - Đăng nhập Admin bảo mật bằng mật khẩu băm `bcrypt` và Cookie HttpOnly, tự khóa 15 phút nếu sai 5 lần liên tiếp (HTTP 429).
  - Thống kê Dashboard: Tổng số đơn, đơn chờ xử lý, đơn hoàn thành, tổng doanh thu thực tế.
  - Quản lý sản phẩm & danh mục: Thêm, sửa giá, chuyển trạng thái còn hàng/hết hàng, ẩn món/danh mục (Soft Delete).
  - Quản lý đơn hàng: Xem chi tiết và cập nhật trạng thái đơn theo đúng ma trận chuyển trạng thái hợp lệ (Chờ xác nhận → Đã xác nhận → Đang chuẩn bị → Đang giao → Hoàn thành / Đã hủy), hỗ trợ Optimistic Locking chống xung đột.
- **An toàn & Bảo mật:** Chống XSS (hàm `escapeHtml`), Chống SQL Injection (SQLAlchemy tham số hóa), mật khẩu không lưu plaintext.

---

## 🗄️ 2. Thiết kế Cơ sở dữ liệu (Đầy đủ 13 bảng theo ERD SRS v1.2)
Hệ quản trị: **MySQL 8.x / MariaDB**, charset `utf8mb4`.

| STT | Bảng dữ liệu | Mục đích |
|---|---|---|
| 1 | `users` | Tài khoản Admin (`role='admin'`) và tài khoản khách |
| 2 | `addresses` | Sổ địa chỉ giao hàng của khách |
| 3 | `categories` | Danh mục món ăn (Mì & Cơm, Đồ chiên, Đồ nướng, Đồ uống, Combo...) |
| 4 | `dishes` | Danh sách món ăn đêm, giá bán, ảnh, mô tả, trạng thái |
| 5 | `dish_options` | Tùy chọn món ăn (thêm trứng, thêm phô mai...) |
| 6 | `carts` | Giỏ hàng lưu trữ database |
| 7 | `cart_items` | Dòng món trong giỏ hàng |
| 8 | `vouchers` | Mã giảm giá đêm khuya |
| 9 | `orders` | Đơn đặt hàng (Mã đơn `NF...`, người nhận, tổng tiền, COD, trạng thái) |
| 10 | `order_items` | Chi tiết món trong đơn (Lưu snapshot tên và giá tại thời điểm đặt) |
| 11 | `order_status_histories` | Lịch sử chuyển trạng thái đơn (ai đổi, từ trạng thái nào sang đâu) |
| 12 | `reviews` | Đánh giá số sao và bình luận của khách |
| 13 | `chat_messages` | Tin nhắn trao đổi hỗ trợ khách hàng |

---

## 🚀 3. Hướng dẫn cài đặt và khởi chạy

### Bước 1: Khởi động MySQL / MariaDB
- Đảm bảo MySQL đang chạy ở cổng `3306` (Ví dụ qua XAMPP: bấm Start MySQL).
- Đã có sẵn 2 file SQL trong thư mục `database/`:
  - `database/schema.sql`: Khởi tạo database `food_night_db` và 13 bảng dữ liệu.
  - `database/sample_data.sql`: Nạp sẵn các danh mục và 16 món ăn đêm hấp dẫn.

### Bước 2: Cài đặt và chạy Backend (FastAPI)
Mở terminal tại thư mục dự án:
```powershell
# Di chuyển vào thư mục backend
cd backend

# Kích hoạt môi trường ảo Python
.\venv\Scripts\activate   # (Hoặc python -m venv venv nếu chưa có)

# Cài đặt thư viện phụ thuộc
pip install -r requirements.txt

# Tạo tài khoản Admin mặc định (nếu chưa tạo)
python scripts/create_admin.py admin admin123 "Quản Trị Viên NightFood"

# Chạy server FastAPI
uvicorn app.main:app --reload --port 8000
```
- Server Backend hoạt động tại: **`http://127.0.0.1:8000`**
- Tài liệu API tương tác tự động Swagger UI: **`http://127.0.0.1:8000/docs`**

### Bước 3: Truy cập Website
Vì FastAPI đã cấu hình mount toàn bộ Frontend tĩnh trực tiếp, bạn chỉ cần mở trình duyệt và truy cập:
- **Trang chủ khách hàng:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/) hoặc `http://127.0.0.1:8000/index.html`
- **Thực đơn đêm:** `http://127.0.0.1:8000/dishes.html`
- **Giỏ hàng:** `http://127.0.0.1:8000/cart.html`
- **Thanh toán:** `http://127.0.0.1:8000/checkout.html`
- **Tra cứu đơn hàng:** `http://127.0.0.1:8000/order-lookup.html`
- **Đăng nhập Quản trị viên (Admin):** `http://127.0.0.1:8000/admin/login.html`
  - **Tài khoản:** `admin`
  - **Mật khẩu:** `admin123`

*(Nếu mở qua Live Server cổng 5500, `js/config.js` cũng tự động trỏ API về `http://127.0.0.1:8000/api`)*

---

## 🎬 4. Kịch bản Demo báo cáo bảo vệ đồ án (10 bước hoàn chỉnh)
1. **Xem Trang chủ NightFood:** Giới thiệu logo trăng đêm neon, thanh trạng thái mở cửa (18:00 - 02:00), các danh mục và món ăn nổi bật.
2. **Khám phá Thực đơn (`dishes.html`):** Tìm kiếm thời gian thực (ví dụ gõ "mì"), lọc theo từng danh mục (Mì và cơm, Đồ chiên, Combo ăn đêm...).
3. **Xem Chi tiết món ăn (`product-detail.html`):** Chọn số lượng, xem ảnh lớn, mô tả và bấm "Thêm vào giỏ hàng".
4. **Quản lý Giỏ hàng (`cart.html`):** Tăng giảm số lượng (1..99), xem tạm tính tự động cập nhật, bấm "Tiến hành đặt hàng".
5. **Đặt hàng COD (`checkout.html`):** Nhập thông tin nhận hàng (Họ tên, SĐT 10 số, Địa chỉ) và bấm "Xác nhận đặt hàng". Nút bấm tự vô hiệu hóa chống gửi trùng.
6. **Nhận Mã đơn hàng (`order-success.html`):** Nhận mã đơn hàng duy nhất dạng `NF...` (Ví dụ `NF542189`).
7. **Đăng nhập Admin (`admin/login.html`):** Đăng nhập với tài khoản `admin` / `admin123`.
8. **Dashboard & Quản lý thực đơn:** Xem thống kê doanh thu và đơn hàng, thử thêm món mới hoặc bật/tắt còn hàng/hết hàng một món.
9. **Xử lý đơn hàng (`admin/orders.html`):** Xem đơn vừa đặt, mở chi tiết và chuyển trạng thái theo quy trình: `Chờ xác nhận` → `Đã xác nhận` → `Đang chuẩn bị` → `Đang giao` → `Hoàn thành`. Xem bảng lịch sử `order_status_histories`.
10. **Khách tra cứu tiến độ (`order-lookup.html`):** Nhập mã `NF...` và số điện thoại, quan sát timeline trạng thái trực quan đã chuyển sang tương ứng.
