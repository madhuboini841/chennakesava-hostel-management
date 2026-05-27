import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'hostel_db'),
    'autocommit': True
}

def update_db():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Add error_message column to sms_logs if it doesn't exist
        print("Checking sms_logs table for error_message column...")
        cursor.execute("SHOW COLUMNS FROM sms_logs LIKE 'error_message'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE sms_logs ADD COLUMN error_message TEXT")
            print("Added error_message column to sms_logs.")
        else:
            print("error_message column already exists in sms_logs.")

        # Initialize default settings
        settings = [
            ('sms_target_student', 'true'),
            ('sms_target_parent', 'false'),
            ('sms_template_due_soon', 'Dear {name}, your hostel fee of Rs.{amount} is due in {days} days ({due_date}). Please pay on time to avoid late fees.'),
            ('sms_template_overdue', 'URGENT: Dear {name}, your hostel fee of Rs.{amount} is OVERDUE. Due date was {due_date}. Please pay immediately.'),
            ('sms_template_paid', 'Dear {name}, we have received your hostel fee payment of Rs.{amount}. Thank you!')
        ]
        
        print("Initializing default SMS settings...")
        for key, value in settings:
            cursor.execute("INSERT IGNORE INTO settings (setting_key, setting_value) VALUES (%s, %s)", (key, value))
            
        print("Database update complete!")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error updating database: {e}")

if __name__ == '__main__':
    update_db()
