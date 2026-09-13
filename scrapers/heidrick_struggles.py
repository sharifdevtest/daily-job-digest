import requests
from bs4 import BeautifulSoup

def scrape():
    jobs = []
    url = "https://www.heidrick.com/en/careers"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            articles = soup.find_all(["article", "div"], class_=lambda c: c and ("career" in c.lower() or "job" in c.lower()))
            for art in articles:
                link_tag = art.find("a")
                if link_tag and link_tag.get("href"):
                    title = link_tag.get_text(strip=True)
                    href = link_tag["href"]
                    if len(title) > 4:
                        full_link = href if href.startswith("http") else f"https://www.heidrick.com{href}"
                        jobs.append({
                            "title": title,
                            "link": full_link,
                            "source": "Heidrick & Struggles",
                            "posted_date": "Recently",
                            "snippet": "Heidrick & Struggles Executive Listing"
                        })
    except Exception as e:
        print(f"[Scraper Error] Heidrick & Struggles scrape failed: {e}")
        
    return jobs