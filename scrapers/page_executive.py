import requests

def scrape():
    jobs = []
    # Direct search endpoint for Page Executive India/Global roles
    url = "https://www.pageexecutive.com/api/v1/jobs/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }
    params = {
        "page": 0,
        "size": 25,
        "sort": "postedDate,desc"
    }
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            items = data.get("content", []) or data.get("jobs", [])
            for item in items:
                title = item.get("title") or item.get("jobTitle")
                link_path = item.get("url") or item.get("link")
                if title and link_path:
                    full_link = link_path if link_path.startswith("http") else f"https://www.pageexecutive.com{link_path}"
                    jobs.append({
                        "title": title,
                        "link": full_link,
                        "source": "Page Executive",
                        "posted_date": item.get("postedDate", "Recently"),
                        "snippet": item.get("summary", "Executive & C-Suite Opportunity")
                    })
    except Exception as e:
        print(f"[Scraper Error] Page Executive API failed: {e}")
        
    return jobs