import sys
from db import init_db

if __name__ == "__main__":
    # Check for CLI flag: python reset_db.py --force
    if "--force" in sys.argv:
        init_db(force_reset=True)
        print("Database wiped and recreated successfully via --force flag!")
        sys.exit(0)

    try:
        confirm = input("Are you sure you want to DROP the 'job_applications' table in Turso? (y/N): ")
        if confirm.lower() == 'y':
            init_db(force_reset=True)
            print("Database wiped and recreated successfully!")
        else:
            print("Reset cancelled.")
    except EOFError:
        print("[Error] Cannot prompt for input in a non-interactive environment. Use 'python reset_db.py --force' to bypass.")