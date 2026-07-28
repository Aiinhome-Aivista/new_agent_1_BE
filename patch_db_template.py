import sys
import os

# Add current dir to path to import database module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.db_connection import get_db_connection

def patch_db():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("SHOW COLUMNS FROM proposals LIKE 'ppt_template_file'")
        result = cursor.fetchone()
        
        if not result:
            print("Adding ppt_template_file column to proposals table...")
            cursor.execute("ALTER TABLE proposals ADD COLUMN ppt_template_file VARCHAR(500) NULL")
            conn.commit()
            print("Successfully added column.")
        else:
            print("Column already exists.")
            
        cursor.close()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    patch_db()
