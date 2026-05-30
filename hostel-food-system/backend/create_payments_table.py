import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def create_table():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            dbname=os.getenv('DB_NAME', 'hostel_db'),
            port=os.getenv('DB_PORT', '5432'),
            sslmode=os.getenv('DB_SSLMODE', 'prefer')
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS online_payments (
            id SERIAL PRIMARY KEY,
            fee_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            razorpay_order_id VARCHAR(255) NOT NULL,
            razorpay_payment_id VARCHAR(255),
            razorpay_signature VARCHAR(255),
            amount DECIMAL(10,2) NOT NULL,
            currency VARCHAR(10) DEFAULT 'INR',
            status VARCHAR(50) DEFAULT 'created',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fee_id) REFERENCES fees(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        );
        """)
        
        print("Successfully created 'online_payments' table for PostgreSQL.")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating table: {e}")

if __name__ == "__main__":
    create_table()
