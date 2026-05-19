import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('DB_HOST', 'localhost'), 
    user=os.getenv('DB_USER', 'root'), 
    password=os.getenv('DB_PASSWORD', ''), 
    dbname=os.getenv('DB_NAME', 'hostel_db'), 
    
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS fee_receipts (
    id INT AUTO_INCREMENT PRIMARY KEY,
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
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS daily_menus (
    id INT AUTO_INCREMENT PRIMARY KEY,
    date DATE NOT NULL,
    meal_slot ENUM('breakfast', 'lunch', 'dinner') NOT NULL,
    meal_type ENUM('veg', 'non-veg') NOT NULL,
    items TEXT NOT NULL,
    is_locked BOOLEAN DEFAULT FALSE,
    UNIQUE KEY unique_menu (date, meal_slot, meal_type)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS food_optouts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    date DATE NOT NULL,
    breakfast BOOLEAN DEFAULT FALSE,
    lunch BOOLEAN DEFAULT FALSE,
    dinner BOOLEAN DEFAULT FALSE,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
    UNIQUE KEY unique_optout (student_id, date)
)
""")

print("Missing tables created.")
cursor.close()
conn.close()
