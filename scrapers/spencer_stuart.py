import requests
from bs4 import BeautifulSoup

def scrape():
    jobs = []
    url = "https://www.spencerstuart.com/opportunities"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for item in soup.find_all("div", class_=lambda c: c and ("opportunity" in c.lower() or "job" in c.lower())):
                title = item.find(["h3", "h4", "a"])
                link = item.find("a")
                if title and link and link.get("href"):
                    href = link["href"]
                    full_link = href if href.startswith("http") else f"https://www.spencerstuart.com{href}"
                    jobs.append({
                        "title": title.get_text(strip=True),
                        "link": full_link,
                        "source": "Spencer Stuart",
                        "posted_date": "Recently",
                        "snippet": "Executive Search Search Opportunity"
                    })
    except Exception as e:
        print(f"[Scraper Warning] Spencer Stuart scrape error: {e}")
        
    return jobs