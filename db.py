import os
import libsql
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

def get_db_connection():
    """Establishes connection to Turso Cloud SQLite DB."""
    url = os.environ.get("TURSO_DATABASE_URL")
    token = os.environ.get("TURSO_AUTH_TOKEN")
    
    if not url or not token:
        raise ValueError("Missing TURSO_DATABASE_URL or TURSO_AUTH_TOKEN environment variables. "
                         "Check your .env file or GitHub Secrets.")
        
    return libsql.connect("jobs_tracker.db", sync_url=url, auth_token=token)

def init_db():
    """Initializes the job_applications table schema."""
    conn = get_db_connection()
    conn.sync()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_applications (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            url TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT DEFAULT 'NEW',
            salary_range TEXT DEFAULT 'Not Specified',
            hiring_manager TEXT DEFAULT 'Not Found',
            contact_email TEXT DEFAULT 'N/A',
            notes TEXT DEFAULT '',
            discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.sync()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Turso Database initialized successfully.")