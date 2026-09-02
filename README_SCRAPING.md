# ⚡ HirePulse Multi-Layer Real-Time Scraping & Aggregation Engine

A production-grade, 4-layer concurrent job aggregation system designed for real-time extraction across global and Indian tech ecosystems. **Zero seed/mock data, 100% live fetched postings.**

---

## 📑 Table of Contents
1. [Architecture Overview](#-architecture-overview)
2. [Setup Instructions](#-setup-instructions)
3. [Running Instructions](#-running-instructions)
4. [Individual Fetcher Debugging](#-individual-fetcher-debugging)
5. [Debugging & Maintenance Guide](#-debugging--maintenance-guide)
6. [Expected Output & Response Schema](#-expected-output--response-schema)
7. [Troubleshooting & Selector Updates](#-troubleshooting--selector-updates)

---

## 🏛 Architecture Overview

The HirePulse engine executes **12 specialized fetchers** simultaneously across **4 distinct layers**, prunes duplicates, validates eligibility with strict client-side filters, scores postings with resume skills, and persists results to an SQLite TTL cache:

```mermaid
flowchart TD
    ClientQuery["User Query (Role, Location, Experience)"] --> CacheCheck{"JobCache Hit?"}
    CacheCheck -- "Yes (< 6 Hours)" --> CachedResponse["Return Cached Payload in < 0.05s"]
    CacheCheck -- "No" --> ConcurrentEngine["asyncio.gather across 4 Layers"]

    subgraph Layer 1: Fast JSON APIs
        L1A["RemoteOK API"]
        L1B["Hacker News 'Who is Hiring' API"]
    end

    subgraph Layer 2: Indian Tech Portals
        L2A["Internshala Fresher Scraper"]
        L2B["Cutshort API"]
        L2C["Instahyre Stealth Scraper"]
    end

    subgraph Layer 3: ATS Direct Endpoints
        L3A["Lever API (41+ Companies)"]
        L3B["Greenhouse API (45+ Companies)"]
        L3C["Ashby API (24+ Companies)"]
        L3D["Workday CXS API (22+ Enterprises)"]
    end

    subgraph Layer 4: Enhanced Boards
        L4A["LinkedIn Comprehensive (Guest API + Scrapling + JobSpy)"]
        L4B["Indeed Comprehensive (Boolean Query + Scrapling + JobSpy)"]
        L4C["Naukri Comprehensive (JSON API + Scrapling + JobSpy)"]
    end

    ConcurrentEngine --> Layer 1
    ConcurrentEngine --> Layer 2
    ConcurrentEngine --> Layer 3
    ConcurrentEngine --> Layer 4

    Layer 1 & Layer 2 & Layer 3 & Layer 4 --> Merger["merge_jobs() Deduplication"]
    Merger --> StrictFilters["Strict Client-Side Filters<br/>• Role Match (role_match)<br/>• Location Match (location_match)<br/>• Experience Detection (detect_experience_level)"]
    StrictFilters --> SkillRanker["Resume Skill Matcher & Ranker"]
    SkillRanker --> SQLiteStore["Store in SQLite Cache (6h TTL)"]
    SQLiteStore --> LiveResponse["Return Ranked Results"]
```

---

## 🛠 Setup Instructions

### 1. Python Environment Requirement
> [!IMPORTANT]
> **Use Python 3.11.**
> Python 3.14 on Windows lacks pre-built C wheels for `numpy 1.26.3` (required by `python-jobspy`). Python 3.11 includes complete precompiled binary wheels for Playwright, Scrapling, JobSpy, and curl_cffi.

Verify your installation:
```bash
py -3.11 --version
```

### 2. Directory Structure Setup
Ensure the following directory structure exists in `backend/`:
```
backend/
├── core/
│   ├── cache/
│   │   ├── __init__.py
│   │   └── job_cache.py
│   ├── filters/
│   │   ├── __init__.py
│   │   └── experience_detector.py
│   ├── location_filter.py
│   └── orchestrator.py
├── fetchers/
│   ├── ats/
│   │   ├── __init__.py
│   │   ├── ashby.py
│   │   ├── greenhouse.py
│   │   ├── lever.py
│   │   └── workday.py
│   ├── boards/
│   │   ├── enhanced/
│   │   │   ├── __init__.py
│   │   │   ├── indeed_enhanced.py
│   │   │   ├── jobspy_wrapper.py
│   │   │   ├── linkedin_enhanced.py
│   │   │   └── naukri_enhanced.py
│   │   ├── linkedin_scrapling.py
│   │   ├── indeed_scrapling.py
│   │   └── naukri_scrapling.py
│   ├── indian/
│   │   ├── __init__.py
│   │   ├── cutshort.py
│   │   ├── instahyre.py
│   │   └── internshala.py
│   ├── json_apis/
│   │   ├── __init__.py
│   │   ├── hackernews.py
│   │   └── remoteok.py
│   └── companies.py
├── hirepulse_cache.db        # Auto-generated SQLite cache
├── main.py
├── test_orchestrator.py
└── requirements.txt
```

### 3. Install Dependencies
Run the following from the `backend/` directory:
```bash
cd backend
py -3.11 -m pip install -r requirements.txt
py -3.11 -m pip install msgspec
py -3.11 -m playwright install
```

### 4. API Keys & Configuration
The core scraping architecture is **100% key-free**:
- Lever, Greenhouse, Workday, RemoteOK, Hacker News, Internshala, and LinkedIn Guest APIs operate **without API keys**.
- Optional AI fallback scrapers (Crawl4AI / ScrapeGraph) can read `OPENAI_API_KEY` or `GROQ_API_KEY` from your `.env` file if configured, but are not required for normal operations.

---

## 🚀 Running Instructions

### 1. Run the Validation Test Script
The test script runs the orchestrator, evaluates all 4 layers, verifies cache generation, and writes `backend/test_results.json`:
```bash
cd backend
py -3.11 test_orchestrator.py
```

- **Run 1**: Live scrapes all sources concurrently (~60–75s depending on network speed).
- **Run 2**: Re-running the command immediately returns cached results in **`0.0s`**.

### 2. Start the FastAPI Production Server
To run the full backend API:
```bash
cd backend
py -3.11 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
- **API Documentation**: Open `http://localhost:8000/docs` in your browser.
- **Search Endpoint**: `GET /api/jobs/search?role=Frontend%20Developer&location=Bangalore&exp=fresher`
- **Health Check**: `http://localhost:8000/health`

---

## 🔍 Individual Fetcher Debugging

To isolate and test any individual fetcher without triggering the full orchestrator:

### 1. Test Layer 1: JSON APIs
```bash
# Test RemoteOK
py -3.11 -c "import asyncio; from fetchers.json_apis.remoteok import fetch_remoteok_jobs; jobs = asyncio.run(fetch_remoteok_jobs('Engineer', 'Remote', '2-5')); print('RemoteOK Count:', len(jobs))"

# Test Hacker News Who is Hiring
py -3.11 -c "import asyncio; from fetchers.json_apis.hackernews import fetch_hackernews_jobs; jobs = asyncio.run(fetch_hackernews_jobs('Engineer', 'Remote', 'fresher')); print('HN Count:', len(jobs))"
```

### 2. Test Layer 2: Indian Portals
```bash
# Test Internshala Fresher Scraper
py -3.11 -c "import asyncio; from fetchers.indian.internshala import fetch_internshala_jobs; jobs = asyncio.run(fetch_internshala_jobs('Software Engineer', 'India', 'fresher')); print('Internshala Count:', len(jobs))"

# Test Cutshort
py -3.11 -c "import asyncio; from fetchers.indian.cutshort import fetch_cutshort_jobs; jobs = asyncio.run(fetch_cutshort_jobs('Frontend Developer', 'Bangalore', 'fresher')); print('Cutshort Count:', len(jobs))"

# Test Instahyre Stealth Scraper
py -3.11 -c "import asyncio; from fetchers.indian.instahyre import fetch_instahyre_jobs; jobs = asyncio.run(fetch_instahyre_jobs('Software Engineering', 'Bangalore', 'fresher')); print('Instahyre Count:', len(jobs))"
```

### 3. Test Layer 3: ATS Endpoints
```bash
# Test Workday Direct CXS API
py -3.11 -c "import asyncio; from fetchers.ats.workday import fetch_workday_jobs; jobs = asyncio.run(fetch_workday_jobs('Engineer', 'Bangalore')); print('Workday Count:', len(jobs))"

# Test Greenhouse Board API
py -3.11 -c "import asyncio; from fetchers.ats.greenhouse import fetch_greenhouse_jobs; jobs = asyncio.run(fetch_greenhouse_jobs('Engineer', 'Bangalore')); print('Greenhouse Count:', len(jobs))"
```

### 4. Test Layer 4: Enhanced Boards
```bash
# Test LinkedIn Guest API & Comprehensive Aggregator
py -3.11 -c "import asyncio; from fetchers.boards.enhanced.linkedin_enhanced import fetch_linkedin_comprehensive; jobs = asyncio.run(fetch_linkedin_comprehensive('React Developer', 'Bangalore', 'fresher')); print('LinkedIn Count:', len(jobs))"

# Test Indeed Boolean Query
py -3.11 -c "import asyncio; from fetchers.boards.enhanced.indeed_enhanced import fetch_indeed_comprehensive; jobs = asyncio.run(fetch_indeed_comprehensive('React Developer', 'Bangalore', 'fresher')); print('Indeed Count:', len(jobs))"

# Test JobSpy 4th Scraper
py -3.11 -c "import asyncio; from fetchers.boards.enhanced.jobspy_wrapper import fetch_jobspy_jobs; jobs = asyncio.run(fetch_jobspy_jobs('React Developer', 'Bangalore', 'fresher', results_wanted=5)); print('JobSpy Count:', len(jobs))"
```

---

## 🐞 Debugging & Maintenance Guide

### 1. Clearing Cache
Cache records are persisted in SQLite at `backend/hirepulse_cache.db`.

To clear a specific query or flush expired items:
```bash
# Clear specific key
py -3.11 -c "from core.cache.job_cache import clear; clear('frontend_developer_bangalore_fresher'); print('Cache cleared')"

# Clear all expired entries
py -3.11 -c "from core.cache.job_cache import clear_expired; clear_expired(); print('Expired cache purged')"

# Or simply delete the SQLite database file:
rm backend/hirepulse_cache.db
```

### 2. Updating Hacker News "Who is Hiring?" Thread ID
Hacker News publishes a new thread on the **1st of every month**.
- File: [`backend/fetchers/json_apis/hackernews.py`](file:///c:/Users/mohan/Downloads/Hire%20Pulse/backend/fetchers/json_apis/hackernews.py)
- Line:
  ```python
  DEFAULT_HN_THREAD_ID = 41234567  # Update to the latest monthly ID
  ```
- *Automatic Fallback*: If the default thread has 0 comments, the fetcher automatically queries the Algolia HN API for the latest active thread.

### 3. Windows Terminal Unicode Encoding (`charmap` error)
If running a script in PowerShell causes `UnicodeEncodeError: 'charmap' codec can't encode character '\u20b9'` (the Indian Rupee symbol `₹`), add this to the top of your script:
```python
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
```

---

## 📊 Expected Output & Response Schema

### Conservative Yield Per Run:
| Layer | Scrapers | Expected Yield |
|---|---|---|
| **Layer 1: JSON APIs** | RemoteOK, Hacker News | 5 – 25 jobs |
| **Layer 2: Indian Portals** | Internshala, Cutshort, Instahyre | 40 – 120 jobs |
| **Layer 3: ATS Endpoints** | Lever (41), Greenhouse (45), Ashby (24), Workday (22) | 200 – 800+ jobs |
| **Layer 4: Enhanced Boards** | LinkedIn, Indeed, Naukri, JobSpy | 50 – 150+ jobs |
| **Total Deduplicated** | Unified Candidate Pool | **300 – 1,000+ jobs** |
| **Filtered & Ranked** | Strictly matching Role, Location & Experience | **30 – 100+ qualified jobs** |

### Standard Job Object Format:
```json
{
  "id": "job_3847291847",
  "title": "Junior Frontend Developer",
  "company": "Naxos Design Studio",
  "location": "Bangalore, India",
  "description": "Looking for React developer with JavaScript and CSS knowledge...",
  "apply_link": "https://internshala.com/job/detail/fresher-junior-software-developer...",
  "url": "https://internshala.com/job/detail/fresher-junior-software-developer...",
  "posted_date": "Recently",
  "source": "internshala",
  "match_score": 87,
  "experience_score": 90,
  "role_score": 95,
  "skill_score": 82
}
```

---

## 🔧 Troubleshooting & Selector Updates

### 1. `ERR_NAME_NOT_RESOLVED` on `in.indeed.com`
Some DNS providers fail to resolve regional Indeed subdomains.
- **Fix Built-in**: `indeed_enhanced.py` automatically falls back to `https://www.indeed.com` if `in.indeed.com` fails.

### 2. LinkedIn Guest API Rate Limiting (HTTP 429)
- The Guest API has a built-in `1.5s` delay between requests (`await asyncio.sleep(1.5)`).
- If your IP gets rate-limited, `fetch_linkedin_comprehensive` immediately falls back to **JobSpy** and **Scrapling**.

### 3. Website Selector Updates
If target portals modify their DOM:
- **Internshala** (`backend/fetchers/indian/internshala.py`):
  - Card container: `.individual_internship`
  - Title: `.job-title-href` or `.job-internship-name`
  - Company: `.company-name`
  - Location: `.locations` or `.location_link`
  - CTC: `.desktop` or `.salary`
- **Instahyre** (`backend/fetchers/indian/instahyre.py`):
  - Card container: `.job-card, .job-item, .employer-block`
  - Title: `.job-title, .designation`
  - Company: `.company-name, .employer-name`
  - Location: `.location, .city`
- **Indeed** (`backend/fetchers/boards/enhanced/indeed_enhanced.py`):
  - Card container: `div.job_seen_beacon`
  - Title: `h2.jobTitle a`
  - Company: `span.companyName`
  - Location: `div.companyLocation`
  - Apply link: `a[data-jk]`

