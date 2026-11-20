# Nội Dung Slide & Kịch Bản Demo Bảo Vệ - Module Menu & Quản Trị Thực Đơn (T3D1C40)

## 1. Nội dung Slide thuyết trình
- **Slide 1: Kiến trúc Module Menu & Database (`categories`, `dishes`, `dish_options`)**:
  - 6 danh mục chuẩn đồ ăn đêm, 30 món ăn, phân nhóm tuỳ chọn `Size` (bắt buộc) và `Topping` (chọn nhiều).
  - Ràng buộc toàn vẹn: Chặn xoá danh mục còn món; món đã phát sinh trong đơn hàng chỉ chuyển sang trạng thái `Ẩn` (`HIDDEN`).
- **Slide 2: Giao diện Thực đơn & Quản trị Menu**:
  - Trang chủ với thanh danh mục dính trên cùng (Sticky Nav), cuộn mượt tới từng danh mục, làm mờ món hết hàng.
  - Trang Admin kéo thả sắp xếp danh mục, upload ảnh món ăn, bật/tắt báo hết món nhanh trong ngày và đánh dấu món nổi bật.

## 2. Kịch bản Demo trực tiếp (2 phút)
1. Mở trang chủ `index.html`, bấm thanh danh mục dính trên cùng để cuộn tới từng nhóm món.
2. Vào `admin/categories.html`, kéo thả hoặc bấm nút Lên/Xuống đổi thứ tự danh mục, thử bấm Xoá danh mục đang có món để thấy thông báo chặn bảo vệ dữ liệu.
3. Vào `admin/dishes.html`, bấm báo hết món nhanh 1 món và quay lại trang khách kiểm tra món đó lập tức hiện mờ `TẠM HẾT MÓN`.
