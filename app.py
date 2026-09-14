import streamlit as st
import pandas as pd
import os
import getpass
from dotenv import load_dotenv
from db import get_db_connection

load_dotenv()

# --- PASSWORD AUTHENTICATION GATEWAY ---
def check_password():
    def password_entered():
        correct_password = os.environ.get("APP_PASSWORD")
        if not correct_password:
            st.error("Setup Error: APP_PASSWORD is not set!")
            return
        if st.session_state["password"] == correct_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        session_user = getpass.getuser()
        st.info(f"👤 Active System Session User: **{session_user}**")
        st.text_input("Enter Portal Password", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Enter Portal Password", type="password", on_change=password_entered, key="password")
        st.error("😕 Access Denied.")
        return False
    return True

if not check_password():
    st.stop()

# --- MAIN APP ---
st.set_page_config(page_title="Executive Job Tracker", layout="wide")
st.title("💼 Executive IT & QA Job Tracker")

@st.cache_data(ttl=600)
def load_data():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM job_applications ORDER BY discovered_at DESC", conn)
    conn.close()
    return df

def update_db(edited_df):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Batch update changed rows
    for _, row in edited_df.iterrows():
        # Smart logic: Auto-move to "APPLIED" if submitted
        new_status = row['status']
        if row['cv_submitted'] and new_status == "NEW":
            new_status = "APPLIED"
            
        cursor.execute("""
            UPDATE job_applications 
            SET status = ?, salary_range = ?, hiring_manager = ?, notes = ?,
                cv_match_verified = ?, 
                cv_submitted = ?, 
                hm_outreach_completed = ?, 
                follow_up_count = ?, 
                last_follow_up_note = ?, 
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (
            new_status, row['salary_range'], row['hiring_manager'], row['notes'],
            int(row['cv_match_verified']), 
            int(row['cv_submitted']), 
            int(row['hm_outreach_completed']), 
            row['follow_up_count'], 
            row['last_follow_up_note'], 
            row['id']
        ))
    conn.commit()
    conn.close()
    st.cache_data.clear()

if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

data = load_data()
statuses = ["NEW", "IN_PROGRESS", "APPLIED", "CLOSED", "TO_REVIEW"]
tabs = st.tabs(statuses)

for i, status in enumerate(statuses):
    with tabs[i]:
        filtered_df = data[data['status'] == status]
        st.subheader(f"{status} ({len(filtered_df)})")
        
        # Grid-based editor
        edited_df = st.data_editor(
            filtered_df,
            column_config={
                "url": st.column_config.LinkColumn("Link"),
                "status": st.column_config.SelectboxColumn("Status", options=statuses),
                "cv_match_verified": st.column_config.CheckboxColumn("CV Match"),
                "cv_submitted": st.column_config.CheckboxColumn("Submitted"),
                "hm_outreach_completed": st.column_config.CheckboxColumn("HM Outreach"),
                "follow_up_count": st.column_config.NumberColumn("Follow-up #", min_value=0),
                "last_follow_up_note": st.column_config.TextColumn("Last Follow-up Note"),
                "notes": st.column_config.TextColumn("Notes", width="medium"),
            },
            hide_index=True,
            use_container_width=True,
            key=f"editor_{status}"
        )
        
        if st.button(f"Save Changes ({status})", key=f"btn_{status}"):
            update_db(edited_df)
            st.success("Changes saved!")
            st.rerun()