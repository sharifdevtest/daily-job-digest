import requests
from bs4 import BeautifulSoup
import re
import html
import time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def clean_text(text):
    if not text:
        return ""
    clean = re.sub(r'\s+', ' ', text)
    return html.unescape(clean).strip()

def scrape():
    """Scrapes public LinkedIn guest job search results for standard and executive IT/QA leadership roles."""
    jobs = []
    seen_links = set()
    base_api = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

    # Search queries: Regular leadership + Executive retained search firms
    queries = [
        # Standard Target Roles
        "IT%20QA%20Manager",
        "Head%20of%20Quality%20Assurance",
        "VP%20Engineering",
        "Director%20of%20Software%20Quality",
        "GCC%20Tech%20Lead",
        
        # Executive Search Firm Targeted Queries
        "%22Korn%20Ferry%22%20AND%20(%22Director%22%20OR%20%22Head%22%20OR%20%22VP%20Engineering%22)",
        "%22Page%20Executive%22%20AND%20(%22QA%22%20OR%20%22Technology%22%20OR%20%22Engineering%22)",
        "%22Heidrick%22%20AND%20(%22Director%22%20OR%20%22Head%22%20OR%20%22GCC%22)",
        "%22Spencer%20Stuart%22%20AND%20(%22Director%22%20OR%20%22Head%22%20OR%20%22VP%22)",
        "%22Sheffield%20Haworth%22%20AND%20(%22Director%22%20OR%20%22Head%22%20OR%20%22Technology%22)"
    ]

    # Target Geographies
    locations = [
        "Dubai%2C%20United%20Arab%20Emirates",
        "India",
        "Saudi%20Arabia"
    ]

    for location in locations:
        for keyword in queries:
            url = f"{base_api}?keywords={keyword}&location={location}&f_TPR=r604800"
            
            try:
                res = requests.get(url, headers=HEADERS, timeout=15)
                print(f"[Debug] LinkedIn Public Query '{keyword[:25]}...' in {location[:10]}: HTTP {res.status_code}")
                
                if res.status_code != 200:
                    continue
                    
                soup = BeautifulSoup(res.text, "html.parser")
                cards = soup.select("li, div.base-card")
                
                for card in cards:
                    title_elem = card.select_one("h3.base-search-card__title, h3")
                    company_elem = card.select_one("h4.base-search-card__subtitle, h4")
                    link_elem = card.select_one("a.base-card__full-link, a")
                    date_elem = card.select_one("time")
                    
                    if title_elem and link_elem:
                        title = clean_text(title_elem.get_text())
                        company = clean_text(company_elem.get_text()) if company_elem else ""
                        raw_href = link_elem.get("href", "")
                        href = raw_href.split('?')[0]  # Strip tracking parameters
                        
                        # Avoid duplicates within the same execution run
                        if href in seen_links or not href:
                            continue
                            
                        seen_links.add(href)
                        posted_date = clean_text(date_elem.get_text()) if date_elem else "Recently Posted"
                        
                        # Highlight firm name if present
                        full_title = f"{title} ({company})" if company else title
                        snippet_text = f"Executive/Leadership posting on LinkedIn"
                        if company:
                            snippet_text += f" via {company}."
                        else:
                            snippet_text += "."

                        jobs.append({
                            "title": full_title,
                            "link": href,
                            "snippet": snippet_text,
                            "posted_date": posted_date,
                            "source": "LinkedIn"
                        })
                        
            except Exception as e:
                print(f"[Warning] LinkedIn search error for {keyword}: {e}")
                
            # Slight sleep to respect rate limits during multi-query iteration
            time.sleep(0.5)

    print(f"[Debug] LinkedIn Total Collected: {len(jobs)} unique matches across queries.")
    return jobs