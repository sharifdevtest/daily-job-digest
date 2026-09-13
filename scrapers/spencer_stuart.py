import requests
from bs4 import BeautifulSoup

def scrape():
    jobs = []
    url = "https://www.spencerstuart.com/opportunities"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            listings = soup.find_all("a", class_=lambda c: c and "opportunity" in c.lower())
            for item in listings:
                title = item.get_text(strip=True)
                href = item.get("href")
                if title and href:
                    full_link = href if href.startswith("http") else f"https://www.spencerstuart.com{href}"
                    jobs.append({
                        "title": title,
                        "link": full_link,
                        "source": "Spencer Stuart",
                        "posted_date": "Recently",
                        "snippet": "Spencer Stuart Leadership Mandate"
                    })
    except Exception as e:
        print(f"[Scraper Error] Spencer Stuart scrape failed: {e}")
        
    return jobs