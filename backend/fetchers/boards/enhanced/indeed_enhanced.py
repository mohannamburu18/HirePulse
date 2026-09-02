import asyncio
import logging
import re
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from core.filters.experience_detector import get_experience_params
from fetchers.boards.enhanced.jobspy_wrapper import fetch_jobspy_jobs

logger = logging.getLogger(__name__)

INDEED_IN_BASE_URL = "https://in.indeed.com"

def _scrape_indeed_page_sync(url: str) -> str:
    """Synchronous fetch of Indeed HTML with Scrapling anti-bot bypass and domain fallback."""
    urls_to_try = [url]
    if "in.indeed.com" in url:
        urls_to_try.append(url.replace("in.indeed.com", "www.indeed.com"))

    for target_url in urls_to_try:
        try:
            from scrapling.fetchers import Fetcher
            fetcher = Fetcher()
            resp = fetcher.get(target_url)
            if resp.status == 200 and resp.text:
                return resp.text
        except Exception as ex:
            logger.debug(f"Fetcher note for {target_url}: {ex}. Trying StealthyFetcher...")
            try:
                from scrapling.fetchers import StealthyFetcher
                s_fetcher = StealthyFetcher(headless=True)
                s_resp = s_fetcher.fetch(target_url)
                if hasattr(s_resp, "body") and s_resp.body:
                    return s_resp.body.decode("utf-8", errors="ignore") if isinstance(s_resp.body, bytes) else str(s_resp.body)
                elif hasattr(s_resp, "text") and s_resp.text:
                    return s_resp.text
            except Exception as s_ex:
                logger.warning(f"StealthyFetcher failed for {target_url}: {s_ex}")

    return ""

async def fetch_indeed_boolean_query(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher",
    pages: int = 3
) -> List[Dict[str, Any]]:
    """
    Fetch Indeed jobs using targeted Boolean experience queries across 3 pages.
    
    Requirements:
    - Use Boolean queries from get_experience_params()
    - Build query: role + " " + boolean_query
    - Use Scrapling StealthyFetcher
    - URL: https://in.indeed.com/jobs?q={query}&l={location}&fromage=7
    - Fetch 3 pages with start=page*10
    - Parse with BeautifulSoup
    - Find job cards: div.job_seen_beacon
    - Extract: title (h2.jobTitle a), company (span.companyName), location (div.companyLocation),
      description (div.job-snippet), URL (a[data-jk])
    - Add 0.5s delay
    """
    exp_params = get_experience_params(exp_level)
    boolean_term = exp_params.get("indeed_boolean") or "entry_level"
    clean_bool = boolean_term.replace("_", " ")
    combined_query = f"{role} \"{clean_bool}\"" if boolean_term else role

    encoded_q = urllib.parse.quote_plus(combined_query)
    encoded_loc = urllib.parse.quote_plus(location or "Bangalore")

    logger.info(
        f"Indeed Boolean Query: role='{role}', boolean='{clean_bool}', "
        f"location='{location}', fetching {pages} pages..."
    )

    all_jobs: List[Dict[str, Any]] = []
    seen_urls = set()
    loop = asyncio.get_running_loop()

    for page in range(pages):
        start_offset = page * 10
        url = f"{INDEED_IN_BASE_URL}/jobs?q={encoded_q}&l={encoded_loc}&fromage=7&start={start_offset}"
        logger.info(f"Indeed: Fetching page {page + 1}/{pages} (start={start_offset})...")

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                html_text = await loop.run_in_executor(executor, _scrape_indeed_page_sync, url)

            if not html_text:
                logger.info(f"Indeed page {page + 1}: Empty HTML received.")
                break

            soup = BeautifulSoup(html_text, "html.parser")
            cards = soup.select("div.job_seen_beacon, div.cardOutline, div.jobsearch-SerpJobCard")

            if not cards:
                logger.info(f"Indeed page {page + 1}: No job cards found.")
                break

            page_count = 0
            for card in cards:
                # 1. Title (h2.jobTitle a or h2.jobTitle)
                title_elem = card.select_one("h2.jobTitle a, h2.jobTitle, a.jcs-JobTitle")
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)

                # 2. Company (span.companyName or span[data-testid='company-name'])
                comp_elem = card.select_one("span.companyName, span[data-testid='company-name'], .company_location span")
                company = comp_elem.get_text(strip=True) if comp_elem else "Hiring Company"

                # 3. Location (div.companyLocation or div[data-testid='text-location'])
                loc_elem = card.select_one("div.companyLocation, div[data-testid='text-location'], .locations")
                job_loc = loc_elem.get_text(strip=True) if loc_elem else location

                # 4. Description (div.job-snippet or table)
                desc_elem = card.select_one("div.job-snippet, .job-snippet ul, div.underShelfFooter")
                desc = desc_elem.get_text(strip=True) if desc_elem else ""

                # 5. URL (a[data-jk] or href)
                jk_elem = card.select_one("a[data-jk]") or card.find("a", href=re.compile(r"jk=|[a-f0-9]{16}"))
                raw_jk = jk_elem.get("data-jk", "") if jk_elem else ""
                raw_href = jk_elem.get("href", "") if jk_elem else ""

                if raw_jk:
                    apply_url = f"{INDEED_IN_BASE_URL}/viewjob?jk={raw_jk}"
                elif "/rc/clk" in raw_href or "/viewjob" in raw_href:
                    apply_url = urllib.parse.urljoin(INDEED_IN_BASE_URL, raw_href)
                elif raw_href.startswith("http"):
                    apply_url = raw_href
                else:
                    # Search fallback
                    apply_url = url

                if apply_url in seen_urls:
                    continue
                seen_urls.add(apply_url)

                all_jobs.append({
                    "title": title,
                    "company": company,
                    "location": job_loc,
                    "description": desc,
                    "url": apply_url,
                    "posted_date": "Recently",
                    "source": "Indeed-Boolean",
                    "raw": {
                        "title": title,
                        "company": company,
                        "location": job_loc,
                        "page": page + 1,
                        "boolean_term": clean_bool
                    }
                })
                page_count += 1

            logger.info(f"Indeed page {page + 1}: Extracted {page_count} jobs (Total: {len(all_jobs)})")

            # 0.5s delay between requests as required
            if page < pages - 1:
                await asyncio.sleep(0.5)

        except Exception as page_ex:
            logger.error(f"Indeed page {page + 1} processing error: {page_ex}")
            break

    logger.info(f"Indeed Boolean Query complete. Total jobs: {len(all_jobs)}")
    return all_jobs

