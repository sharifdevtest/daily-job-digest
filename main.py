import os
import json
import requests
import feedparser

def load_config():
    """Loads the search configuration rules from config.json."""
    with open("config.json", "r") as f:
        return json.load(f)

def fetch_and_filter_jobs(config):
    """
    Parses configured Google Alert RSS feeds and filters job listings.
    Uses flexible keyword matching to ensure potential roles are not missed.
    """
    matched_jobs = []
    
    # Core domain keywords for flexible matching during feed validation
    role_keywords = [
        "delivery", "project manager", "engineering manager", 
        "qa", "test", "architect", "governance", "quality", "leader"
    ]
    
    for source in config.get("sources", []):
        feed = feedparser.parse(source["feed_url"])
        
        for entry in feed.entries:
            title = entry.title
            link = entry.link
            
            # 1. Skip listing if it contains any explicitly excluded keyword
            if any(bad_word.lower() in title.lower() for bad_word in config.get("excluded_keywords", [])):
                continue
                
            # 2. Match either against full target roles OR broad role keywords
            title_lower = title.lower()
            exact_match = any(role.lower() in title_lower for role in config.get("target_roles", []))
            broad_match = any(kw in title_lower for kw in role_keywords)
            
            if exact_match or broad_match:
                matched_jobs.append({
                    "title": title,
                    "link": link,
                    "source": source["name"]
                })
            
    return matched_jobs

def send_telegram_digest(jobs):
    """Formats the matched jobs and pushes them to Telegram via Bot API."""
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Error: Missing TELEGRAM_TOKEN or TELEGRAM_CHAT_ID secrets.")
        return

    if not jobs:
        message = "🌅 *Daily Job Briefing*\n\nNo new matching roles found in the last 24 hours."
    else:
        message = "🌅 *Daily Job Briefing: Leadership & QA Roles*\n\n"
        # Display top 10 unique matches to keep the message concise
        for i, job in enumerate(jobs[:10], 1):
            # Clean special Markdown characters from RSS titles
            clean_title = (
                job['title']
                .replace('*', '')
                .replace('_', '')
                .replace('[', '')
                .replace(']', '')
            )
            message += f"{i}. *{clean_title}*\n"
            message += f"📌 _Source: {job['source']}_\n"
            message += f"🔗 [Apply / View Listing]({job['link']})\n\n"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("Telegram digest pushed successfully!")
        else:
            print(f"Failed to send Telegram message: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Network error while connecting to Telegram API: {e}")

if __name__ == "__main__":
    config = load_config()
    jobs = fetch_and_filter_jobs(config)
    send_telegram_digest(jobs)