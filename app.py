import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
from db import get_db_connection

# Load local environment variables from .env
load_dotenv()

# --- PASSWORD AUTHENTICATION GATEWAY ---
def check_password():
    """Returns True if the user has entered correct username and password."""
    def credentials_entered():
        correct_username = os.environ.get("APP_USERNAME")
        correct_password = os.environ.get("APP_PASSWORD")
        
        if not correct_username or not correct_password:
            st.error("Setup Error: Credentials are not set in the .env environment!")
            return

        if (st.session_state["username"] == correct_username and 
            st.session_state["password"] == correct_password):
            st.session_state["password_correct"] = True
            # Clean up credentials
            del st.session_state["username"]
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Show both Username and Password fields
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Log In", on_click=credentials_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Log In", on_click=credentials_entered)
        st.error("😕 Username or Password incorrect.")
        return False
    else:
        return True

# If the password check fails, halt execution here and do not load the rest of the application
if not check_password():
    st.stop()

# Remaining application configuration runs only if authentication succeeds
st.set_page_config(page_title="Executive QA/IT Job Tracker", layout="wide")
st.title("💼 Senior IT & QA Leadership Application Tracker")

def load_data():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM job_applications ORDER BY discovered_at DESC", conn)
    conn.close()
    return df

def update_job_details(job_id, status, salary, manager, notes):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE job_applications 
        SET status = ?, salary_range = ?, hiring_manager = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (status, salary, manager, notes, job_id))
    conn.commit()
    conn.close()

# Main Board View
try:
    data = load_data()
except Exception as e:
    st.error(f"Error connecting to database: {e}")
    st.info("Make sure you have run 'python db.py' once to initialize your Turso table!")
    st.stop()

statuses = ["NEW", "IN_PROGRESS", "APPLIED", "CLOSED"]
cols = st.columns(4)

for i, status in enumerate(statuses):
    with cols[i]:
        st.subheader(f"{status} ({len(data[data['status'] == status])})")
        st.markdown("---")
        
        filtered_df = data[data['status'] == status]
        for _, job in filtered_df.iterrows():
            with st.expander(f"**{job['title']}**\n\n*{job['company']} ({job['source']})*"):
                st.write(f"📍 **Location:** {job['location']}")
                st.markdown(f"🔗 [Direct Application Link]({job['url']})")
                
                # Dynamic Editable Inputs
                salary = st.text_input("Salary", value=job['salary_range'], key=f"sal_{job['id']}")
                manager = st.text_input("Hiring Manager / Recruiter", value=job['hiring_manager'], key=f"hm_{job['id']}")
                notes = st.text_area("Notes / Next Steps", value=job['notes'] or "", key=f"notes_{job['id']}")
                
                new_status = st.selectbox(
                    "Move Status Queue", 
                    options=statuses, 
                    index=statuses.index(job['status']),
                    key=f"status_{job['id']}"
                )
                
                if st.button("Update Card", key=f"btn_{job['id']}"):
                    update_job_details(job['id'], new_status, salary, manager, notes)
                    st.success("Card updated!")
                    st.rerun()