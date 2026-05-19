import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def reset_db():
    if os.getenv("ALLOW_RESET") != "True":
        print("RESET is disabled in .env (ALLOW_RESET != True). Aborting.")
        return

    confirmation = input("WARNING: This will WIPE the database. Type 'YES' to continue: ")
    if confirmation != "YES":
        print("Aborting database reset.")
        return

    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        
    )
    cursor = conn.cursor()
    
    # Drop existing db to ensure clean slate
    cursor.execute("DROP DATABASE IF EXISTS hostel_db")
    cursor.execute("CREATE DATABASE hostel_db")
    cursor.execute("USE hostel_db")
    
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

    print("Database fully reset and initialized successfully.")
    cursor.close()
    conn.close()

if __name__ == '__main__':
    reset_db()
