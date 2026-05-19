-- ============================================================
-- Hostel Management System - Database Schema
-- Run this file in MySQL to set up the database
-- ============================================================

-- -------------------------------------------------------
-- Table: rooms
-- Stores all hostel rooms
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    room_number VARCHAR(10) NOT NULL UNIQUE,
    floor INT NOT NULL,
    capacity INT NOT NULL DEFAULT 2,
    current_occupancy INT NOT NULL DEFAULT 0,
    room_type VARCHAR(50) DEFAULT 'double',
    status VARCHAR(50) DEFAULT 'available',
    monthly_fee DECIMAL(10,2) NOT NULL DEFAULT 5000.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------
-- Table: admins
-- Stores admin login credentials
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS admins (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    reset_token VARCHAR(255) DEFAULT NULL,
    reset_token_expiry TIMESTAMP DEFAULT NULL,
    must_change_password BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- -------------------------------------------------------
-- Table: students
-- Stores student details (room_id is foreign key)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS students (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    mobile_number VARCHAR(15),
    roll_number VARCHAR(30) UNIQUE,
    course VARCHAR(100),
    year_of_study INT,
    room_id INT,
    join_date DATE DEFAULT (CURRENT_DATE),
    status VARCHAR(50) DEFAULT 'active',
    profile_image VARCHAR(255) DEFAULT 'default.png',
    parent_number VARCHAR(15),
    meal_preference VARCHAR(50) DEFAULT 'veg',
    dob DATE,
    gender VARCHAR(20),
    aadhaar_number VARCHAR(20),
    blood_group VARCHAR(10),
    parent_name VARCHAR(100),
    parent_relation VARCHAR(50),
    college_name VARCHAR(150),
    branch VARCHAR(100),
    permanent_address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    pincode VARCHAR(20),
    reset_token VARCHAR(255) DEFAULT NULL,
    reset_token_expiry TIMESTAMP DEFAULT NULL,
    must_change_password BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL
);

-- -------------------------------------------------------
-- Table: fees
-- Tracks fee payment status per student per month
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS fees (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    month VARCHAR(20) NOT NULL,       -- e.g., "June 2025"
    year INT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    payment_date DATE,
    due_date DATE NOT NULL,
    remarks TEXT,
    reminder_7_days_sent BOOLEAN DEFAULT FALSE,
    reminder_3_days_sent BOOLEAN DEFAULT FALSE,
    reminder_0_days_sent BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- -------------------------------------------------------
-- Table: complaints
-- Students submit complaints; admin updates status
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS complaints (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50) DEFAULT 'other',
    status VARCHAR(50) DEFAULT 'open',
    admin_response TEXT,
    assigned_to VARCHAR(100) DEFAULT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- -------------------------------------------------------
-- Table: notices
-- Admin posts notices visible to all students
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS notices (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    priority VARCHAR(50) DEFAULT 'medium',
    posted_by INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (posted_by) REFERENCES admins(id) ON DELETE CASCADE
);

-- -------------------------------------------------------
-- Table: student_activity_logs
-- Tracks log entries for user activity
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS student_activity_logs (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    action VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- -------------------------------------------------------
-- Table: receipts
-- Tracks generated PDF receipts for fee records
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS receipts (
    id SERIAL PRIMARY KEY,
    fee_id INT NOT NULL,
    receipt_url VARCHAR(255) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (fee_id) REFERENCES fees(id) ON DELETE CASCADE
);

-- -------------------------------------------------------
-- Table: sms_logs
-- Tracks sent SMS notifications
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS sms_logs (
    id SERIAL PRIMARY KEY,
    student_id INT,
    mobile_number VARCHAR(15) NOT NULL,
    message TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'sent',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
);

-- -------------------------------------------------------
-- Table: settings
-- Stores API keys and global configurations
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS settings (
    setting_key VARCHAR(50) PRIMARY KEY,
    setting_value TEXT
);

-- Initialize setting for Fast2SMS API Key
INSERT INTO settings (setting_key, setting_value) VALUES ('fast2sms_api_key', '') ON CONFLICT (setting_key) DO NOTHING;

-- ============================================================
-- SEED DATA: Insert sample rooms
-- ============================================================
INSERT INTO rooms (room_number, floor, capacity, room_type, monthly_fee) VALUES
('101', 1, 1, 'single', 6000.00),
('102', 1, 2, 'double', 4500.00),
('103', 1, 2, 'double', 4500.00),
('201', 2, 2, 'double', 5000.00),
('202', 2, 3, 'triple', 3500.00),
('203', 2, 1, 'single', 6000.00),
('301', 3, 2, 'double', 5500.00),
('302', 3, 3, 'triple', 4000.00)
ON CONFLICT (room_number) DO NOTHING;

-- ============================================================
-- SEED DATA: Insert default admin
-- Password: admin123 (bcrypt hashed - will be re-created by app)
-- ============================================================
-- NOTE: The app.py will create the admin on first run automatically.
-- This is just a placeholder.
-- ============================================================

-- ============================================================
-- Table: transactions
-- Stores all financial records (Income/Expense)
-- ============================================================
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    type VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    remarks VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- Table: fee_receipts
-- Tracks generated fee receipts
-- ============================================================
CREATE TABLE IF NOT EXISTS fee_receipts (
    id SERIAL PRIMARY KEY,
    receipt_number VARCHAR(50) UNIQUE,
    student_id INT,
    student_name VARCHAR(100),
    room_number VARCHAR(20),
    amount DECIMAL(10,2),
    payment_type VARCHAR(50),
    payment_mode VARCHAR(50),
    period VARCHAR(50),
    remarks TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE SET NULL
);

-- ============================================================
-- Table: daily_menus
-- Tracks food menus for each day and slot
-- ============================================================
CREATE TABLE IF NOT EXISTS daily_menus (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    meal_slot VARCHAR(50) NOT NULL,
    meal_type VARCHAR(50) NOT NULL,
    items TEXT NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE,
    UNIQUE (date, meal_slot, meal_type)
);

-- ============================================================
-- Table: food_optouts
-- Tracks student food opt-outs
-- ============================================================
CREATE TABLE IF NOT EXISTS food_optouts (
    id SERIAL PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    breakfast BOOLEAN DEFAULT FALSE,
    lunch BOOLEAN DEFAULT FALSE,
    dinner BOOLEAN DEFAULT FALSE,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE (student_id, date)
);


-- Update schema for existing databases
ALTER TABLE admins ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255);
ALTER TABLE admins ADD COLUMN IF NOT EXISTS reset_token_expiry TIMESTAMP;
ALTER TABLE admins ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;
ALTER TABLE students ADD COLUMN IF NOT EXISTS reset_token VARCHAR(255);
ALTER TABLE students ADD COLUMN IF NOT EXISTS reset_token_expiry TIMESTAMP;
ALTER TABLE students ADD COLUMN IF NOT EXISTS must_change_password BOOLEAN DEFAULT FALSE;
