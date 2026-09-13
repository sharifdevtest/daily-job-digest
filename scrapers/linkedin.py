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
    """Scrapes public LinkedIn guest job search results for UAE IT Leadership roles."""
    jobs = []
    # Querying LinkedIn's public job search endpoint for IT/QA roles in Dubai/UAE
    url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords=IT%20QA%20Manager&location=Dubai%2C%20United%20Arab%20Emirates&f_TPR=r604800"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=15)
        print(f"[Debug] LinkedIn Public HTTP Status: {res.status_code}")
        if res.status_code != 200:
            return jobs
            
        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.select("li, div.base-card")
        print(f"[Debug] LinkedIn Public: {len(cards)} card containers found.")
        
        for card in cards:
            title_elem = card.select_one("h3.base-search-card__title, h3")
            link_elem = card.select_one("a.base-card__full-link, a")
            date_elem = card.select_one("time")
            
            if title_elem and link_elem:
                title = clean_text(title_elem.get_text())
                href = link_elem.get("href", "").split('?')[0]  # Clean tracking parameters
                posted_date = clean_text(date_elem.get_text()) if date_elem else "Recently Posted"
                
                if title and href:
                    jobs.append({
                        "title": title,
                        "link": href,
                        "snippet": "Direct LinkedIn job posting listing.",
                        "posted_date": posted_date,
                        "source": "LinkedIn"
                    })
    except Exception as e:
        print(f"[Error] LinkedIn public scraping failed: {e}")
        
    return jobs