# Nội Dung Slide & Kịch Bản Demo Bảo Vệ - Module Đơn Hàng, Theo Dõi & Xử Lý Đơn (T3D1C46)

## 1. Nội dung Slide thuyết trình
- **Slide 1: Luồng Trạng Thái Đơn Hàng & Lịch Sử Chuyển Trạng Thái (`order_status_histories`)**:
  - 5 bước chuẩn: `Chờ xác nhận` → `Đã xác nhận` → `Đang chuẩn bị` → `Đang giao` → `Hoàn thành` (và `Đã huỷ`).
  - Phân quyền huỷ đơn chặt chẽ: Khách chỉ được huỷ khi đơn còn `Chờ xác nhận`; Nhân viên huỷ trước `Đang giao` kèm lý do bắt buộc.
- **Slide 2: Theo dõi đơn tự động 15s & Màn hình Nhân viên 3 cột có âm báo**:
  - Trang khách: Tab `Đơn Hàng Của Tôi`, thanh tiến trình tự cập nhật mỗi 15 giây, nút `Đặt lại` nhanh.
  - Trang nhân viên (`admin/orders.html`): Bảng 3 cột (`Đơn Mới`, `Đang Chuẩn Bị`, `Đang Giao`), âm báo đơn mới tự động, in phiếu bếp/giao hàng bằng `window.print()`.

## 2. Kịch bản Demo trực tiếp (2 phút)
1. Mở song song tab Khách (`order-lookup.html`) và tab Nhân viên (`admin/orders.html`).
2. Trên tab Nhân viên, bấm âm báo đơn mới, bấm chuyển nhanh trạng thái đơn từ cột `Đơn Mới` sang `Đang Chuẩn Bị` rồi bấm `🖨️ In phiếu`.
3. Quan sát bên tab Khách thanh tiến trình tự động chuyển trạng thái và hiển thị đầy đủ dòng thời gian lịch sử.
