# Nội Dung Slide & Kịch Bản Demo Bảo Vệ - Module Giỏ Hàng & Đặt Món Trong Transaction (T3D1C44)

## 1. Nội dung Slide thuyết trình
- **Slide 1: Cơ chế Giỏ hàng & Tính tiền tại Server**:
  - Phân tách dòng giỏ hàng thông minh: Cùng món nhưng khác tuỳ chọn hoặc ghi chú tách dòng riêng; trùng hoàn toàn thì cộng dồn.
  - Ngăn kéo giỏ hàng trượt trên mobile (`.cart-drawer`), sửa ghi chú trực tiếp trong giỏ.
  - Tính tiền hoàn toàn ở Backend: Đơn giá gốc + giá tuỳ chọn, phí ship theo khu vực (`Nội thành`, `Quận lân cận`, `Ngoại thành`), giảm giá khuyến mãi, cảnh báo khi món hết hoặc đổi giá.
- **Slide 2: Đặt món Nguyên tử (Database Transaction) & Chống Gian Lận**:
  - Kiểm tra giờ mở cửa (18:00 - 02:00) và giờ giao mong muốn, lưu snapshot giá + tuỳ chọn vào `order_items`, trừ lượt `vouchers`, xoá giỏ hàng trong 1 transaction.
  - Chống bấm đặt 2 lần và lưu lựa chọn thanh toán cho lần đặt sau.

## 2. Kịch bản Demo trực tiếp (2 phút)
1. Bấm icon `⚡` cạnh nút Giỏ hàng trên Header để mở ngăn kéo giỏ hàng nhanh, sau đó vào `cart.html` sửa ghi chú và số lượng món.
2. Chuyển sang `checkout.html`, chọn nhanh địa chỉ từ `Sổ địa chỉ`, đổi khu vực sang `Thanh Xuân (+15.000đ)`, áp dụng mã `DEMKHUYA10`, chọn giờ giao và bấm `Đặt Món Ngay`.
