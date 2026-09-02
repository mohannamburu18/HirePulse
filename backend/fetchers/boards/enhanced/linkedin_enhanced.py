import asyncio
import aiohttp
import logging
import re
import urllib.parse
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

from core.filters.experience_detector import get_experience_params
from fetchers.boards.enhanced.jobspy_wrapper import fetch_jobspy_jobs

logger = logging.getLogger(__name__)

LINKEDIN_GUEST_API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

async def fetch_linkedin_guest_api(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher",
    pages: int = 3
) -> List[Dict[str, Any]]:
    """
    Fetch LinkedIn job listings directly from LinkedIn's public guest API.
    
    Requirements:
    - Use aiohttp with browser headers
    - URL: https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search
    - Parameters: keywords=role, location=location, f_E=exp_params, f_TPR=r604800, start=page*25
    - Parse with BeautifulSoup
    - Extract job cards from li elements
    - Extract: title (base-search-card__title), company (base-search-card__subtitle),
      location (job-search-card__location), URL (base-card__full-link), date (job-search-card__listdate)
    - Fetch 3 pages with 1.5s delay
    """
    exp_params = get_experience_params(exp_level).get("linkedin_f_e", "1,2")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.linkedin.com/jobs/search",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    all_jobs: List[Dict[str, Any]] = []
    seen_links = set()

    logger.info(
        f"LinkedIn Guest API: Querying role='{role}', location='{location}', "
        f"f_E='{exp_params}' across {pages} pages..."
    )

    try:
        timeout = aiohttp.ClientTimeout(total=20)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for page in range(pages):
                start_offset = page * 25
                params = {
                    "keywords": role or "Frontend Developer",
                    "location": location or "Bangalore",
                    "f_TPR": "r604800",
                    "start": str(start_offset)
                }
                if exp_params:
                    params["f_E"] = exp_params

                logger.info(f"LinkedIn Guest API: Fetching page {page + 1}/{pages} (start={start_offset})...")

                try:
                    async with session.get(LINKEDIN_GUEST_API_URL, params=params) as resp:
                        if resp.status != 200:
                            logger.warning(f"LinkedIn Guest API page {page + 1} returned status {resp.status}")
                            break

                        html_text = await resp.text()
                        if not html_text.strip():
                            logger.info(f"LinkedIn Guest API page {page + 1}: Empty response body.")
                            break

                        soup = BeautifulSoup(html_text, "html.parser")
                        cards = soup.find_all("li")
                        if not cards:
                            logger.info(f"LinkedIn Guest API page {page + 1}: No <li> job cards found.")
                            break

                        page_count = 0
                        for card in cards:
                            # 1. Title (base-search-card__title)
                            title_elem = card.find(class_=re.compile(r"base-search-card__title|job-title"))
                            if not title_elem:
                                continue
                            title = title_elem.get_text(strip=True)

                            # 2. Company (base-search-card__subtitle)
                            comp_elem = card.find(class_=re.compile(r"base-search-card__subtitle"))
                            company = comp_elem.get_text(strip=True) if comp_elem else "Technology Enterprise"

                            # 3. Location (job-search-card__location)
                            loc_elem = card.find(class_=re.compile(r"job-search-card__location"))
                            job_loc = loc_elem.get_text(strip=True) if loc_elem else location

                            # 4. URL (base-card__full-link)
                            link_elem = card.find("a", class_=re.compile(r"base-card__full-link|job-link")) or card.find("a", href=True)
                            raw_href = link_elem.get("href", "") if link_elem else ""

                            # Extract clean /jobs/view/{id} apply link
                            job_id_match = re.search(r"view/(\d+)", raw_href) or re.search(r"jobPosting:(\d+)", str(card))
                            if job_id_match:
                                apply_url = f"https://www.linkedin.com/jobs/view/{job_id_match.group(1)}"
                            elif raw_href.startswith("http"):
                                apply_url = raw_href.split("?")[0]
                            else:
                                continue

                            if apply_url in seen_links:
                                continue
                            seen_links.add(apply_url)

                            # 5. Date (job-search-card__listdate or time)
                            date_elem = card.find(class_=re.compile(r"job-search-card__listdate")) or card.find("time")
                            date_str = date_elem.get_text(strip=True) if date_elem else "Recently"

                            all_jobs.append({
                                "title": title,
                                "company": company,
                                "location": job_loc,
                                "url": apply_url,
                                "posted_date": date_str,
                                "source": "LinkedIn-GuestAPI",
                                "raw": {
                                    "title": title,
                                    "company": company,
                                    "location": job_loc,
                                    "url": apply_url,
                                    "page": page + 1
                                }
                            })
                            page_count += 1

                        logger.info(f"LinkedIn Guest API page {page + 1}: Extracted {page_count} jobs (Total: {len(all_jobs)})")

                except Exception as page_ex:
                    logger.error(f"LinkedIn Guest API error on page {page + 1}: {page_ex}")
                    break

                # 1.5s delay between pages as required
                if page < pages - 1:
                    await asyncio.sleep(1.5)

    except Exception as e:
        logger.error(f"Error executing fetch_linkedin_guest_api: {e}", exc_info=True)

    logger.info(f"LinkedIn Guest API complete. Total jobs collected: {len(all_jobs)}")
    return all_jobs

