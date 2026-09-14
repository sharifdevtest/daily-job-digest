# Scrapers Subdirectory Instructions

This directory contains the scraping engine and job site modules for the **Executive QA/IT Job Tracker**.

## Architectural Role

All job site scrapers reside here. They are dynamically imported and executed by the main pipeline (`main.py`). The scrapers fetch job postings directly from targeted recruitment portals and platform APIs.

---

## 🛠️ Scraper Module Specifications

To keep the pipeline robust and maintainable, all scrapers must strictly adhere to the following conventions:

### 1. Unified Interface
Every scraper module **must** implement a zero-argument `scrape()` function as its primary entry point.
```python
def scrape() -> list[dict]:
    """
    Scrapes the target job board and returns a list of standardized job dictionaries.
    """
```

### 2. Standard Output Format
The `scrape()` function must return a list of dictionary items representing the scraped jobs. Each job dictionary must match the following schema:
```python
{
    "title": str,        # Job title (optionally includes company name in parentheses)
    "link": str,         # Direct URL to the job posting (absolute path, stripped of trackers)
    "snippet": str,      # Short summary or description snippet (truncated to 180 chars max)
    "posted_date": str,  # Raw date or relative age of the job post (e.g., "Recently Posted", "3 days ago")
    "source": str        # Standardized source identifier (e.g., "Adecco ME", "LinkedIn")
}
```

### 3. Reliable Scraping Design Patterns
* **User-Agent & Headers:** Always include a modern `User-Agent` header to prevent requests from being blocked by default user-agent filters.
* **Network Timeouts:** Always supply a strict timeout (e.g., `timeout=15`) in `requests.get()` to prevent hanging processes from stalling the scheduled runner.
* **Text Normalization:** Use a standard whitespace and HTML-entity clean function:
  ```python
  import re
  import html

  def clean_text(text):
      if not text:
          return ""
      clean = re.sub(r'\s+', ' ', text)
      return html.unescape(clean).strip()
  ```
* **Graceful Exception Isolation:** Wrap the entirety of the network fetching and parsing loop in a `try...except` block. A failure on a single website must never crash the entire pipeline run. Return an empty list `[]` on failure.

---

## 🚀 Adding and Registering a New Scraper

To add support for a new recruitment portal:

1. **Create the file:** Add a new `.py` file inside the `scrapers/` folder (e.g., `scrapers/monster.py`).
2. **Implement `scrape()`:** Follow the module specifications above.
3. **Register in `main.py`:**
   * Import the new scraper function at the top of `main.py`:
     ```python
     from scrapers.monster import scrape as scrape_monster
     ```
   * Update the runner sequence in `main.py` (inside the execution list or orchestration logic) to execute `scrape_monster()` and collect its results.

---

## ⚠️ Important Scraper Safeguards
* **Anti-Scraping / Rate Limits:** For crawlers making multiple sequential queries (e.g. LinkedIn), introduce slight delays (`time.sleep(0.5)`) to reduce block rates and practice good web citizenship.
* **Tracking Parameter Removal:** Strip redundant tracking query parameters (e.g., `?utm_source=...`) from absolute URLs to ensure accurate duplicate prevention based on URLs.
