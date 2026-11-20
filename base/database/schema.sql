-- ===============================================================
-- NightFood - Cơ sở dữ liệu quán bán đồ ăn đêm trực tuyến
-- Hệ quản trị: MySQL / MariaDB (utf8mb4)
-- Đặc tả SRS v1.2: Đầy đủ 13 bảng theo ERD chung
-- ===============================================================

CREATE DATABASE IF NOT EXISTS `food_night_db` 
  CHARACTER SET utf8mb4 
  COLLATE utf8mb4_unicode_ci;

USE `food_night_db`;

-- Tắt kiểm tra khóa ngoại để drop các bảng cũ an toàn khi khởi tạo
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `chat_messages`;
DROP TABLE IF EXISTS `reviews`;
DROP TABLE IF EXISTS `order_status_histories`;
DROP TABLE IF EXISTS `order_items`;
DROP TABLE IF EXISTS `orders`;
DROP TABLE IF EXISTS `vouchers`;
DROP TABLE IF EXISTS `cart_items`;
DROP TABLE IF EXISTS `carts`;
DROP TABLE IF EXISTS `dish_options`;
DROP TABLE IF EXISTS `dishes`;
DROP TABLE IF EXISTS `categories`;
DROP TABLE IF EXISTS `addresses`;
DROP TABLE IF EXISTS `users`;
DROP TABLE IF EXISTS `items`; -- Bảng ví dụ cũ nếu có

SET FOREIGN_KEY_CHECKS = 1;

-- 1. Bảng users: Tài khoản Admin và khách hàng
CREATE TABLE `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `full_name` VARCHAR(100) NULL,
  `username` VARCHAR(50) UNIQUE NULL,
  `phone` VARCHAR(10) NULL,
  `password_hash` VARCHAR(255) NULL,
  `role` ENUM('admin', 'customer') NOT NULL DEFAULT 'customer',
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX `idx_users_username` (`username`),
  INDEX `idx_users_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Bảng addresses: Sổ địa chỉ giao hàng của khách
CREATE TABLE `addresses` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `recipient_name` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(10) NOT NULL,
  `address_line` VARCHAR(255) NOT NULL,
  `area` VARCHAR(100) DEFAULT 'Nội thành',
  `is_default` BOOLEAN DEFAULT FALSE,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Bảng categories: Danh mục món ăn
CREATE TABLE `categories` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(100) NOT NULL UNIQUE,
  `sort_order` INT NOT NULL DEFAULT 0,
  `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
  INDEX `idx_categories_active` (`is_active`),
  INDEX `idx_categories_sort` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 4. Bảng dishes: Món ăn, đồ uống, combo ăn đêm
CREATE TABLE `dishes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `category_id` INT NOT NULL,
  `name` VARCHAR(150) NOT NULL,
  `description` TEXT NULL,
  `price` INT NOT NULL,
  `image_url` VARCHAR(500) NULL,
  `status` VARCHAR(20) NOT NULL DEFAULT 'AVAILABLE',
  `is_available` BOOLEAN DEFAULT TRUE,
  `is_active` BOOLEAN DEFAULT TRUE,
  `is_featured` BOOLEAN DEFAULT FALSE,
  `is_combo` BOOLEAN DEFAULT FALSE,
  `combo_items_json` TEXT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`category_id`) REFERENCES `categories`(`id`) ON DELETE RESTRICT,
  INDEX `idx_dishes_category_active` (`category_id`, `is_active`),
  INDEX `idx_dishes_available` (`is_available`),
  INDEX `idx_dishes_featured` (`is_featured`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. Bảng dish_options: Tùy chọn món (Size, Topping: thêm trứng, thêm phô mai, ...)
CREATE TABLE `dish_options` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `dish_id` INT NOT NULL,
  `option_group` VARCHAR(50) NOT NULL DEFAULT 'Topping',
  `option_name` VARCHAR(100) NOT NULL,
  `extra_price` INT NOT NULL DEFAULT 0,
  `is_required` BOOLEAN DEFAULT FALSE,
  `max_select` INT NOT NULL DEFAULT 1,
  `is_active` BOOLEAN DEFAULT TRUE,
  FOREIGN KEY (`dish_id`) REFERENCES `dishes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. Bảng carts: Giỏ hàng
CREATE TABLE `carts` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL,
  `guest_token` VARCHAR(64) UNIQUE NULL,
  `status` ENUM('active', 'checked_out') DEFAULT 'active',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. Bảng cart_items: Dòng món trong giỏ hàng
CREATE TABLE `cart_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `cart_id` INT NOT NULL,
  `dish_id` INT NOT NULL,
  `dish_option_id` INT NULL,
  `selected_options_json` TEXT NULL,
  `note` VARCHAR(255) NULL,
  `quantity` INT NOT NULL DEFAULT 1,
  FOREIGN KEY (`cart_id`) REFERENCES `carts`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`dish_id`) REFERENCES `dishes`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`dish_option_id`) REFERENCES `dish_options`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. Bảng vouchers: Mã giảm giá
