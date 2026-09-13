import requests
from bs4 import BeautifulSoup

def scrape():
    jobs = []
    url = "https://www.kornferry.com/careers"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, "html.parser")
            # Target specific job card markup elements
            cards = soup.select("a[href*='/careers/'], div.job-card, article.career-item")
            for card in cards:
                title = card.get_text(strip=True)
                href = card.get("href") or (card.find("a")["href"] if card.find("a") else None)
                if href and len(title) > 5:
                    full_link = href if href.startswith("http") else f"https://www.kornferry.com{href}"
                    jobs.append({
                        "title": title,
                        "link": full_link,
                        "source": "Korn Ferry",
                        "posted_date": "Recently",
                        "snippet": "Korn Ferry Executive Search Listing"
                    })
    except Exception as e:
        print(f"[Scraper Error] Korn Ferry scrape failed: {e}")
        
    return jobs