async def fetch_linkedin_comprehensive(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher"
) -> List[Dict[str, Any]]:
    """
    Comprehensive multi-method LinkedIn aggregator:
    1. Try Guest API first
    2. Fallback to JobSpy (filtered for LinkedIn source)
    3. Fallback to existing Scrapling fetcher
    4. Deduplicate by URL & title+company
    5. Return unique jobs
    """
    logger.info(f"Starting comprehensive LinkedIn search for role='{role}', location='{location}', exp='{exp_level}'...")
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
            # Standardize URL key
            if "url" not in j and "apply_link" in j:
                j["url"] = j["apply_link"]
            unique_jobs.append(j)

    # 1. Method 1: Guest API
    try:
        guest_jobs = await fetch_linkedin_guest_api(role, location, exp_level, pages=3)
        logger.info(f"Method 1 (Guest API) retrieved {len(guest_jobs)} jobs")
        for job in guest_jobs:
            add_job(job)
    except Exception as e:
        logger.warning(f"Method 1 (Guest API) failed: {e}")

    # 2. Method 2: Fallback / Augmentation via JobSpy (LinkedIn only)
    if len(unique_jobs) < 30:
        logger.info("Method 1 yield under target threshold. Invoking Method 2 (JobSpy LinkedIn)...")
        try:
            jobspy_all = await fetch_jobspy_jobs(role, location, exp_level, results_wanted=50)
            jobspy_li = [j for j in jobspy_all if "linkedin" in str(j.get("source", "")).lower() or "linkedin" in str(j.get("site", "")).lower()]
            logger.info(f"Method 2 (JobSpy) retrieved {len(jobspy_li)} LinkedIn jobs")
            for job in jobspy_li:
                add_job(job)
        except Exception as e:
            logger.warning(f"Method 2 (JobSpy) failed: {e}")

    # 3. Method 3: Fallback / Augmentation via existing Scrapling fetcher
    if len(unique_jobs) < 20:
        logger.info("Total LinkedIn yield still below threshold. Invoking Method 3 (Scrapling fetcher)...")
        try:
            from fetchers.boards.linkedin_scrapling import fetch_linkedin_scrapling
            scrapling_jobs = await fetch_linkedin_scrapling(role, location, exp_level)
            logger.info(f"Method 3 (Scrapling) retrieved {len(scrapling_jobs)} jobs")
            for job in scrapling_jobs:
                job_dict = job.model_dump() if hasattr(job, "model_dump") else dict(job)
                add_job(job_dict)
        except Exception as e:
            logger.warning(f"Method 3 (Scrapling) failed: {e}")

    logger.info(f"Comprehensive LinkedIn search completed. Total deduplicated jobs: {len(unique_jobs)}")
    return unique_jobs

