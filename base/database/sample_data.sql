-- ===============================================================
-- Dữ liệu mẫu NightFood (sample_data.sql)
-- Chú ý: Không chứa tài khoản hoặc mật khẩu admin theo yêu cầu NFR-10
-- ===============================================================

USE `food_night_db`;

-- 1. Thêm danh mục món ăn
INSERT INTO `categories` (`id`, `name`, `is_active`) VALUES
(1, 'Mì và cơm', 1),
(2, 'Đồ chiên & Ăn vặt', 1),
(3, 'Đồ nướng & Nhắm đêm', 1),
(4, 'Đồ uống & Tráng miệng', 1),
(5, 'Combo ăn đêm', 1);

-- 2. Thêm món ăn đêm đa dạng và hấp dẫn
INSERT INTO `dishes` (`id`, `category_id`, `name`, `description`, `price`, `image_url`, `is_available`, `is_active`) VALUES
-- Danh mục 1: Mì và cơm
(1, 1, 'Mì trộn xúc xích trứng lòng đào', 'Mì trộn sốt tương đen đậm đà kèm 2 xúc xích nướng, trứng ốp la lòng đào béo ngậy và rau dưa ăn kèm giòn rụm.', 35000, 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=500&auto=format&fit=crop&q=60', 1, 1),
(2, 1, 'Cơm đùi gà sốt cay đêm', 'Cơm rang hạt ngọc vàng ruộm ăn kèm đùi gà chiên giòn rưới sốt cay Hàn Quốc ngọt bùi ấm bụng đêm khuya.', 45000, 'https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=500&auto=format&fit=crop&q=60', 1, 1),
(3, 1, 'Mì tôm bò bắp chua cay', 'Tô mì tôm bắp bò tươi thái mỏng, nước dùng chua thanh vị cà chua và cay nồng sate, sưởi ấm dạ dày lúc nửa đêm.', 40000, 'https://images.unsplash.com/photo-1591814468924-caf88d1232e1?w=500&auto=format&fit=crop&q=60', 1, 1),
(4, 1, 'Cháo sườn sụn nóng hổi', 'Cháo gạo xay mịn sánh mượt, ngọt lịm từ nước hầm xương với những miếng sườn sụn giòn sần sật, rắc thêm tiêu và hành phi.', 35000, 'https://images.unsplash.com/photo-1541832676-9b763b0239ab?w=500&auto=format&fit=crop&q=60', 1, 1),

-- Danh mục 2: Đồ chiên & Ăn vặt
(5, 2, 'Khoai tây chiên lắc phô mai', 'Khoai tây cắt lát chiên vàng giòn tan, phủ lớp bột phô mai hảo hạng mằn mặn thơm lừng, chấm tương cà hoặc sốt mayonnaise.', 25000, 'https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=500&auto=format&fit=crop&q=60', 1, 1),
(6, 2, 'Gà viên chiên giòn sốt cay ngọt', 'Từng viên thịt gà tươi lọc xương tẩm bột chiên phồng giòn rụm, áo đều lớp sốt chua ngọt cay tê đầu lưỡi.', 30000, 'https://images.unsplash.com/photo-1562967914-608f82629710?w=500&auto=format&fit=crop&q=60', 1, 1),
(7, 2, 'Nem chua rán phố cổ', 'Đĩa 10 que nem chua rán vỏ ngoài vàng giòn rụm, nhân bên trong dai dẻo thơm nức, chấm tương ớt sate cay nồng chuẩn vị.', 35000, 'https://images.unsplash.com/photo-1544025162-d76694265947?w=500&auto=format&fit=crop&q=60', 1, 1),
(8, 2, 'Xúc xích Đức nướng phô mai', '2 cây xúc xích Đức nướng khói thơm lừng, bên trong đẫm phô mai béo ngậy tan chảy khi cắn từng miếng.', 28000, 'https://images.unsplash.com/photo-1587314168485-3236d6710814?w=500&auto=format&fit=crop&q=60', 1, 1),

-- Danh mục 3: Đồ nướng & Nhắm đêm
(9, 3, 'Chân gà sả tắc rút xương', 'Chân gà tươi rút xương giòn sần sật ngâm nước sốt chua cay mặn ngọt đậm đà, thơm phức mùi sả tắc và ớt tươi.', 45000, 'https://images.unsplash.com/photo-1527477396000-e27163b481c2?w=500&auto=format&fit=crop&q=60', 1, 1),
(10, 3, 'Xiên thịt heo nướng mật ong (3 xiên)', 'Thịt nạc vai thái vừa miếng ướp mật ong hoa rừng cùng sả tiêu thơm lừng, nướng than hoa xém cạnh đậm vị.', 35000, 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=500&auto=format&fit=crop&q=60', 1, 1),

-- Danh mục 4: Đồ uống & Tráng miệng
(11, 4, 'Trà đào cam sả mát lạnh', 'Trà đào thơm nức hòa quyện vị cam chua dịu, thoang thoảng hương sả ấm áp kèm 3 miếng đào ngâm giòn ngọt.', 20000, 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=500&auto=format&fit=crop&q=60', 1, 1),
(12, 4, 'Trà chanh giã tay hoa nhài', 'Trà nhài thơm ngát kết hợp cùng chanh tươi giã tay nguyên vỏ bung tỏa tinh dầu thơm mát giải ngấy cực đỉnh.', 15000, 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500&auto=format&fit=crop&q=60', 1, 1),
(13, 4, 'Sữa chua trân châu đường đen', 'Sữa chua dẻo nhà làm thơm béo kết hợp cùng trân châu nấu đường đen dẻo thơm ấm ngọt, ăn là mê.', 25000, 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=500&auto=format&fit=crop&q=60', 1, 1),

-- Danh mục 5: Combo ăn đêm
(14, 5, 'Combo Cú Đêm Vui Vẻ', 'Bao gồm: 01 Gà viên chiên giòn + 01 Khoai tây chiên phô mai + 01 Pepsi mát lạnh. Tiết kiệm 15% so với mua lẻ.', 65000, 'https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?w=500&auto=format&fit=crop&q=60', 1, 1),
(15, 5, 'Combo Cày Deadline', 'Bao gồm: 01 Mì trộn xúc xích trứng lòng đào + 01 Nem chua rán (5 que) + 01 Trà đào cam sả. Cung cấp năng lượng cày xuyên đêm.', 75000, 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500&auto=format&fit=crop&q=60', 1, 1),
(16, 5, 'Combo Cú Vọ Đẳng Cấp', 'Bao gồm: 01 Cơm đùi gà sốt cay + 01 Chân gà sả tắc rút xương + 01 Trà chanh giã tay.', 95000, 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60', 1, 1);

-- 3. Tùy chọn món ăn (dish_options)
INSERT INTO `dish_options` (`id`, `dish_id`, `option_name`, `extra_price`, `is_active`) VALUES
(1, 1, 'Thêm 01 trứng ốp la lòng đào', 5000, 1),
(2, 1, 'Thêm 01 xúc xích nướng', 8000, 1),
(3, 1, 'Thêm phô mai tan chảy', 10000, 1),
(4, 2, 'Thêm sốt cay đặc biệt', 5000, 1),
(5, 5, 'Thêm phô mai gấp đôi', 8000, 1),
(6, 11, 'Thêm đào ngâm giòn', 6000, 1);

-- 4. Mã giảm giá mẫu (vouchers)
INSERT INTO `vouchers` (`id`, `code`, `discount_type`, `discount_value`, `min_order_amount`, `max_discount_amount`, `start_at`, `end_at`, `usage_limit`, `used_count`, `is_active`) VALUES
(1, 'DEMKHUYA10', 'percent', 10, 50000, 20000, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 500, 12, 1),
(2, 'NIGHTFOOD15K', 'fixed', 15000, 80000, 15000, '2026-01-01 00:00:00', '2026-12-31 23:59:59', 200, 5, 1);

-- 5. Đánh giá mẫu (reviews) cho các món hot
INSERT INTO `users` (`id`, `full_name`, `username`, `phone`, `password_hash`, `role`, `is_active`, `created_at`) VALUES
(1, 'Khách Hàng Thân Thiết', 'customer1', '0987654321', NULL, 'customer', 1, NOW());

INSERT INTO `reviews` (`user_id`, `dish_id`, `rating`, `comment`, `is_visible`) VALUES
(1, 1, 5, 'Mì trộn rất vừa vị, sốt béo ngậy, giao hàng lúc 1h sáng mà vẫn nóng hổi!', 1),
(1, 14, 5, 'Combo Cú Đêm quá hợp lý cho dân coder trực đêm, gà chiên ráo dầu.', 1),
(1, 2, 5, 'Cơm gà sốt cay thơm ngon, đùi gà to đùng ăn no căng bụng.', 1);
