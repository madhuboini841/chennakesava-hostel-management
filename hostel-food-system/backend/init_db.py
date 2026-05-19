import psycopg2
import os
import bcrypt

def init_db():
    try:
        db_host = os.getenv('DB_HOST', 'localhost')
        conn_args = {
            'host': db_host,
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', ''),
            'dbname': os.getenv('DB_NAME', 'postgres'),
            'port': os.getenv('DB_PORT', '5432')
        }
        if db_host != 'localhost':
            conn_args['sslmode'] = 'require'
            
        conn = psycopg2.connect(**conn_args)
        conn.autocommit = True
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
                
        # Insert default admin user requested by user
        cursor.execute("SELECT id FROM admins WHERE email = 'admin@cbh.com'")
        if not cursor.fetchone():
            hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            cursor.execute(
                "INSERT INTO admins (name, email, password_hash) VALUES (%s, %s, %s) ON CONFLICT (email) DO NOTHING",
                ("Admin", "admin@cbh.com", hashed)
            )

        print("Database initialized successfully with default admin.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.closed == 0:
            conn.close()

if __name__ == '__main__':
    init_db()
