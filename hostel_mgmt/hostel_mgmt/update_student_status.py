import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'hostel_db'),
    'autocommit': True
}

def update_status_enum():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Alter the status column to include pending and rejected
        print("Modifying 'status' column in 'students' table...")
        cursor.execute("ALTER TABLE students MODIFY COLUMN status ENUM('active', 'inactive', 'pending', 'rejected') DEFAULT 'active';")
        print("Successfully updated 'status' column in 'students' table.")
        
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        print(f"Error updating database: {e}")

if __name__ == "__main__":
    update_status_enum()
