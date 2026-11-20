# Nội Dung Slide & Kịch Bản Demo Bảo Vệ - Module Tìm Kiếm, Bộ Lọc & Chi Tiết Món (T3D1C42)

## 1. Nội dung Slide thuyết trình
- **Slide 1: Tìm kiếm Gợi ý Debounce & Bộ lọc đa tiêu chí**:
  - Tìm kiếm theo tên món có gợi ý trực tiếp sau 300ms (debounce), kết hợp lọc danh mục, khoảng giá, trạng thái còn bán và sắp xếp (giá tăng/giảm, bán chạy, đánh giá cao), phân trang.
- **Slide 2: Chi tiết món, Chọn Tuỳ chọn động & Món đã xem gần đây**:
  - Phân nhóm tuỳ chọn `Size` (bắt buộc chọn 1) và `Topping` (chọn nhiều), tự động tính lại giá ngay khi tích chọn, lưu lịch sử `Món đã xem gần đây` vào `localStorage`.

## 2. Kịch bản Demo trực tiếp (2 phút)
1. Tại `dishes.html`, gõ `"mì"` vào ô tìm kiếm để hiển thị danh sách gợi ý nhanh kèm ảnh và giá; thử lọc mức giá `30.000đ - 50.000đ` và sắp xếp `Giá: Thấp → Cao`.
2. Mở chi tiết món `Mì trộn xúc xích trứng lòng đào`, chọn `Cỡ lớn (+10.000đ)` và tích 2 loại topping, nhập ghi chú `"Ít cay"` để thấy tổng tiền tự động tăng theo lựa chọn rồi bấm `Thêm vào giỏ hàng`.
