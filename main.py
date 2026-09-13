import json
import os
import hashlib
from db import get_db_connection, init_db
from extractors import extract_salary, extract_hiring_manager

# Import active scrapers from scrapers directory
from scrapers.michael_page import scrape as scrape_michael_page
from scrapers.hays import scrape as scrape_hays
from scrapers.adecco import scrape as scrape_adecco
from scrapers.randstad import scrape as scrape_randstad
from scrapers.charterhouse import scrape as scrape_charterhouse
from scrapers.linkedin import scrape as scrape_linkedin

def load_config():
    """Loads configuration directly from config.json."""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def filter_jobs(raw_jobs, config):
    """Filters listings strictly for IT/QA leadership roles[cite: 1]."""
    filtered = []
    excluded = [k.lower() for k in config.get("excluded_keywords", [])]
    target_roles = [r.lower() for r in config.get("target_roles", [])]
    
    seen_links = set()
    for job in raw_jobs:
        if job["link"] in seen_links:
            continue
            
        title_lower = job["title"].lower()
        if any(bad in title_lower for bad in excluded):
            continue
            
        if any(role in title_lower for role in target_roles):
            seen_links.add(job["link"])
            filtered.append(job)
            
    return filtered

def upsert_to_turso(jobs):
    """Inserts new filtered jobs into Turso Cloud DB with status = 'NEW'."""
    conn = get_db_connection()
    conn.sync()
    cursor = conn.cursor()
    new_jobs = []
    
    for job in jobs:
        job_id = hashlib.md5(job['link'].encode('utf-8')).hexdigest()
        
        cursor.execute("SELECT id FROM job_applications WHERE id = ?", (job_id,))
        if not cursor.fetchone():
            raw_text = f"{job['title']} {job.get('snippet', '')}"
            salary = extract_salary(raw_text)
            manager = extract_hiring_manager(raw_text)
            
            cursor.execute("""
                INSERT INTO job_applications (id, title, company, location, url, source, status, salary_range, hiring_manager)
                VALUES (?, ?, ?, ?, ?, ?, 'NEW', ?, ?)
            """, (
                job_id,
                job['title'],
                job.get('company', 'Agency/Executive Search'),
                job.get('location', 'GCC / India'),
                job['link'],
                job['source'],
                salary,
                manager
            ))
            new_jobs.append(job)
            
    conn.commit()
    conn.sync()
    conn.close()
    return new_jobs

if __name__ == "__main__":
    init_db()
    config = load_config()
    
    raw_jobs = []
    raw_jobs.extend(scrape_michael_page())
    raw_jobs.extend(scrape_hays())
    raw_jobs.extend(scrape_adecco())
    raw_jobs.extend(scrape_randstad())
    raw_jobs.extend(scrape_charterhouse())
    raw_jobs.extend(scrape_linkedin())
    
    filtered_jobs = filter_jobs(raw_jobs, config)
    new_matched_jobs = upsert_to_turso(filtered_jobs)
    
    print(f"Processed {len(raw_jobs)} total. Saved {len(new_matched_jobs)} new IT/QA matches to Turso.")