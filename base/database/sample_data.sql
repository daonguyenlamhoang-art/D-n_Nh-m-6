-- ===============================================================
-- Dữ liệu mẫu NightFood (sample_data.sql) - T3D1F81
-- Seed đầy đủ 6 danh mục và 30 món ăn đêm kèm nhóm tùy chọn (Size/Topping)
-- ===============================================================

USE `food_night_db`;

-- 1. Thêm 6 danh mục món ăn
INSERT INTO `categories` (`id`, `name`, `sort_order`, `is_active`) VALUES
(1, 'Mì và cơm', 1, 1),
(2, 'Đồ chiên & Ăn vặt', 2, 1),
(3, 'Đồ nướng & Nhắm đêm', 3, 1),
(4, 'Đồ uống & Tráng miệng', 4, 1),
(5, 'Combo ăn đêm', 5, 1),
(6, 'Cháo & Súp nóng đêm', 6, 1);

-- 2. Thêm 30 món ăn đêm đa dạng và hấp dẫn (5 món mỗi danh mục)
INSERT INTO `dishes` (`id`, `category_id`, `name`, `description`, `price`, `image_url`, `status`, `is_available`, `is_active`, `is_featured`) VALUES
-- Danh mục 1: Mì và cơm (5 món)
(1, 1, 'Mì trộn xúc xích trứng lòng đào', 'Mì trộn sốt tương đen đậm đà kèm 2 xúc xích nướng, trứng ốp la lòng đào béo ngậy và rau dưa ăn kèm giòn rụm.', 35000, 'https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 1),
(2, 1, 'Cơm đùi gà sốt cay đêm', 'Cơm rang hạt ngọc vàng ruộm ăn kèm đùi gà chiên giòn rưới sốt cay Hàn Quốc ngọt bùi ấm bụng đêm khuya.', 45000, 'https://images.unsplash.com/photo-1626082927389-6cd097cdc6ec?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 1),
(3, 1, 'Mì tôm bò bắp chua cay', 'Tô mì tôm bắp bò tươi thái mỏng, nước dùng chua thanh vị cà chua và cay nồng sate, sưởi ấm dạ dày lúc nửa đêm.', 40000, 'https://images.unsplash.com/photo-1591814468924-caf88d1232e1?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(4, 1, 'Cơm rang dưa bò Hà Nội', 'Cơm rang săn hạt cùng thịt bò xào mềm và dưa cải chua giòn sần sật, kèm bát canh nước bò nóng hổi.', 42000, 'https://images.unsplash.com/photo-1512058564366-18510be2db19?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(5, 1, 'Mì cay hải sản cấp độ đêm', 'Mì Hàn Quốc sợi dai nấu cùng tôm tươi, mực giòn, bò viên và nấm kim châm trong nước dùng kim chi cay nồng.', 48000, 'https://images.unsplash.com/photo-1552611052-33e04de081de?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 1),

-- Danh mục 2: Đồ chiên & Ăn vặt (5 món)
(6, 2, 'Khoai tây chiên lắc phô mai', 'Khoai tây cắt lát chiên vàng giòn tan, phủ lớp bột phô mai hảo hạng mằn mặn thơm lừng, chấm tương cà.', 25000, 'https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(7, 2, 'Gà viên chiên giòn sốt cay ngọt', 'Từng viên thịt gà tươi lọc xương tẩm bột chiên phồng giòn rụm, áo đều lớp sốt chua ngọt cay tê đầu lưỡi.', 30000, 'https://images.unsplash.com/photo-1562967914-608f82629710?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 1),
(8, 2, 'Nem chua rán phố cổ (10 que)', 'Đĩa 10 que nem chua rán vỏ ngoài vàng giòn rụm, nhân bên trong dai dẻo thơm nức, chấm tương ớt sate.', 35000, 'https://images.unsplash.com/photo-1544025162-d76694265947?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(9, 2, 'Xúc xích Đức nướng phô mai', '2 cây xúc xích Đức nướng khói thơm lừng, bên trong đẫm phô mai béo ngậy tan chảy khi cắn từng miếng.', 28000, 'https://images.unsplash.com/photo-1587314168485-3236d6710814?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(10, 2, 'Phô mai que kéo sợi (5 chiếc)', 'Phô mai Mozzarella bọc bột xù chiên vàng ươm, kéo sợi dài béo ngậy cực cuốn cho buổi cày phim đêm.', 30000, 'https://images.unsplash.com/photo-1541592106381-b31e9677c0e5?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),

-- Danh mục 3: Đồ nướng & Nhắm đêm (5 món)
(11, 3, 'Chân gà sả tắc rút xương', 'Chân gà tươi rút xương giòn sần sật ngâm nước sốt chua cay mặn ngọt đậm đà, thơm phức mùi sả tắc và ớt tươi.', 45000, 'https://images.unsplash.com/photo-1527477396000-e27163b481c2?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 1),
(12, 3, 'Xiên thịt heo nướng mật ong (3 xiên)', 'Thịt nạc vai thái vừa miếng ướp mật ong hoa rừng cùng sả tiêu thơm lừng, nướng than hoa xém cạnh đậm vị.', 35000, 'https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(13, 3, 'Cánh gà nướng BBQ mật ong', '4 cánh gà ta ướp sốt BBQ hun khói và mật ong, nướng vàng óng thơm phức, chấm muối ớt xanh.', 48000, 'https://images.unsplash.com/photo-1608039755401-742074f0548d?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(14, 3, 'Bạch tuộc nướng sa tế cay', 'Bạch tuộc tươi giòn sần sật ướp sa tế ớt hiểm nướng than hồng, ăn kèm đậu bắp nướng và rau răm.', 55000, 'https://images.unsplash.com/photo-1565557623262-b51c2513a641?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(15, 3, 'Sụn gà rang muối Hồng Kông', 'Sụn gà giòn rụm chiên vàng xóc cùng lớp muối Hồng Kông thơm mùi sả chiên và lá chanh thái chỉ.', 45000, 'https://images.unsplash.com/photo-1567620832903-9fc6debc209f?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),

-- Danh mục 4: Đồ uống & Tráng miệng (5 món)
(16, 4, 'Trà đào cam sả mát lạnh', 'Trà đào thơm nức hòa quyện vị cam chua dịu, thoang thoảng hương sả ấm áp kèm 3 miếng đào ngâm giòn ngọt.', 20000, 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 1),
(17, 4, 'Trà chanh giã tay hoa nhài', 'Trà nhài thơm ngát kết hợp cùng chanh tươi giã tay nguyên vỏ bung tỏa tinh dầu thơm mát giải ngấy cực đỉnh.', 15000, 'https://images.unsplash.com/photo-1513558161293-cdaf765ed2fd?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(18, 4, 'Sữa chua trân châu đường đen', 'Sữa chua dẻo nhà làm thơm béo kết hợp cùng trân châu nấu đường đen dẻo thơm ấm ngọt, ăn là mê.', 25000, 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(19, 4, 'Trà sữa nướng trân châu hoàng kim', 'Trà sữa nướng caramel thơm ngậy kết hợp trân châu hoàng kim dai giòn, tiếp sức thức đêm học bài.', 28000, 'https://images.unsplash.com/photo-1558857563-b371033873b8?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(20, 4, 'Bánh flan caramel cốt dừa', '2 hộp bánh flan trứng sữa mềm mịn béo thơm, phủ sốt caramel đắng nhẹ và cốt dừa béo ngậy.', 20000, 'https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),

-- Danh mục 5: Combo ăn đêm (5 món)
(21, 5, 'Combo Cú Đêm Vui Vẻ', 'Bao gồm: 01 Gà viên chiên giòn + 01 Khoai tây chiên phô mai + 01 Pepsi mát lạnh. Tiết kiệm 15% so với mua lẻ.', 65000, 'https://images.unsplash.com/photo-1625813506062-0aeb1d7a094b?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 1),
(22, 5, 'Combo Cày Deadline', 'Bao gồm: 01 Mì trộn xúc xích trứng lòng đào + 01 Nem chua rán (5 que) + 01 Trà đào cam sả.', 75000, 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 1),
(23, 5, 'Combo Cú Vọ Đẳng Cấp', 'Bao gồm: 01 Cơm đùi gà sốt cay + 01 Chân gà sả tắc rút xương + 01 Trà chanh giã tay.', 95000, 'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 1),
(24, 5, 'Combo Chiến Hữu Xem Bóng', 'Bao gồm: 01 Chân gà sả tắc + 01 Cánh gà nướng BBQ + 01 Khoai tây chiên + 02 Trà chanh giã tay.', 115000, 'https://images.unsplash.com/photo-1561758033-d89a9ad46330?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(25, 5, 'Combo Đôi Bạn Cú Đêm', 'Bao gồm: 02 Mì trộn xúc xích lòng đào + 01 Phô mai que kéo sợi + 02 Trà đào cam sả.', 120000, 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),

-- Danh mục 6: Cháo & Súp nóng đêm (5 món)
(26, 6, 'Cháo sườn sụn nóng hổi', 'Cháo gạo xay mịn sánh mượt, ngọt lịm từ nước hầm xương với những miếng sườn sụn giòn sần sật, rắc tiêu và quẩy.', 35000, 'https://images.unsplash.com/photo-1541832676-9b763b0239ab?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 1),
(27, 6, 'Cháo gà xé nấm hương đêm', 'Cháo nấu từ nước luộc gà ta ngọt thanh, phủ đầy thịt gà xé phay, nấm hương, hành phi và lá tía tô ấm bụng.', 38000, 'https://images.unsplash.com/photo-1547592166-23ac45744acd?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(28, 6, 'Cháo tim cật nóng sốt', 'Tim và cật heo tươi xào săn cùng hành tỏi rồi đổ vào nồi cháo trắng sánh mịn, thêm tiêu bắc cay nồng.', 40000, 'https://images.unsplash.com/photo-1604908176997-125f25cc6f3d?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(29, 6, 'Súp cua trứng bắc thảo', 'Súp cua sánh đặc với thịt cua tươi, nấm tuyết, ngô ngọt, trứng cút và nửa quả trứng bắc thảo béo bùi.', 35000, 'https://images.unsplash.com/photo-1547592180-85f173990554?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0),
(30, 6, 'Súp gà ngô non nấm hương', 'Bát súp gà nóng hổi thơm dịu mùi dầu mè, đầy ắp gà xé, ngô ngọt Mỹ và nấm hương thái sợi.', 30000, 'https://images.unsplash.com/photo-1578020190125-f4f7c18bc9cb?w=500&auto=format&fit=crop&q=60', 'AVAILABLE', 1, 1, 0);

-- 3. Tùy chọn món ăn (dish_options) phân theo nhóm Size (bắt buộc) và Topping (không bắt buộc)
INSERT INTO `dish_options` (`id`, `dish_id`, `option_group`, `option_name`, `extra_price`, `is_required`, `max_select`, `is_active`) VALUES
(1, 1, 'Size', 'Cỡ vừa (Tiêu chuẩn)', 0, 1, 1, 1),
(2, 1, 'Size', 'Cỡ lớn (+50% mì)', 10000, 1, 1, 1),
(3, 1, 'Topping', 'Thêm 01 trứng ốp la lòng đào', 5000, 0, 3, 1),
(4, 1, 'Topping', 'Thêm 01 xúc xích nướng', 8000, 0, 3, 1),
(5, 1, 'Topping', 'Thêm phô mai tan chảy', 10000, 0, 3, 1),
(6, 2, 'Size', 'Suất tiêu chuẩn', 0, 1, 1, 1),
(7, 2, 'Size', 'Suất đặc biệt thêm cơm', 8000, 1, 1, 1),
(8, 2, 'Topping', 'Thêm sốt cay đặc biệt', 5000, 0, 2, 1),
(9, 6, 'Topping', 'Thêm phô mai gấp đôi', 8000, 0, 1, 1),
(10, 16, 'Size', 'Size M (500ml)', 0, 1, 1, 1),
(11, 16, 'Size', 'Size L (700ml)', 6000, 1, 1, 1),
(12, 16, 'Topping', 'Thêm đào ngâm giòn (2 miếng)', 6000, 0, 2, 1),
(13, 26, 'Topping', 'Thêm quẩy giòn (3 chiếc)', 5000, 0, 2, 1),
(14, 26, 'Topping', 'Thêm ruốc heo nhà làm', 7000, 0, 2, 1);

-- 4. Mã giảm giá mẫu (vouchers)
INSERT INTO `vouchers` (`id`, `code`, `discount_type`, `discount_value`, `min_order_amount`, `max_discount_amount`, `start_at`, `end_at`, `usage_limit`, `used_count`, `is_active`) VALUES
(1, 'DEMKHUYA10', 'percent', 10, 50000, 20000, '2026-01-01 00:00:00', '2027-12-31 23:59:59', 500, 12, 1),
(2, 'NIGHTFOOD15K', 'fixed', 15000, 80000, 15000, '2026-01-01 00:00:00', '2027-12-31 23:59:59', 200, 5, 1);

-- 5. Đánh giá mẫu (reviews) cho các món hot
INSERT INTO `users` (`id`, `full_name`, `username`, `phone`, `password_hash`, `role`, `is_active`, `created_at`) VALUES
(1, 'Khách Hàng Thân Thiết', 'customer1', '0987654321', NULL, 'customer', 1, NOW());

INSERT INTO `reviews` (`user_id`, `dish_id`, `rating`, `comment`, `is_visible`) VALUES
(1, 1, 5, 'Mì trộn rất vừa vị, sốt béo ngậy, giao hàng lúc 1h sáng mà vẫn nóng hổi!', 1),
(1, 21, 5, 'Combo Cú Đêm quá hợp lý cho dân coder trực đêm, gà chiên ráo dầu.', 1),
(1, 2, 5, 'Cơm gà sốt cay thơm ngon, đùi gà to đùng ăn no căng bụng.', 1);

-- 6. Dữ liệu mẫu cho bảng items (CRUD mẫu khởi tạo)
INSERT INTO `items` (`name`, `description`, `price`) VALUES
('Mì trộn xúc xích mẫu', 'Item mẫu kiểm tra kết nối FastAPI + MySQL', 35000),
('Trà đào cam sả mẫu', 'Đồ uống mẫu kiểm tra CRUD base code', 20000);
