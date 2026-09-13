import os
import json
import re
import requests

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

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def filter_jobs(raw_jobs, config):
    """Filters listings for strict IT/QA leadership focus."""
    filtered = []
    excluded = [k.lower() for k in config.get("excluded_keywords", [])]
    target_roles = [r.lower() for r in config.get("target_roles", [])]
    
    it_domain_triggers = {
        "it", "qa", "test", "testing", "software", "engineering", 
        "technology", "data", "cloud", "agile", "infrastructure", 
        "system", "devops", "architect", "quality", "digital"
    }
    
    seen_links = set()
    
    for job in raw_jobs:
        if job["link"] in seen_links:
            continue
            
        title_lower = job["title"].lower()
        
        # 1. Reject explicit exclusion keywords
        if any(bad in title_lower for bad in excluded):
            continue
            
        # 2. Require at least ONE IT/Tech domain trigger keyword
        title_words = set(re.findall(r'\w+', title_lower))
        if not it_domain_triggers.intersection(title_words):
            continue
            
        # 3. Require role/seniority keyword match
        role_words = set(re.findall(r'\w+', ' '.join(target_roles)))
        if role_words.intersection(title_words):
            seen_links.add(job["link"])
            filtered.append(job)
            print(f"[IT Match] {job['title']} ({job['source']})")
            
    return filtered

def send_telegram_digest(jobs):
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Error: Missing Telegram secrets.")
        return

    if not jobs:
        message = "🌅 *Daily Direct Scraper Briefing*\n\nNo fresh matching IT/QA leadership roles found today."
    else:
        message = f"🌅 *Live Agency Job Briefing: {len(jobs)} IT/QA Roles Found*\n\n"
        for i, job in enumerate(jobs[:10], 1):
            clean_title = job['title'].replace('*', '').replace('_', '').replace('[', '').replace(']', '')
            clean_snippet = job['snippet'].replace('*', '').replace('_', '').replace('[', '').replace(']', '')
            
            message += f"*{i}. {clean_title}* ({job['source']})\n"
            message += f"📅 *Posted:* {job['posted_date']}\n"
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
            print("Telegram digest pushed successfully!")
        else:
            print(f"Push failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Network error: {e}")

if __name__ == "__main__":
    config = load_config()
    print("Scraping target recruitment agency portals...")
    
    raw_jobs = []
    for scraper_func in SCRAPERS:
        raw_jobs.extend(scraper_func())
    
    print(f"[Debug] Collected {len(raw_jobs)} total raw jobs across agencies.")
    
    final_jobs = filter_jobs(raw_jobs, config)
    print(f"Filtered down to {len(final_jobs)} IT/QA leadership matches.")
    
    send_telegram_digest(final_jobs)