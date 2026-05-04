-- =====================================================
-- Lost & Found Database Setup Script
-- Run this in MySQL before starting the app
-- =====================================================

-- Create database (if not exists)
CREATE DATABASE IF NOT EXISTS lost_found_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE lost_found_db;

-- =====================================================
-- USERS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS users (
    user_id      INT AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100)  NOT NULL,
    email        VARCHAR(255)  NOT NULL UNIQUE,
    password     VARCHAR(255)  NOT NULL,
    phone        VARCHAR(20)   DEFAULT NULL,
    role         ENUM('USER', 'ADMIN') DEFAULT 'USER',
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role  (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- ITEMS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS items (
    item_id      INT AUTO_INCREMENT PRIMARY KEY,
    title        VARCHAR(255)  NOT NULL,
    description  TEXT          DEFAULT NULL,
    category     ENUM('LOST', 'FOUND') NOT NULL,
    location     VARCHAR(255)  DEFAULT NULL,
    date         DATE          NOT NULL,
    image_url    VARCHAR(500)  DEFAULT NULL,
    user_id      INT           NOT NULL,
    status       ENUM('ACTIVE', 'RESOLVED') DEFAULT 'ACTIVE',
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_category (category),
    INDEX idx_status    (status),
    INDEX idx_user_id   (user_id),
    INDEX idx_created   (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- CLAIMS TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS claims (
    claim_id     INT AUTO_INCREMENT PRIMARY KEY,
    item_id      INT           NOT NULL,
    claimer_id   INT           NOT NULL,
    message      TEXT          DEFAULT NULL,
    status       ENUM('PENDING', 'ACCEPTED', 'REJECTED') DEFAULT 'PENDING',
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (item_id)   REFERENCES items(item_id)   ON DELETE CASCADE,
    FOREIGN KEY (claimer_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_item_id    (item_id),
    INDEX idx_claimer_id (claimer_id),
    INDEX idx_status     (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- NOTIFICATIONS TABLE (for email notifications)
-- =====================================================
CREATE TABLE IF NOT EXISTS notifications (
    notif_id     INT AUTO_INCREMENT PRIMARY KEY,
    user_id      INT           NOT NULL,
    type         VARCHAR(50)   NOT NULL,
    title        VARCHAR(255)  NOT NULL,
    message      TEXT          NOT NULL,
    reference_id INT           DEFAULT NULL,
    is_read      BOOLEAN       DEFAULT FALSE,
    created_at   TIMESTAMP     DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id  (user_id),
    INDEX idx_is_read  (is_read),
    INDEX idx_created  (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- INSERT DEFAULT ADMIN USER
-- Password: admin123
-- =====================================================
INSERT INTO users (name, email, password, role) VALUES
('Administrator', 'admin@lostandfound.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NhQ7zX4Q3V7qGe', 'ADMIN')
ON DUPLICATE KEY UPDATE name = name;

-- =====================================================
-- SAMPLE DATA (Optional - for testing)
-- =====================================================
-- Uncomment the following lines to insert sample data

/*
INSERT INTO users (name, email, password, phone) VALUES
('John Doe',    'john@example.com',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NhQ7zX4Q3V7qGe', '+1234567890'),
('Jane Smith',  'jane@example.com',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.NhQ7zX4Q3V7qGe', '+0987654321')
ON DUPLICATE KEY UPDATE name = name;

INSERT INTO items (title, description, category, location, date, user_id, status) VALUES
('Blue Wallet',    'Leather wallet with student ID inside',     'LOST',  'Library entrance',  CURDATE(), 2, 'ACTIVE'),
('Keys',           'Car keys with a red keychain',              'FOUND', 'Parking lot B',     CURDATE(), 3, 'ACTIVE'),
('Black Phone',    'iPhone 13 with blue case',                 'LOST',  'Cafeteria',        CURDATE(), 2, 'ACTIVE');

INSERT INTO claims (item_id, claimer_id, message, status) VALUES
(1, 3, 'This is my wallet! It has my student ID with number 2024-1234.', 'PENDING');
*/
