import requests
from bs4 import BeautifulSoup
import re
import html

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_text(text):
    if not text:
        return ""
    clean = re.sub(r'\s+', ' ', text)
    return html.unescape(clean).strip()

def scrape():
    """Scrapes active job listings from Hays Middle East."""
    jobs = []
    url = "https://www.hays.ae/job-search"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        print(f"[Debug] Hays HTTP Status: {res.status_code}")
        if res.status_code != 200:
            return jobs
            
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select("div.job-card, article.job-tile, li.search-result, .job-description")
        print(f"[Debug] Hays: {len(cards)} card containers found.")
        
        for card in cards:
            title_elem = card.select_one("h3 a, h2 a, a.job-title, a[href*='/job-details/']")
            snippet_elem = card.select_one(".job-summary, .description, p")
            date_elem = card.select_one(".posted-date, time, span[class*='date']")
            
            if title_elem:
                title = clean_text(title_elem.get_text())
                href = title_elem.get("href", "")
                if href and not href.startswith("http"):
                    href = f"https://www.hays.ae{href}"
                    
                snippet = clean_text(snippet_elem.get_text()) if snippet_elem else "View job details on site."
                posted_date = clean_text(date_elem.get_text()) if date_elem else "Recently Posted"
                
                if title and href:
                    jobs.append({
                        "title": title,
                        "link": href,
                        "snippet": snippet[:180] + "..." if len(snippet) > 180 else snippet,
                        "posted_date": posted_date,
                        "source": "Hays"
                    })
    except Exception as e:
        print(f"[Error] Hays scraping failed: {e}")
        
    return jobs