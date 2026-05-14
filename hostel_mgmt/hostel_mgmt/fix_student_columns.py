import mysql.connector

conn = mysql.connector.connect(host='localhost', user='root', password='', database='hostel_db', autocommit=True)
cursor = conn.cursor()

columns = [
    ("meal_preference", "ENUM('veg', 'non-veg') DEFAULT 'veg'"),
    ("dob", "DATE"),
    ("gender", "VARCHAR(20)"),
    ("aadhaar_number", "VARCHAR(20)"),
    ("blood_group", "VARCHAR(10)"),
    ("parent_name", "VARCHAR(100)"),
    ("parent_relation", "VARCHAR(50)"),
    ("college_name", "VARCHAR(150)"),
    ("branch", "VARCHAR(100)"),
    ("permanent_address", "TEXT"),
    ("city", "VARCHAR(100)"),
    ("state", "VARCHAR(100)"),
    ("pincode", "VARCHAR(20)")
]

for col_name, col_type in columns:
    try:
        cursor.execute(f"ALTER TABLE students ADD COLUMN {col_name} {col_type}")
        print(f"Added {col_name}")
    except mysql.connector.Error as err:
        if err.errno == 1060: # Duplicate column name
            print(f"Column {col_name} already exists")
        else:
            print(f"Error adding {col_name}: {err}")

cursor.close()
conn.close()
