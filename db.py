import os
from dotenv import load_dotenv
import libsql

load_dotenv()

def get_db_connection():
    url = os.environ.get("TURSO_DATABASE_URL")
    token = os.environ.get("TURSO_AUTH_TOKEN")
    return libsql.connect(url, auth_token=token)

def init_db(force_reset=False):
    """Initializes the job_applications table. If force_reset=True, drops the table first."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if force_reset:
        print("[DB Reset] Dropping existing 'job_applications' table...")
        cursor.execute("DROP TABLE IF EXISTS job_applications")
    
    # Clean, modern v2 schema
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT,
            source TEXT,
            status TEXT DEFAULT 'NEW',
            salary_range TEXT,
            hiring_manager TEXT,
            contact_email TEXT,
            notes TEXT,
            discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Turso Database initialized successfully.")