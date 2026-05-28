import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'dbname': os.getenv('DB_NAME', 'postgres'),
    'port': os.getenv('DB_PORT', '5432')
}

if DB_CONFIG['host'] != 'localhost':
    DB_CONFIG['sslmode'] = 'require'

try:
    print("Connecting to database...")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()

    print("Creating meal_feedback table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meal_feedback (
        id SERIAL PRIMARY KEY,
        student_id INT NOT NULL,
        date DATE NOT NULL,
        meal_slot VARCHAR(50) NOT NULL,
        rating INT,
        like_status VARCHAR(20),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
        UNIQUE (student_id, date, meal_slot)
    );
    """)

    print("Creating kitchen_announcements table...")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS kitchen_announcements (
        id SERIAL PRIMARY KEY,
        title VARCHAR(200) NOT NULL,
        content TEXT,
        type VARCHAR(50) DEFAULT 'update', 
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    print("Tables created successfully!")
    cursor.close()
    conn.close()
except Exception as e:
    print(f"Database error: {e}")
