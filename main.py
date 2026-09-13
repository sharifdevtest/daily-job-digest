import json
import os
import hashlib
import re
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
    """
    100% Dynamic job filter reading all criteria directly from config.json.
    Requires: (Exact Match OR (Leadership Token AND Domain Token)) AND NOT Excluded
    """
    filtered = []
    
    # Read lists dynamically from config.json
    excluded = [k.lower().strip() for k in config.get("excluded_keywords", [])]
    target_roles = [r.lower().strip() for r in config.get("target_roles", [])]
    domain_keywords = [d.lower().strip() for d in config.get("domain_triggers", [])]
    leadership_keywords = [l.lower().strip() for l in config.get("leadership_keywords", [])]
    
    # Token sets derived directly from config
    leadership_tokens = set(leadership_keywords)
    domain_tokens = set(domain_keywords)

    seen_links = set()
    for job in raw_jobs:
        link = job.get("link", "")
        if not link or link in seen_links:
            continue
            
        title_lower = job.get("title", "").lower()
        title_words = set(re.findall(r'\w+', title_lower))
        
        # Rule 1: Exclude unwanted roles
        if any(bad in title_lower for bad in excluded):
            continue
            
        # Rule 2: Check for exact target role substring match
        matched = any(role in title_lower for role in target_roles)
        
        # Rule 3: Dynamic 2-Way Match (Must have 1 Leadership Token AND 1 Domain Token)
        if not matched:
            has_leadership = bool(leadership_tokens.intersection(title_words))
            has_domain = bool(domain_tokens.intersection(title_words))
            if has_leadership and has_domain:
                matched = True
                
        if matched:
            seen_links.add(link)
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
    
    scrapers = [
        ("Michael Page", scrape_michael_page),
        ("Hays", scrape_hays),
        ("Adecco", scrape_adecco),
        ("Randstad", scrape_randstad),
        ("Charterhouse", scrape_charterhouse),
        ("LinkedIn", scrape_linkedin),
    ]
    
    raw_jobs = []
    for name, scraper_func in scrapers:
        try:
            jobs = scraper_func()
            print(f"[{name}] Extracted {len(jobs)} raw jobs.")
            raw_jobs.extend(jobs)
        except Exception as e:
            print(f"[{name}] Scraper failed: {e}")

    filtered_jobs = filter_jobs(raw_jobs, config)
    print(f"Total raw: {len(raw_jobs)} | Passed filter: {len(filtered_jobs)}")
    
    new_matched_jobs = upsert_to_turso(filtered_jobs)
    print(f"Newly added to Turso: {len(new_matched_jobs)}")