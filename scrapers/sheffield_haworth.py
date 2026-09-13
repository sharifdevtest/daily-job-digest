import requests
from bs4 import BeautifulSoup

def scrape():
    jobs = []
    url = "https://www.sheffieldhaworth.com/careers/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            post_links = soup.select("h2.entry-title a, h3.entry-title a, a.job-apply-link")
            for link in post_links:
                title = link.get_text(strip=True)
                href = link.get("href")
                if title and href:
                    jobs.append({
                        "title": title,
                        "link": href,
                        "source": "Sheffield Haworth",
                        "posted_date": "Recently",
                        "snippet": "Sheffield Haworth BFSI / Tech Advisory Role"
                    })
    except Exception as e:
        print(f"[Scraper Error] Sheffield Haworth scrape failed: {e}")
        
    return jobs