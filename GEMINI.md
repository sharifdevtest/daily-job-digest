# Executive QA/IT Job Tracker (Daily Job Digest)

Welcome to the **Executive QA/IT Job Tracker** developer instructions manual. This file serves as the team's guide to the project's architecture, workflows, database models, and coding standards.

---

## 🛠️ Project Tech Stack

* **Frontend Dashboard:** Streamlit
* **Database Driver:** LibSQL (SQL-compatible client connecting to a Turso database)
* **Web Scraping & Parsing:** BeautifulSoup4, Requests, Regex
* **Data Handling:** Pandas, JSON
* **Environment Management:** python-dotenv

---

## 📂 Codebase Architecture & File Structure

The project directory is structured as follows:

* **`app.py`:** The Streamlit dashboard. It queries the local or remote Turso DB to display active target roles divided by application status queues (`NEW`, `IN_PROGRESS`, `APPLIED`, `CLOSED`). It provides an expandable editor to update salary estimates, contact information, next-step notes, and application status.
* **`main.py`:** The primary crawler pipeline orchestrator. It executes the scrapers, aggregates raw job items, filters jobs using lists defined in `config.json`, extracts missing fields via regex-based extractors, and executes an upsert logic (`upsert_to_turso`) to avoid duplicate entries.
* **`db.py`:** Connects to the Turso database using LibSQL (referencing environment variables `TURSO_DATABASE_URL` and `TURSO_AUTH_TOKEN`). It defines the schema and handles DB/table initializations.
* **`extractors.py`:** Standardized regex extraction utilities for extracting salary ranges, recruiter/hiring manager names, and candidate contact emails from job description strings.
* **`config.json`:** Core crawler parameters containing lists of target roles, inclusion keywords (domain triggers, leadership keywords), and excluded terms (e.g., "junior", "intern") to filter relevant opportunities.
* **`reset_db.py`:** A maintenance script designed to wipe and recreate the database table. It accepts the `--force` flag for headless/CI runs.
* **`scrapers/`:** Directory containing specialized scraper modules for individual platforms.
  * *See [scrapers/GEMINI.md](scrapers/GEMINI.md) for detailed subdirectory rules, interface models, and scraper registration guidelines.*

---

## 🔄 Core Developer Workflows

### 1. Database Initialization & Configuration
Before executing any script, ensure local environment variables are set in a `.env` file:
```bash
TURSO_DATABASE_URL=your-turso-database-url
TURSO_AUTH_TOKEN=your-turso-auth-token
```

To initialize the database table:
```bash
python db.py
```

### 2. Running the Scraper Pipeline
To trigger standard platform crawlers, filter newly scraped jobs, run modular extractors, and sync results to Turso DB:
```bash
python main.py
```

### 3. Launching the Streamlit Web Application
To run the interactive tracking dashboard in your local browser:
```bash
streamlit run app.py
```

### 4. Wiping and Recreating the Database
To hard-reset the Turso database table:
* **Interactive:** Run `python reset_db.py` and confirm prompt.
* **Automated/CI:** Use `python reset_db.py --force`.

---

## 💾 Database Schema

The `job_applications` table is structured in Turso as follows:

| Column Name | SQLite / LibSQL Type | Description / Constraints |
| :--- | :--- | :--- |
| `id` | `TEXT` | **Primary Key** (Generated as an MD5 hash of the direct job URL) |
| `title` | `TEXT` | Job title (and optionally company name) |
| `company` | `TEXT` | Employing company or recruitment agency |
| `location` | `TEXT` | Geographical location of the job |
| `url` | `TEXT` | Absolute link to the listing |
| `source` | `TEXT` | Source board name (e.g., `LinkedIn`, `Adecco ME`) |
| `status` | `TEXT` | State of application: `NEW`, `IN_PROGRESS`, `APPLIED`, `CLOSED` |
| `salary_range` | `TEXT` | Parsed salary bracket |
| `hiring_manager`| `TEXT` | Extracted recruiter or contact person's name |
| `contact_email` | `TEXT` | Direct email address found in the description text |
| `created_at` | `DATETIME` | Automatic timestamp generated on first insert |
| `last_seen_at` | `DATETIME` | Updated timestamp whenever a matching URL is re-scraped |

> **Note on Upsert/Update Logic:** When a job is re-scraped, the system only updates empty metadata fields if a valid value is discovered. It never overwrites manually updated attributes.

---

## 📌 Coding Standards and Best Practices

### Exception Handling
* **Isolate Failures:** Never allow a failure in an individual scraper block to crash the broader pipeline. Standardize try-except limits around external network calls.
* **Database Connections:** Always close database connections in a `finally` block or clean context manager to prevent connection exhaustion.

### LibSQL Sync Protocol
* When writing or reading data using Streamlit (`app.py`), remember to invoke `conn.sync()` after transaction commits to ensure that local database states are completely synchronized with your remote Turso cloud database.

### Filtering Logic Rules
The filtering mechanism in `main.py` is entirely dynamic:
1. Match raw jobs against `excluded_keywords` in `config.json`. If a match is found, immediately discard.
2. Allow jobs matching any exact keyword in `target_roles`.
3. Allow jobs containing at least one `leadership_keywords` keyword AND at least one `domain_triggers` keyword.
