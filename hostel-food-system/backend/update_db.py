import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'hostel_db',
    'autocommit': True
}

def update_schema():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # 1. Add meal_preference to students if not exists
        try:
            cursor.execute("ALTER TABLE students ADD COLUMN meal_preference ENUM('veg', 'non-veg') DEFAULT 'veg';")
            print("Added meal_preference to students table.")
        except psycopg2.Error as e:
            if e.errno == 1060: # Duplicate column name
                print("Column meal_preference already exists.")
            else:
                print(f"Error adding column: {e}")

        # 2. Create daily_menus table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_menus (
                id INT AUTO_INCREMENT PRIMARY KEY,
                date DATE NOT NULL,
                meal_slot ENUM('breakfast', 'lunch', 'dinner') NOT NULL,
                meal_type ENUM('veg', 'non-veg') NOT NULL,
                items TEXT NOT NULL,
                is_locked BOOLEAN DEFAULT FALSE,
                posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                UNIQUE KEY unique_menu (date, meal_slot, meal_type)
            );
        """)
        print("Created daily_menus table.")

        # 3. Create food_optouts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS food_optouts (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL,
                date DATE NOT NULL,
                breakfast BOOLEAN DEFAULT FALSE,
                lunch BOOLEAN DEFAULT FALSE,
                dinner BOOLEAN DEFAULT FALSE,
                reason TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                UNIQUE KEY unique_optout (student_id, date)
            );
        """)
        print("Created food_optouts table.")

        cursor.close()
        conn.close()
        print("Schema update completed successfully.")

    except psycopg2.Error as e:
        print(f"Database connection failed: {e}")

if __name__ == "__main__":
    update_schema()