CREATE TABLE `vouchers` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `code` VARCHAR(30) UNIQUE NOT NULL,
  `discount_type` ENUM('fixed', 'percent') NOT NULL,
  `discount_value` INT NOT NULL,
  `min_order_amount` INT NOT NULL DEFAULT 0,
  `max_discount_amount` INT NULL,
  `start_at` DATETIME NOT NULL,
  `end_at` DATETIME NOT NULL,
  `usage_limit` INT NULL,
  `used_count` INT DEFAULT 0,
  `is_active` BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. Bảng orders: Đơn đặt hàng NightFood
CREATE TABLE `orders` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `order_code` VARCHAR(30) UNIQUE NOT NULL,
  `user_id` INT NULL,
  `guest_token` VARCHAR(64) NULL,
  `address_id` INT NULL,
  `voucher_id` INT NULL,
  `customer_name` VARCHAR(100) NOT NULL,
  `phone` VARCHAR(10) NOT NULL,
  `customer_email` VARCHAR(150) NULL,
  `address` VARCHAR(255) NOT NULL,
  `area` VARCHAR(100) DEFAULT 'Nội thành',
  `note` VARCHAR(500) NULL,
  `desired_delivery_time` VARCHAR(100) NULL,
  `subtotal` INT NOT NULL DEFAULT 0,
  `shipping_fee` INT NOT NULL DEFAULT 0,
  `discount_amount` INT NOT NULL DEFAULT 0,
  `total_amount` INT NOT NULL DEFAULT 0,
  `payment_method` VARCHAR(30) DEFAULT 'COD',
  `payment_confirmed` BOOLEAN DEFAULT FALSE,
  `status` VARCHAR(30) DEFAULT 'pending',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`address_id`) REFERENCES `addresses`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`voucher_id`) REFERENCES `vouchers`(`id`) ON DELETE SET NULL,
  INDEX `idx_orders_code` (`order_code`),
  INDEX `idx_orders_phone` (`phone`),
  INDEX `idx_orders_guest_token` (`guest_token`),
  INDEX `idx_orders_status` (`status`),
  INDEX `idx_orders_created` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. Bảng order_items: Chi tiết các món trong đơn hàng (snapshot tên và giá)
CREATE TABLE `order_items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `order_id` INT NOT NULL,
  `dish_id` INT NOT NULL,
  `dish_option_id` INT NULL,
  `dish_name` VARCHAR(150) NOT NULL,
  `option_name` VARCHAR(255) NULL,
  `options_json` TEXT NULL,
  `note` VARCHAR(255) NULL,
  `quantity` INT NOT NULL DEFAULT 1,
  `unit_price` INT NOT NULL DEFAULT 0,
  `subtotal` INT NOT NULL DEFAULT 0,
  FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`dish_id`) REFERENCES `dishes`(`id`) ON DELETE RESTRICT,
  FOREIGN KEY (`dish_option_id`) REFERENCES `dish_options`(`id`) ON DELETE SET NULL,
  INDEX `idx_order_items_order_id` (`order_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. Bảng order_status_histories: Lịch sử chuyển trạng thái đơn
CREATE TABLE `order_status_histories` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `order_id` INT NOT NULL,
  `changed_by` INT NULL,
  `old_status` VARCHAR(30) NULL,
  `new_status` VARCHAR(30) NOT NULL,
  `note` VARCHAR(255) NULL,
  `changed_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`changed_by`) REFERENCES `users`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. Bảng reviews: Đánh giá món ăn
CREATE TABLE `reviews` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NOT NULL,
  `dish_id` INT NOT NULL,
  `rating` TINYINT NOT NULL,
  `comment` TEXT NULL,
  `is_visible` BOOLEAN DEFAULT TRUE,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`dish_id`) REFERENCES `dishes`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. Bảng chat_messages: Tin nhắn hỗ trợ
CREATE TABLE `chat_messages` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` INT NULL,
  `order_id` INT NULL,
  `sender_type` ENUM('customer', 'admin') NOT NULL,
  `guest_token` VARCHAR(64) NULL,
  `message` TEXT NOT NULL,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`order_id`) REFERENCES `orders`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Bảng items: CRUD mẫu cho bước khởi tạo base code
CREATE TABLE IF NOT EXISTS `items` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `name` VARCHAR(255) NOT NULL,
  `description` TEXT NULL,
  `price` DECIMAL(12, 2) NOT NULL DEFAULT 0,
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