async def fetch_indeed_comprehensive(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher"
) -> List[Dict[str, Any]]:
    """
    Comprehensive multi-method Indeed aggregator:
    1. Try Boolean query first
    2. Fallback / augment with JobSpy (filter for indeed source)
    3. Fallback / augment with existing Scrapling fetcher
    4. Deduplicate by URL & signature
    5. Return unique jobs
    """
    logger.info(f"Starting comprehensive Indeed search for role='{role}', location='{location}', exp='{exp_level}'...")
    unique_jobs: List[Dict[str, Any]] = []
    seen_urls = set()
    seen_sigs = set()

    def add_job(j: Dict[str, Any]) -> None:
        url = j.get("url") or j.get("apply_link") or ""
        title = (j.get("title") or "").strip().lower()
        company = (j.get("company") or "").strip().lower()
        sig = f"{title}_{company}"

        if url and url not in seen_urls and sig not in seen_sigs:
            seen_urls.add(url)
            seen_sigs.add(sig)
            if "url" not in j and "apply_link" in j:
                j["url"] = j["apply_link"]
            unique_jobs.append(j)

    # 1. Method 1: Boolean Query
    try:
        bool_jobs = await fetch_indeed_boolean_query(role, location, exp_level, pages=3)
        logger.info(f"Method 1 (Boolean Query) retrieved {len(bool_jobs)} jobs")
        for job in bool_jobs:
            add_job(job)
    except Exception as e:
        logger.warning(f"Method 1 (Boolean Query) failed: {e}")

    # 2. Method 2: Fallback / Augment via JobSpy (Indeed only)
    if len(unique_jobs) < 20:
        logger.info("Method 1 yield below target threshold. Invoking Method 2 (JobSpy Indeed)...")
        try:
            jobspy_all = await fetch_jobspy_jobs(role, location, exp_level, results_wanted=40)
            jobspy_ind = [j for j in jobspy_all if "indeed" in str(j.get("source", "")).lower() or "indeed" in str(j.get("site", "")).lower()]
            logger.info(f"Method 2 (JobSpy) retrieved {len(jobspy_ind)} Indeed jobs")
            for job in jobspy_ind:
                add_job(job)
        except Exception as e:
            logger.warning(f"Method 2 (JobSpy Indeed) failed: {e}")

    # 3. Method 3: Fallback / Augment via existing Scrapling fetcher
    if len(unique_jobs) < 15:
        logger.info("Total Indeed yield still below target. Invoking Method 3 (Scrapling fetcher)...")
        try:
            from fetchers.boards.indeed_scrapling import fetch_indeed_scrapling
            scrapling_jobs = await fetch_indeed_scrapling(role, location)
            logger.info(f"Method 3 (Scrapling) retrieved {len(scrapling_jobs)} jobs")
            for job in scrapling_jobs:
                job_dict = job.model_dump() if hasattr(job, "model_dump") else dict(job)
                add_job(job_dict)
        except Exception as e:
            logger.warning(f"Method 3 (Scrapling) failed: {e}")

    logger.info(f"Comprehensive Indeed search completed. Total unique jobs: {len(unique_jobs)}")
    return unique_jobs
