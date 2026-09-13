import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from db import get_db_connection

# Load local environment variables from .env
load_dotenv()

st.set_page_config(page_title="Executive QA/IT Job Tracker", layout="wide")
st.title("💼 Senior IT & QA Leadership Application Tracker")

def load_data():
    conn = get_db_connection()
    conn.sync()
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
    conn.sync()
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