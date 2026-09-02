# 🛡 HirePulse Monitoring & Maintenance Operations Guide

This guide provides system administrators and engineers with the operational procedures, health checks, log analysis protocols, performance tuning configurations, and scaling strategies required to maintain the **HirePulse 4-Layer Universal Job Engine** in production.

---

## 📑 Table of Contents
1. [Logging Strategy & Telemetry](#1-logging-strategy--telemetry)
2. [Health Checks & Observability](#2-health-checks--observability)
3. [Routine Maintenance Schedule](#3-routine-maintenance-schedule)
4. [Performance Optimization & Tuning](#4-performance-optimization--tuning)
5. [Scaling & Extension Playbook](#5-scaling--extension-playbook)
6. [Emergency Incident Response](#6-emergency-incident-response)

---

## 1. 📝 Logging Strategy & Telemetry

### Log Level Standards
The engine strictly adopts the standard Python `logging` hierarchy:
- **`INFO`**: Normal operations, task lifecycle progress (e.g., `"Fetched 30 jobs from LinkedIn Guest API in 2.1s"`).
- **`WARNING`**: Non-fatal scrape degradation or fallback trigger (e.g., `"Naukri JSON API returned 406; invoking Scrapling fallback"`, `"Cutshort placeholder endpoint returned 404"`).
- **`ERROR`**: Critical network failure, unhandled parser exception, or database corruption that impacts pipeline execution.

### Standard Log Format
All loggers output unified structured telemetry:
```text
%(asctime)s [%(levelname)s] %(name)s: %(message)s
```
*Example Console Output:*
```text
2026-09-02 23:18:11,091 [INFO] fetchers.boards.enhanced.jobspy_wrapper: JobSpy: Retrieved DataFrame with 80 rows across sites
2026-09-02 23:18:12,341 [INFO] core.orchestrator: Filtered jobs passing Role, Location & Experience checks: 38
2026-09-02 23:18:12,374 [INFO] hirepulse.api: <-- [GET] /api/jobs completed with HTTP 200 in 23.77ms
```

### Log Storage & Forwarding
- **Standard Out / Console**: Captured directly by `uvicorn` and container supervisors (Docker, PM2, systemd).
- **File Logging (Optional)**: To persist logs to disk, configure a `RotatingFileHandler` in `main.py`:
  ```python
  import logging
  from logging.handlers import RotatingFileHandler

  file_handler = RotatingFileHandler("backend/logs/hirepulse.log", maxBytes=10*1024*1024, backupCount=5)
  file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
  logging.getLogger().addHandler(file_handler)
  ```

---

## 2. 🩺 Health Checks & Observability

### 2.1 Automated Health Endpoints
- **Liveness Probe**:
  ```bash
  curl http://localhost:8000/health
  # Expected Response: {"status": "healthy", "timestamp": "...", "service": "HirePulse Backend"}
  ```
- **Live Scraper Telemetry Probe**:
  ```bash
  curl "http://localhost:8000/api/debug/live?role=Frontend%20Developer&location=Bangalore"
  ```
  Returns live raw counts across all direct sources without seed data.

### 2.2 Cache Statistics & Health Inspection
The SQLite cache is stored in `backend/hirepulse_cache.db`. To inspect the cache health:

```bash
cd backend
py -3.11 -c "
import sqlite3, json
conn = sqlite3.connect('hirepulse_cache.db')
c = conn.cursor()
c.execute('SELECT COUNT(*) FROM job_cache')
total_entries = c.fetchone()[0]

c.execute('SELECT cache_key, fetched_at, expires_at, length(jobs_json) FROM job_cache')
rows = c.fetchall()

print(f'Total Cache Keys: {total_entries}')
for r in rows:
    print(f'  Key: {r[0]:<40} | Fetched: {r[1]} | Size: {r[3]/1024:.1f} KB')
conn.close()
"
```

### 2.3 Source Breakdown Verification
Run the validation script to view real-time source distribution:
```bash
cd backend
py -3.11 test_orchestrator.py
```
Check that the **Sources Breakdown** displays active postings across:
- `LinkedIn-GuestAPI`
- `Greenhouse`
- `internshala`
- `Workday`
- `JobSpy-Indeed`

---

## 3. 📅 Routine Maintenance Schedule

| Cadence | Task | File / Component | Action |
|---|---|---|---|
| **Daily** | Job Count Monitoring | `test_orchestrator.py` | Verify that total returned jobs remain **>= 30** for standard queries. |
| **Weekly** | Selector Integrity Check | `fetchers/indian/`, `fetchers/boards/enhanced/` | Run isolated fetcher tests to check if portals changed class names. |
| **Monthly (1st)** | Update HN Hiring Thread ID | `fetchers/json_apis/hackernews.py` | Update `DEFAULT_HN_THREAD_ID` to the new monthly post on Hacker News. |
| **As Needed** | Cache Flush | `hirepulse_cache.db` | Purge expired or stale records when testing new matching algorithms. |

### How to Update Hacker News Thread ID
1. On the 1st of each month, visit [Hacker News](https://news.ycombinator.com/submitted?id=whoishiring) and open the new *"Ask HN: Who is hiring?"* post.
2. Note the ID from the URL (`https://news.ycombinator.com/item?id=XXXXXX`).
3. In [`backend/fetchers/json_apis/hackernews.py`](file:///c:/Users/mohan/Downloads/Hire%20Pulse/backend/fetchers/json_apis/hackernews.py):
   ```python
   DEFAULT_HN_THREAD_ID = XXXXXX  # Update with new monthly ID
   ```
*(Note: The fetcher includes automatic Algolia fallback if this ID is omitted or empty).*

### How to Flush Cache
```bash
# Clear specific query key
py -3.11 -c "from core.cache.job_cache import clear; clear('frontend_developer_bangalore_fresher')"

# Clear all expired entries
py -3.11 -c "from core.cache.job_cache import clear_expired; clear_expired()"

# Hard reset: Delete database
rm backend/hirepulse_cache.db
```

---

## 4. 🚀 Performance Optimization & Tuning

### 4.1 Modifying Cache TTL
By default, query results are cached for **6 hours**. To adjust the TTL:
- File: [`backend/core/orchestrator.py`](file:///c:/Users/mohan/Downloads/Hire%20Pulse/backend/core/orchestrator.py)
- Search for `cache_set(...)`:
  ```python
  # Change ttl_hours to your desired window (e.g. 2 hours or 12 hours)
  cache_set(cache_key, ranked_jobs, ttl_hours=6)
  ```

### 4.2 Adjusting Scraper HTTP Timeouts
If running on a slower internet connection or high-latency network:
- **`aiohttp` Fetchers** (`remoteok.py`, `hackernews.py`, `cutshort.py`, `linkedin_enhanced.py`):
  ```python
  timeout = aiohttp.ClientTimeout(total=25)  # Increase from 12s/20s to 25s/30s
  ```
- **`httpx` Fetchers** (`workday.py`, `lever.py`, `greenhouse.py`):
  ```python
  async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
  ```

### 4.3 Scaling Scraping Depth (Pagination)
To increase candidate pool volume:
- **LinkedIn Enhanced** ([`linkedin_enhanced.py`](file:///c:/Users/mohan/Downloads/Hire%20Pulse/backend/fetchers/boards/enhanced/linkedin_enhanced.py)):
  ```python
  # Increase pages from 3 to 5 (fetches 125 candidate cards)
  async def fetch_linkedin_guest_api(..., pages: int = 5):
  ```
- **Indeed Boolean** ([`indeed_enhanced.py`](file:///c:/Users/mohan/Downloads/Hire%20Pulse/backend/fetchers/boards/enhanced/indeed_enhanced.py)):
  ```python
  # Increase pages from 3 to 5 (fetches 50 candidate cards)
  async def fetch_indeed_boolean_query(..., pages: int = 5):
  ```
- **Internshala** ([`internshala.py`](file:///c:/Users/mohan/Downloads/Hire%20Pulse/backend/fetchers/indian/internshala.py)):
  ```python
  # Increase scraped pages from 3 to 5 (fetches up to 250 candidate cards)
  ```

---

## 5. 📈 Scaling & Extension Playbook

### 5.1 Adding New ATS Companies
To add new tracked companies to Lever, Greenhouse, Ashby, or Workday:
1. Open [`backend/fetchers/companies.py`](file:///c:/Users/mohan/Downloads/Hire%20Pulse/backend/fetchers/companies.py).
2. Append the company slug to the respective list:
   ```python
   # To add a Lever company:
   LEVER_COMPANIES.append("new_company_slug")

   # To add a Workday company:
   WORKDAY_COMPANIES.append({
       "company_name": "NewCo",
       "domain": "newco.wd1.myworkdayjobs.com",
       "wd_identifier": "External",
       "company": "NewCo",
       "url": "https://newco.wd1.myworkdayjobs.com/wday/cxs/newco/External/jobs",
       "base_link": "https://newco.wd1.myworkdayjobs.com/en-US/External"
   })
   ```

### 5.2 Adding a Brand New Fetcher
To register a new job board (e.g. Wellfound or Hirist):
1. Create `backend/fetchers/indian/hirist.py`.
2. Implement an async function returning standardized job dicts:
   ```python
   async def fetch_hirist_jobs(role: str, location: str, exp: str) -> List[Dict[str, Any]]:
       ...
       return [{"title": ..., "company": ..., "location": ..., "apply_link": ..., "source": "hirist"}]
   ```
3. Export from `backend/fetchers/indian/__init__.py`.
4. Add the task into [`backend/core/orchestrator.py`](file:///c:/Users/mohan/Downloads/Hire%20Pulse/backend/core/orchestrator.py):
   ```python
   layer2_tasks.append(fetch_hirist_jobs(role, location, exp))
   ```

### 5.3 Implementing Proxy Rotation
If external portals begin blocking cloud IPs:
1. **In `aiohttp` Sessions**:
   ```python
   async with aiohttp.ClientSession() as session:
       async with session.get(url, proxy="http://user:pass@proxy.provider.com:8080") as resp:
   ```
2. **In `JobSpy`**:
   Pass proxy lists via `proxies` parameter:
   ```python
   scrape_jobs(..., proxies=["http://proxy1:port", "http://proxy2:port"])
   ```
3. **In `Scrapling`**:
   Configure proxy support in `StealthyFetcher`:
   ```python
   fetcher = StealthyFetcher(headless=True, proxy="http://proxy:port")
   ```

---

## 6. 🚨 Emergency Incident Response

| Symptom | Probable Cause | Corrective Action |
|---|---|---|
| **Results return 0 jobs** | Strict filters too restrictive or network outage | Check logs for `Filtered jobs passing Role, Location & Experience checks`. Relax filters or inspect network. |
| **HTTP 406 on Naukri API** | Cloudflare WAF block | Automated fallback to `naukri_scrapling` and `JobSpy` handles this seamlessly. No action required. |
| **`ERR_NAME_NOT_RESOLVED` on Indeed** | Regional DNS failure on `in.indeed.com` | `indeed_enhanced.py` automatically falls back to `www.indeed.com`. |
| **Playwright / Scrapling error** | Missing browser binaries or `msgspec` | Run `py -3.11 -m playwright install` and `py -3.11 -m pip install msgspec`. |
| **Windows Console `charmap` error** | Unhandled Unicode Rupee sign `₹` in standard output | Ensure `sys.stdout.reconfigure(encoding="utf-8")` is included at script entry. |

