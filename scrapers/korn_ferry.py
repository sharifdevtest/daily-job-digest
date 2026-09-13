import requests
from bs4 import BeautifulSoup

def scrape():
    jobs = []
    url = "https://www.kornferry.com/careers"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            for card in soup.find_all(["div", "article"], class_=lambda c: c and "job" in c.lower()):
                title_elem = card.find(["h2", "h3", "a"])
                link_elem = card.find("a")
                
                if title_elem and link_elem and link_elem.get("href"):
                    href = link_elem["href"]
                    full_link = href if href.startswith("http") else f"https://www.kornferry.com{href}"
                    jobs.append({
                        "title": title_elem.get_text(strip=True),
                        "link": full_link,
                        "source": "Korn Ferry",
                        "posted_date": "Recently",
                        "snippet": "Executive Leadership Role / GCC Focus"
                    })
    except Exception as e:
        print(f"[Scraper Warning] Korn Ferry scrape error: {e}")
        
    return jobs