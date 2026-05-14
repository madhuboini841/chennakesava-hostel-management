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

def add_columns():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        tables = ['admins', 'students']
        columns = [
            ("reset_token", "VARCHAR(255) DEFAULT NULL"),
            ("reset_token_expiry", "DATETIME DEFAULT NULL"),
            ("must_change_password", "BOOLEAN DEFAULT FALSE")
        ]
        
        for table in tables:
            for col_name, col_type in columns:
                try:
                    cursor.execute(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    print(f"Added {col_name} to {table}")
                except mysql.connector.Error as e:
                    if e.errno == 1060: # Duplicate column name
                        print(f"Column {col_name} already exists in {table}")
                    else:
                        print(f"Error adding {col_name} to {table}: {e}")
                        
        cursor.close()
        conn.close()
        print("Database schema updated successfully.")
    except Exception as e:
        print(f"Failed to connect to db: {e}")

if __name__ == '__main__':
    add_columns()
