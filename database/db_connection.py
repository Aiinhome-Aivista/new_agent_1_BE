import os
import sqlite3
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# Global state to switch to SQLite fallback if MySQL is offline
USE_SQLITE = False

class RowWrapper(dict):
    def __init__(self, sqlite_row):
        super().__init__({k: sqlite_row[k] for k in sqlite_row.keys()})
        self.tuple_values = tuple(sqlite_row)

    def __getitem__(self, key):
        if isinstance(key, int):
            return self.tuple_values[key]
        return super().__getitem__(key)

class SQLiteCursorWrapper:
    def __init__(self, sqlite_cursor):
        self.cursor = sqlite_cursor

    def execute(self, query, params=None):
        # Convert %s placeholders to SQLite's ? placeholders
        query = query.replace('%s', '?')
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)

    def fetchone(self):
        row = self.cursor.fetchone()
        if row:
            return RowWrapper(row)
        return None

    def fetchall(self):
        rows = self.cursor.fetchall()
        return [RowWrapper(r) for r in rows]

    def close(self):
        self.cursor.close()

class SQLiteConnectionWrapper:
    def __init__(self, sqlite_conn):
        self.conn = sqlite_conn

    def cursor(self, dictionary=False):
        self.conn.row_factory = sqlite3.Row
        return SQLiteCursorWrapper(self.conn.cursor())

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

def get_db_connection():
    global USE_SQLITE
    if USE_SQLITE:
        return get_sqlite_connection()

    try:
        # Try MySQL
        return mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "1234"),
            database=os.getenv("MYSQL_NAME", "mydb")
        )
    except Exception as e:
        print(f"MySQL connection failed: {e}. Falling back to local SQLite database.")
        USE_SQLITE = True
        return get_sqlite_connection()

def get_sqlite_connection():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path, check_same_thread=False)
    return SQLiteConnectionWrapper(conn)

def init_sqlite_db():
    db_path = os.path.join(os.path.dirname(__file__), 'database.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposals (
        id TEXT PRIMARY KEY,
        client_name TEXT NOT NULL,
        project_duration TEXT NOT NULL,
        budget TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Ingesting',
        generated_file_path TEXT NULL,
        structured_json_ir TEXT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS knowledge_assets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL,
        category TEXT NOT NULL,
        capabilities TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proposal_steps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        proposal_id TEXT NOT NULL,
        step_name TEXT NOT NULL,
        status TEXT NOT NULL,
        log_message TEXT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Seed default user if empty
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('admin', 'password', 'admin')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('presales', 'password', 'presales')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('bidmanager', 'password', 'bidmanager')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('delivery', 'password', 'delivery')")
        cursor.execute("INSERT INTO users (username, password, role) VALUES ('partner', 'password', 'partner')")
        
    # Seed knowledge assets if empty
    cursor.execute("SELECT id FROM knowledge_assets")
    if not cursor.fetchone():
        assets = [
            ('Enterprise Cloud Migration Toolkit', 'A framework containing reusable Ansible and Terraform templates for migrating enterprise Java/React apps to AWS/Azure.', 'Asset', 'AWS,Azure,Terraform,Ansible,Migration,Java,React'),
            ('Enterprise Data Governance Framework', 'Standard templates, policies, and schemas for metadata management, lineage tracking, and data cataloging.', 'Asset', 'Governance,Collibra,Data Catalog,Metadata,SQL'),
            ('DevOps Pipeline Accelerator', 'Pre-configured CI/CD pipelines using GitHub Actions and GitLab CI, with integrated security scans (Snyk, SonarQube).', 'Asset', 'DevOps,GitHub Actions,GitLab CI,Snyk,SonarQube,Docker,Kubernetes'),
            ('React/TypeScript Front-End Competency', 'Large pool of skilled front-end engineers specializing in React, TypeScript, State Management (Zustand/Redux), and Tailwind CSS.', 'Competency', 'React,TypeScript,Zustand,Tailwind CSS,Vite'),
            ('Python Data Engineering Competency', 'Team of data engineers experienced in PySpark, Pandas, Airflow, and building robust ETL pipelines.', 'Competency', 'Python,PySpark,Pandas,Airflow,ETL,Data Pipeline'),
            ('Cybersecurity Compliance Competency', 'Certified auditors and engineers specializing in ISO27001, SOC2, and data privacy compliance assessments.', 'Competency', 'ISO27001,SOC2,Cybersecurity,Compliance,Audit')
        ]
        for name, desc, cat, caps in assets:
            cursor.execute("INSERT INTO knowledge_assets (name, description, category, capabilities) VALUES (?, ?, ?, ?)", (name, desc, cat, caps))
            
    conn.commit()
    cursor.close()
    conn.close()
    print("Local SQLite database initialized and seeded successfully.")

def init_db():
    """Initializes the database. Tries MySQL first, falls back to SQLite."""
    global USE_SQLITE
    try:
        # First connect to MySQL without database name to create database if not exists
        conn = mysql.connector.connect(
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", 3306)),
            user=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", "1234")
        )
        cursor = conn.cursor()
        
        # Read and execute schema file
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            commands = schema_sql.split(';')
            for command in commands:
                cmd = command.strip()
                if cmd:
                    cursor.execute(cmd)
            conn.commit()
            
            # --- Safely run migrations (ADD COLUMN IF NOT EXISTS equivalent for MySQL) ---
            try:
                cursor.execute("ALTER TABLE proposals ADD COLUMN submitted_by_role VARCHAR(50) NULL")
            except mysql.connector.Error as err:
                if err.errno != 1060: # 1060 = Duplicate column name
                    print(f"Migration error (submitted_by_role): {err}")
                    
            try:
                cursor.execute("ALTER TABLE proposals ADD COLUMN last_transitioned_at TIMESTAMP NULL")
            except mysql.connector.Error as err:
                if err.errno != 1060:
                    print(f"Migration error (last_transitioned_at): {err}")
                    
            conn.commit()
            print("MySQL database initialized successfully.")
        else:
            print("Schema file not found at:", schema_path)
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"MySQL initialization failed: {e}. Switching init_db to local SQLite.")
        USE_SQLITE = True
        init_sqlite_db()
