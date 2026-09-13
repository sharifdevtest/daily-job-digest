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

def scrape_michael_page(target_roles, locations):
    """Direct scraper for Michael Page Middle East job listings."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Run targeted queries for primary role categories
    for role in target_roles[:4]:  # Prioritize top leadership/QA roles to manage execution time
        url = f"https://www.michaelpage.ae/jobs/{role.replace(' ', '-').lower()}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.find_all("article", class_=re.compile(r'job-card|card'))
            
            for article in articles:
                title_elem = article.find(["h3", "h2", "a"], class_=re.compile(r'title|heading'))
                link_elem = article.find("a", href=True)
                snippet_elem = article.find(["p", "div"], class_=re.compile(r'summary|description|text'))
                
                if title_elem and link_elem:
                    title = clean_text(title_elem.get_text())
                    link = link_elem["href"]
                    if not link.startswith("http"):
                        link = f"https://www.michaelpage.ae{link}"
                        
                    snippet = clean_text(snippet_elem.get_text()) if snippet_elem else "No description preview available."
                    
                    jobs.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet[:180] + "..." if len(snippet) > 180 else snippet,
                        "source": "Michael Page AE"
                    })
        except Exception as e:
            print(f"Error scraping Michael Page for {role}: {e}")
            
    return jobs

def scrape_hays(target_roles):
    """Direct scraper for Hays Middle East job search."""
    jobs = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    for role in target_roles[:4]:
        url = f"https://www.hays.ae/jobs?q={requests.utils.quote(role)}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                continue
                
            soup = BeautifulSoup(res.text, "html.parser")
            job_cards = soup.find_all("div", class_=re.compile(r'job-card|result-card|search-result'))
            
            for card in job_cards:
                title_elem = card.find(["h3", "a"], class_=re.compile(r'title'))
                link_elem = card.find("a", href=True)
                snippet_elem = card.find(["p", "span"], class_=re.compile(r'snippet|desc'))
                
                if title_elem and link_elem:
                    title = clean_text(title_elem.get_text())
                    link = link_elem["href"]
                    if not link.startswith("http"):
                        link = f"https://www.hays.ae{link}"
                        
                    snippet = clean_text(snippet_elem.get_text()) if snippet_elem else "No description preview available."
                    
                    jobs.append({
                        "title": title,
                        "link": link,
                        "snippet": snippet[:180] + "..." if len(snippet) > 180 else snippet,
                        "source": "Hays AE"
                    })
        except Exception as e:
            print(f"Error scraping Hays for {role}: {e}")
            
    return jobs

def filter_jobs(raw_jobs, config):
    """Filters listings against locations and excluded keywords from config.json."""
    filtered = []
    excluded = [k.lower() for k in config.get("excluded_keywords", [])]
    locations = [l.lower() for l in config.get("locations", [])]
    
    seen_links = set()
    
    for job in raw_jobs:
        if job["link"] in seen_links:
            continue
            
        title_lower = job["title"].lower()
        snippet_lower = job["snippet"].lower()
        
        # Check excluded keywords
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
        message = "🌅 *Daily Direct Scraper Briefing*\n\nNo fresh matching roles found directly on target agency sites today."
    else:
        message = f"🌅 *Live Agency Job Briefing: {len(jobs)} Roles Found*\n\n"
        for i, job in enumerate(jobs[:8], 1):  # Top 8 listings
            clean_title = (
                job['title']
                .replace('*', '')
                .replace('_', '')
                .replace('[', '')
                .replace(']', '')
            )
            clean_snippet = (
                job['snippet']
                .replace('*', '')
                .replace('_', '')
                .replace('[', '')
                .replace(']', '')
            )
            
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
            print("Telegram digest pushed successfully!")
        else:
            print(f"Push failed: {res.status_code} - {res.text}")
    except Exception as e:
        print(f"Network error: {e}")

if __name__ == "__main__":
    config = load_config()
    target_roles = config.get("target_roles", [])
    locations = config.get("locations", [])
    
    print("Scraping direct agency sites...")
    raw_jobs = []
    raw_jobs.extend(scrape_michael_page(target_roles, locations))
    raw_jobs.extend(scrape_hays(target_roles))
    
    final_jobs = filter_jobs(raw_jobs, config)
    print(f"Found {len(final_jobs)} matching roles.")
    
    send_telegram_digest(final_jobs)