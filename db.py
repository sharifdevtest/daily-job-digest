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
            description TEXT,
            notes TEXT,
            discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            last_seen_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            cv_match_verified BOOLEAN DEFAULT 0,
            cv_submitted BOOLEAN DEFAULT 0,
            hm_outreach_completed BOOLEAN DEFAULT 0,
            follow_up_count INTEGER DEFAULT 0,
            last_follow_up_note TEXT,
            match_score REAL,
            missing_skills TEXT,
            tailored_resume_path TEXT
        )
    """)
    
    # Ensure new columns exist for existing tables
    columns_to_add = {
        'match_score': 'REAL',
        'missing_skills': 'TEXT',
        'tailored_resume_path': 'TEXT',
        'description': 'TEXT'
    }
    
    cursor.execute("PRAGMA table_info(job_applications)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    for col, col_type in columns_to_add.items():
        if col not in existing_columns:
            print(f"[DB Migration] Adding column '{col}' to 'job_applications'...")
            cursor.execute(f"ALTER TABLE job_applications ADD COLUMN {col} {col_type}")
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Turso Database initialized successfully.")