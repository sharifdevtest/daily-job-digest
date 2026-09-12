import os
import json
import smtplib
import feedparser
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def fetch_and_filter_jobs(config):
    matched_jobs = []
    
    for source in config.get("sources", []):
        feed = feedparser.parse(source["feed_url"])
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            
            # Exclusion logic
            if any(bad_word.lower() in title.lower() for bad_word in config["excluded_keywords"]):
                continue
                
            # Matching logic
            matched_jobs.append({
                "title": title,
                "link": link,
                "source": source["name"]
            })
            
    return matched_jobs

def send_html_email(jobs, recipient_email):
    sender_email = os.environ.get("SENDER_EMAIL")
    app_password = os.environ.get("GMAIL_APP_PASSWORD")
    
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "Daily Job Digest: Leadership & Engineering Roles"
    msg["From"] = sender_email
    msg["To"] = recipient_email

    # Dynamic HTML Builder
    job_rows = ""
    for job in jobs:
        job_rows += f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #ddd;">
                <strong style="color: #004085; font-size: 16px;">{job['title']}</strong><br/>
                <span style="color: #6c757d; font-size: 12px;">Source: {job['source']}</span>
            </td>
            <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">
                <a href="{job['link']}" style="background-color: #007bff; color: white; padding: 6px 12px; text-decoration: none; border-radius: 4px; font-size: 14px;">View Job</a>
            </td>
        </tr>
        """

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #f8f9fa; padding: 20px;">
        <div style="max-width: 650px; margin: auto; background: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #dee2e6;">
            <h2 style="color: #212529; border-bottom: 2px solid #007bff; padding-bottom: 10px;">Morning Job Briefing</h2>
            <table style="width: 100%; border-collapse: collapse;">
                {job_rows if jobs else "<tr><td colspan='2'>No new matching roles found in the last 24 hours.</td></tr>"}
            </table>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient_email, msg.as_string())

if __name__ == "__main__":
    config = load_config()
    jobs = fetch_and_filter_jobs(config)
    recipient = os.environ.get("RECIPIENT_EMAIL")
    send_html_email(jobs, recipient)