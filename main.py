import os
import json
import re
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Import scraper modules
from scrapers import michael_page, hays, adecco, randstad, linkedin, charterhouse

# List all active agency scrapers
SCRAPERS = [
    michael_page.scrape,
    hays.scrape,
    adecco.scrape,
    randstad.scrape,
    linkedin.scrape,
    charterhouse.scrape
]

SEEN_JOBS_FILE = "seen_jobs.json"

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def load_seen_jobs():
    """Loads previously alerted job URLs from persistent storage."""
    if os.path.exists(SEEN_JOBS_FILE):
        try:
            with open(SEEN_JOBS_FILE, "r") as f:
                return set(json.load(f))
        except Exception as e:
            print(f"[Warning] Failed to load seen_jobs.json: {e}")
    return set()

def save_seen_jobs(seen_jobs):
    """Saves updated set of reported job URLs back to disk."""
    try:
        with open(SEEN_JOBS_FILE, "w") as f:
            json.dump(list(seen_jobs), f, indent=2)
        print(f"[Storage] Successfully updated {SEEN_JOBS_FILE} with {len(seen_jobs)} records.")
    except Exception as e:
        print(f"[Error] Failed to save seen_jobs.json: {e}")

def filter_jobs(raw_jobs, config, seen_jobs):
    """Filters listings for strict IT/QA leadership focus and excludes previously reported jobs."""
    filtered = []
    excluded = [k.lower() for k in config.get("excluded_keywords", [])]
    target_roles = [r.lower() for r in config.get("target_roles", [])]
    
    it_domain_triggers = {
        "it", "qa", "test", "testing", "software", "engineering", 
        "technology", "data", "cloud", "agile", "infrastructure", 
        "system", "devops", "architect", "quality", "digital"
    }
    
    for job in raw_jobs:
        link = job["link"]
        
        # 1. Skip if already sent in a previous run
        if link in seen_jobs:
            continue
            
        title_lower = job["title"].lower()
        
        # 2. Reject explicit exclusion keywords
        if any(bad in title_lower for bad in excluded):
            continue
            
        # 3. Require at least ONE IT/Tech domain trigger keyword
        title_words = set(re.findall(r'\w+', title_lower))
        if not it_domain_triggers.intersection(title_words):
            continue
            
        # 4. Require role/seniority keyword match
        role_words = set(re.findall(r'\w+', ' '.join(target_roles)))
        if role_words.intersection(title_words):
            seen_jobs.add(link)
            filtered.append(job)
            print(f"[New IT Match] {job['title']} ({job['source']})")
            
    return filtered, seen_jobs

def send_telegram_digest(jobs):
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Error: Missing Telegram secrets.")
        return

    if not jobs:
        print("No new jobs to report today. Skipping Telegram notification.")
        return

    messages = []
    current_msg = f"🌅 *Live Agency Job Briefing: {len(jobs)} New IT/QA Roles Found*\n\n"
    
    for i, job in enumerate(jobs, 1):
        clean_title = job['title'].replace('*', '').replace('_', '').replace('[', '').replace(']', '')
        clean_snippet = job['snippet'].replace('*', '').replace('_', '').replace('[', '').replace(']', '')
        
        entry = f"*{i}. {clean_title}* ({job['source']})\n"
        entry += f"📅 *Posted:* {job['posted_date']}\n"
        if clean_snippet:
            entry += f"📝 *Details:* {clean_snippet}\n"
        entry += f"🔗 [Apply / View Listing]({job['link']})\n\n"
        
        if len(current_msg) + len(entry) > 3800:
            messages.append(current_msg)
            current_msg = entry
        else:
            current_msg += entry
            
    if current_msg:
        messages.append(current_msg)

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    for idx, msg in enumerate(messages):
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        }
        
        try:
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                print(f"Telegram chunk {idx+1}/{len(messages)} pushed successfully!")
            else:
                print(f"Push failed: {res.status_code} - {res.text}")
        except Exception as e:
            print(f"Network error: {e}")

def send_email_digest(jobs):
    sender_email = os.environ.get("EMAIL_SENDER")
    sender_password = os.environ.get("EMAIL_PASSWORD")
    recipient_email = os.environ.get("EMAIL_RECIPIENT")
    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", 587))

    if not sender_email or not sender_password or not recipient_email:
        print("[Email Warning] Email credentials missing. Skipping email notification.")
        return

    if not jobs:
        print("No new jobs to report. Skipping Email notification.")
        return

    # Build HTML Body
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <h2>🌅 Daily Job Briefing: {len(jobs)} New Roles Found</h2>
        <p>Here are your newly discovered IT/QA leadership listings for today:</p>
        <hr style="border: 0; border-top: 1px solid #ccc;">
    """

    for i, job in enumerate(jobs, 1):
        html_content += f"""
        <div style="margin-bottom: 20px; padding: 10px; border-left: 4px solid #007bff; background-color: #f8f9fa;">
            <h3 style="margin: 0 0 5px 0;">{i}. <a href="{job['link']}" style="color: #007bff; text-decoration: none;">{job['title']}</a></h3>
            <p style="margin: 2px 0; font-size: 0.9em; color: #555;"><strong>Source:</strong> {job['source']} | <strong>Posted:</strong> {job['posted_date']}</p>
            <p style="margin: 5px 0;">{job['snippet']}</p>
            <a href="{job['link']}" style="display: inline-block; padding: 6px 12px; background-color: #28a745; color: white; text-decoration: none; border-radius: 4px; font-size: 0.85em;">View & Apply Listing</a>
        </div>
        """

    html_content += """
        <hr style="border: 0; border-top: 1px solid #ccc;">
        <p style="font-size: 0.8em; color: #777;">Automated alert generated by your Job Search Scraper Pipeline.</p>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🎯 Job Alert: {len(jobs)} New IT/QA Leadership Roles Found"
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg.attach(MIMEText(html_content, "html"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        print("Email digest sent successfully!")
    except Exception as e:
        print(f"[Email Error] Failed to send email: {e}")

if __name__ == "__main__":
    config = load_config()
    seen_jobs = load_seen_jobs()
    
    print("Scraping target recruitment agency portals...")
    raw_jobs = []
    for scraper_func in SCRAPERS:
        try:
            raw_jobs.extend(scraper_func())
        except Exception as e:
            print(f"[Error] Execution failed for standard scraper function: {e}")
    
    print(f"[Debug] Collected {len(raw_jobs)} total raw jobs across agencies.")
    
    final_jobs, updated_seen_jobs = filter_jobs(raw_jobs, config, seen_jobs)
    print(f"Filtered down to {len(final_jobs)} fresh IT/QA leadership matches.")
    
    # Trigger notifications across both channels
    send_telegram_digest(final_jobs)
    send_email_digest(final_jobs)
    
    save_seen_jobs(updated_seen_jobs)