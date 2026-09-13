import os
import json
import re
import html
import requests
from bs4 import BeautifulSoup

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def clean_text(text):
    if not text:
        return ""
    clean = re.sub(r'\s+', ' ', text)
    return html.unescape(clean).strip()

def scrape_michael_page():
    """Scrapes active job listings from Michael Page Middle East."""
    jobs = []
    url = "https://www.michaelpage.ae/jobs"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        print(f"[Debug] Michael Page HTTP Status: {res.status_code}")
        if res.status_code != 200:
            return jobs
            
        soup = BeautifulSoup(res.text, "html.parser")
        
        # Target exact HTML card containers used by Michael Page
        cards = soup.select("li.views-row, article.card, div.job-title")
        print(f"[Debug] Identified {len(cards)} specific job card containers.")
        
        for card in cards:
            title_elem = card.select_one("h3 a, h2 a, .job-title a, a[href*='/job-detail/']")
            snippet_elem = card.select_one(".job-summary, .card-body, p")
            
            if title_elem:
                title = clean_text(title_elem.get_text())
                href = title_elem.get("href", "")
                
                if not href.startswith("http"):
                    href = f"https://www.michaelpage.ae{href}"
                    
                snippet = clean_text(snippet_elem.get_text()) if snippet_elem else "View job details on site."
                
                if title:
                    jobs.append({
                        "title": title,
                        "link": href,
                        "snippet": snippet[:180] + "..." if len(snippet) > 180 else snippet,
                        "source": "Michael Page AE"
                    })
    except Exception as e:
        print(f"[Error] Failed to scrape Michael Page: {e}")
        
    return jobs

def filter_jobs(raw_jobs, config):
    """Filters listings with flexible partial keyword matching."""
    filtered = []
    excluded = [k.lower() for k in config.get("excluded_keywords", [])]
    target_roles = [r.lower() for r in config.get("target_roles", [])]
    
    seen_links = set()
    
    for job in raw_jobs:
        if job["link"] in seen_links:
            continue
            
        title_lower = job["title"].lower()
        snippet_lower = job["snippet"].lower()
        
        # 1. Skip excluded keywords
        if any(bad in title_lower for bad in excluded):
            continue
            
        # 2. Match target role keywords (checks if core terms like 'qa', 'manager', 'lead', 'architect', 'delivery' exist)
        role_words = set(re.findall(r'\w+', ' '.join(target_roles)))
        title_words = set(re.findall(r'\w+', title_lower))
        
        # Keep job if there's an overlap in key leadership/QA terminology
        if role_words.intersection(title_words):
            seen_links.add(job["link"])
            filtered.append(job)
            print(f"[Match Found] {job['title']}")
            
    return filtered

def send_telegram_digest(jobs):
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Error: Missing Telegram secrets.")
        return

    if not jobs:
        message = "🌅 *Daily Job Briefing*\n\nNo fresh matching roles found directly on target agency portals today."
    else:
        message = f"🌅 *Live Agency Job Briefing: {len(jobs)} Roles Found*\n\n"
        for i, job in enumerate(jobs[:8], 1):
            clean_title = job['title'].replace('*', '').replace('_', '').replace('[', '').replace(']', '')
            clean_snippet = job['snippet'].replace('*', '').replace('_', '').replace('[', '').replace(']', '')
            
            message += f"*{i}. {clean_title}* ({job['source']})\n"
            if clean_snippet:
                message += f"📝 *Details:* {clean_snippet}\n"
            message += f"🔗 [Apply / View Listing]({job['link']})\n\n"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        res = requests.post(url, json=payload, timeout=10)
        if res.status_code == 200:
            print("Telegram message sent successfully!")
        else:
            print(f"Push failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Network error: {e}")

if __name__ == "__main__":
    config = load_config()
    print("Scraping direct agency portal...")
    
    raw_jobs = scrape_michael_page()
    print(f"[Debug] Extracted {len(raw_jobs)} total raw job cards from page.")
    
    final_jobs = filter_jobs(raw_jobs, config)
    print(f"Found {len(final_jobs)} matching roles.")
    
    send_telegram_digest(final_jobs)