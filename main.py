import os
import json
import requests
import feedparser

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
            
            # Check exclusions
            if any(bad_word.lower() in title.lower() for bad_word in config.get("excluded_keywords", [])):
                continue
                
            matched_jobs.append({
                "title": title,
                "link": link,
                "source": source["name"]
            })
            
    return matched_jobs

def send_telegram_digest(jobs):
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Telegram credentials missing.")
        return

    if not jobs:
        message = "🌅 *Daily Job Briefing*\n\nNo new matching roles found in the last 24 hours."
    else:
        message = "🌅 *Daily Job Briefing: Leadership & QA Roles*\n\n"
        for i, job in enumerate(jobs[:10], 1): # Send top matches
            clean_title = job['title'].replace('*', '').replace('_', '')
            message += f"{i}. *{clean_title}*\n"
            message += f"📌 _Source: {job['source']}_\n"
            message += f"🔗 [Apply Here]({job['link']})\n\n"

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Telegram message sent successfully!")
    else:
        print(f"Failed to send Telegram message: {response.text}")

if __name__ == "__main__":
    config = load_config()
    jobs = fetch_and_filter_jobs(config)
    send_telegram_digest(jobs)