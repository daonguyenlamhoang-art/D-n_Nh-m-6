# Đặc Tả Thiết Kế Wireframe Trang Khách & CSS Chung (T3D22F6)

## 1. Hệ thống CSS chung (`base/frontend/css/style.css`)
- **Bảng màu Dark Mode NightFood**:
  - `--bg-main: #0B1120`, `--bg-card: #1E293B`, `--accent-primary: #F97316`, `--accent-secondary: #FBBF24`.
- **Thành phần dùng chung**:
  - Nút bấm: `.btn-primary`, `.btn-secondary`, `.btn-danger`, `.btn-add-cart`, `.btn-fav-heart`.
  - Card món ăn: `.dish-card`, `.dish-card.out-of-stock` (làm mờ món hết kèm nhãn `TẠM HẾT MÓN`).
  - Thanh danh mục dính trên cùng: `.sticky-category-nav`.
  - Ngăn kéo giỏ hàng trượt trên mobile: `.cart-drawer-overlay`, `.cart-drawer`.
  - Khung chat nổi cho khách: `.chat-fab`, `.chat-panel`.

## 2. Wireframe 5 Màn Hình Khách (Desktop 1366px & Mobile 375px)
1. **Trang chủ (`index.html`)**: Hero Banner, thanh danh mục dính trên cùng, món nổi bật, danh sách món theo từng danh mục.
2. **Menu & Tìm kiếm (`dishes.html`)**: Ô tìm kiếm có gợi ý debounce, bộ lọc danh mục/khoảng giá/còn bán, sắp xếp.
3. **Chi tiết món (`product-detail.html`)**: Chọn nhóm tuỳ chọn Size/Topping (bắt buộc/không), ghi chú, số lượng, giá động, đánh giá.
4. **Giỏ hàng (`cart.html` & Mobile Drawer)**: Danh sách món + tuỳ chọn + ghi chú, tăng/giảm/xoá, tạm tính, mã giảm giá.
5. **Theo dõi đơn (`order-lookup.html`)**: Tab đơn của tôi theo trạng thái, thanh tiến trình 5 bước tự cập nhật mỗi 15 giây, nút huỷ đơn khi còn `Chờ xác nhận`.
