import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'hostel_db'),
    'autocommit': True
}

def create_table():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS online_payments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fee_id INT NOT NULL,
            student_id INT NOT NULL,
            razorpay_order_id VARCHAR(255) NOT NULL,
            razorpay_payment_id VARCHAR(255),
            razorpay_signature VARCHAR(255),
            amount DECIMAL(10,2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'INR',
            status ENUM('created', 'successful', 'failed') DEFAULT 'created',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (fee_id) REFERENCES fees(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        );
        """)
        
        print("Successfully created 'online_payments' table.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_table()
