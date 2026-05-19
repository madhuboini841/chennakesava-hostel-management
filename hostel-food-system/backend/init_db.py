import mysql.connector

def init_db():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            autocommit=True
        )
        cursor = conn.cursor()
        
        with open('database.sql', 'r') as f:
            lines = f.readlines()

        clean_lines = []
        for line in lines:
            line_stripped = line.strip()
            if not line_stripped.startswith('--') and line_stripped:
                clean_lines.append(line)
                
        sql_script = ''.join(clean_lines)

        statements = sql_script.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement:
                cursor.execute(statement)

        print("Database initialized successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == '__main__':
    init_db()
