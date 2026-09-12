import os
import json
import re
import html
import requests

def load_config():
    with open("config.json", "r") as f:
        return json.load(f)

def clean_html(raw_html):
    """Strips HTML tags and unescapes entities from API snippets."""
    clean_text = re.sub(r'<[^>]+>', '', raw_html)
    return html.unescape(clean_text).strip()

def build_search_queries(target_roles, chunk_size=4):
    """Dynamically builds Google OR queries from the target_roles list in config.json."""
    queries = []
    # Quote each role for exact/clean match, then group them in chunks
    for i in range(0, len(target_roles), chunk_size):
        chunk = target_roles[i:i + chunk_size]
        query_str = " OR ".join([f'"{role}"' for role in chunk])
        queries.append(query_str)
    return queries

def fetch_live_google_jobs(config):
    api_key = os.environ.get("GOOGLE_API_KEY")
    cx = os.environ.get("GOOGLE_CX")
    
    if not api_key or not cx:
        print("Error: Missing GOOGLE_API_KEY or GOOGLE_CX secret.")
        return []

    matched_jobs = []
    
    # Dynamically generate queries from config.json
    target_roles = config.get("target_roles", [])
    if not target_roles:
        print("Warning: No target_roles found in config.json")
        return []
        
    search_queries = build_search_queries(target_roles, chunk_size=4)
    url = "https://www.googleapis.com/customsearch/v1"

    for query in search_queries:
        params = {
            "key": api_key,
            "cx": cx,
            "q": query,
            "dateRestrict": "d7",  # Set to d7 to ensure Google captures recently indexed listings
            "num": 10
        }
        
        try:
            res = requests.get(url, params=params, timeout=10)
            if res.status_code != 200:
                print(f"API Error ({res.status_code}): {res.text}")
                continue
                
            data = res.json()
            items = data.get("items", [])
            
            for item in items:
                title = clean_html(item.get("title", ""))
                link = item.get("link", "")
                snippet = clean_html(item.get("snippet", ""))
                
                # Exclude unwanted roles
                if any(bad.lower() in title.lower() or bad.lower() in snippet.lower() for bad in config.get("excluded_keywords", [])):
                    continue
                
                # Basic location detection from snippet, title, or link text
                detected_loc = "Not Specified"
                for loc in config.get("locations", []):
                    if loc.lower() in title.lower() or loc.lower() in snippet.lower() or loc.lower() in link.lower():
                        detected_loc = loc
                        break

                matched_jobs.append({
                    "title": title,
                    "link": link,
                    "snippet": snippet[:180] + "..." if len(snippet) > 180 else snippet,
                    "location": detected_loc
                })
        except Exception as e:
            print(f"Failed to fetch search results: {e}")
            
    return matched_jobs

def send_telegram_digest(jobs):
    bot_token = os.environ.get("TELEGRAM_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("Error: Missing Telegram secrets.")
        return

    if not jobs:
        message = "🌅 *Daily Job Briefing*\n\nNo fresh matching roles found in Google Search over the past 7 days."
    else:
        # Deduplicate results by URL
        seen_links = set()
        unique_jobs = []
        for j in jobs:
            if j['link'] not in seen_links:
                seen_links.add(j['link'])
                unique_jobs.append(j)

        message = f"🌅 *Live Search Job Briefing: {len(unique_jobs)} Roles Found*\n\n"
        for i, job in enumerate(unique_jobs[:8], 1): # Top 8 listings
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
            
            message += f"*{i}. {clean_title}*\n"
            message += f"📍 *Location:* {job['location']}\n"
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
    jobs = fetch_live_google_jobs(config)
    send_telegram_digest(jobs)