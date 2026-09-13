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

def scrape_michael_page_regional(target_roles, config_locations):
    """Scrapes Michael Page UAE active job listings."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Direct regional listings endpoint (Server-side rendered)
    url = "https://www.michaelpage.ae/jobs/united-arab-emirates"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        print(f"[Debug] Michael Page HTTP Status: {res.status_code}")
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # Find all job cards/items on page 1
            cards = soup.find_all(["li", "article", "div"], class_=re.compile(r'views-row|job|card|search-result', re.I))
            print(f"[Debug] Found {len(cards)} potential job containers on page.")
            
            for card in cards:
                title_elem = card.find(["h3", "h2", "a"], class_=re.compile(r'title|heading', re.I))
                link_elem = card.find("a", href=True)
                snippet_elem = card.find(["p", "div", "span"], class_=re.compile(r'summary|desc|text|snippet', re.I))
                
                if title_elem and link_elem:
                    title = clean_text(title_elem.get_text())
                    link = link_elem["href"]
                    if not link.startswith("http"):
                        link = f"https://www.michaelpage.ae{link}"
                        
                    snippet = clean_text(snippet_elem.get_text()) if snippet_elem else "Active regional listing."
                    
                    # Match against target roles loosely
                    title_lower = title.lower()
                    if any(role.lower() in title_lower for role in target_roles) or len(target_roles) == 0:
                        jobs.append({
                            "title": title,
                            "link": link,
                            "snippet": snippet[:180] + "..." if len(snippet) > 180 else snippet,
                            "source": "Michael Page AE"
                        })
    except Exception as e:
        print(f"Error scraping Michael Page: {e}")
            
    return jobs

def filter_jobs(raw_jobs, config):
    """Filters listings against excluded keywords."""
    filtered = []
    excluded = [k.lower() for k in config.get("excluded_keywords", [])]
    seen_links = set()
    
    for job in raw_jobs:
        if job["link"] in seen_links:
            continue
            
        title_lower = job["title"].lower()
        snippet_lower = job["snippet"].lower()
        
        # Check excluded keywords (Junior, Intern, etc.)
        if any(bad in title_lower or bad in snippet_lower for bad in excluded):
            continue
            
        seen_links.add(job["link"])
        filtered.append(job)
        
    return filtered

def send_telegram_digest(jobs):
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Error: Missing Telegram secrets.")
        return

    if not jobs:
        message = "🌅 *Daily Job Briefing*\n\nNo active matching roles found on agency boards today."
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
            print(f"Telegram push failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Network error: {e}")

if __name__ == "__main__":
    config = load_config()
    target_roles = config.get("target_roles", [])
    locations = config.get("locations", [])
    
    print("Scraping direct agency portal...")
    raw_jobs = scrape_michael_page_regional(target_roles, locations)
    
    # If no strict role matches, return all active management/tech roles for verification
    if not raw_jobs:
        print("[Fallback] No exact title matches for target_roles. Fetching all active regional listings...")
        raw_jobs = scrape_michael_page_regional([], locations)
        
    final_jobs = filter_jobs(raw_jobs, config)
    print(f"Found {len(final_jobs)} matching roles.")
    
    send_telegram_digest(final_jobs)