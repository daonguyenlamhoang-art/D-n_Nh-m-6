# Nội Dung Slide & Kịch Bản Demo Bảo Vệ - Module Khuyến Mãi, Đánh Giá, Chat & Dashboard Admin (T3D1C48)

## 1. Nội dung Slide thuyết trình
- **Slide 1: Mã giảm giá (`vouchers`), Đánh giá món (`reviews`) & Chat trực tuyến (`chat_messages`)**:
  - Mã giảm giá theo `%` hoặc số tiền cố định, kiểm tra không phân biệt hoa thường, tự động trừ lượt khi đặt đơn thành công.
  - Khách đánh giá từng món 1 lần sau khi đơn `Hoàn thành`; cửa hàng phản hồi đánh giá và ẩn đánh giá vi phạm.
  - Khung chat nổi cho khách và trang chat 2 cột cho nhân viên, tự động polling tin nhắn mới mỗi 3 giây (`since = id tin cuối`).
- **Slide 2: Dashboard Thống kê Admin (Chart.js)**:
  - Biểu đồ doanh thu theo ngày/tháng, biểu đồ tỷ lệ đơn theo trạng thái, top món bán chạy, điểm đánh giá trung bình và tổng số mã giảm giá đã dùng.

## 2. Kịch bản Demo trực tiếp (2 phút)
1. Bấm nút Chat nổi `💬` ở góc dưới trang khách gửi tin nhắn, mở `admin/chat.html` xem số tin chưa đọc và bấm trả lời ngay.
2. Tại đơn đã `Hoàn thành` trên `order-lookup.html`, gửi đánh giá 5 sao rồi vào `admin/vouchers.html` trả lời đánh giá đó.
3. Mở `admin/dashboard.html`, lọc khoảng thời gian và trình chiếu biểu đồ Chart.js doanh thu & trạng thái đơn.
