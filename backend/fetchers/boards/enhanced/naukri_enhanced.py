import asyncio
import aiohttp
import logging
import urllib.parse
from typing import List, Dict, Any, Optional

from core.filters.experience_detector import get_experience_params
from fetchers.boards.enhanced.jobspy_wrapper import fetch_jobspy_jobs
from fetchers.boards.naukri_scrapling import fetch_naukri_scrapling

logger = logging.getLogger(__name__)

NAUKRI_API_URL = "https://www.naukri.com/jobapi/v3/search"
NAUKRI_BASE_URL = "https://www.naukri.com"

async def fetch_naukri_json_api(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher",
    max_pages: int = 3
) -> List[Dict[str, Any]]:
    """
    Fetch job openings from Naukri's jobapi/v3/search endpoint.
    
    Requirements:
    - Use aiohttp with proper headers (User-Agent, Referer, Accept, Origin, appid)
    - URL: https://www.naukri.com/jobapi/v3/search
    - Parameters: noOfResults=100, k=role, l=location, experience=exp_value, jobAge=7, pageNo=page
    - Experience mapping from get_experience_params()
    - Fetch up to 3 pages or until no results
    - Parse jobDetails array
    - Extract: title, companyName, location, jobDescription, jobUrl, postedDate
    - Add 0.5s delay
    - Return jobs with source: "naukri_api"
    """
    exp_params = get_experience_params(exp_level)
    exp_value = exp_params.get("naukri_exp", 0)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Referer": "https://www.naukri.com/",
        "Origin": "https://www.naukri.com",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "appid": "109",
        "systemid": "Naukri",
        "clientid": "d3skt0p"
    }

    all_jobs: List[Dict[str, Any]] = []
    seen_urls = set()

    logger.info(
        f"Naukri JSON API: Querying role='{role}', location='{location}', "
        f"exp={exp_value} across up to {max_pages} pages..."
    )

    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            for page in range(1, max_pages + 1):
                params = {
                    "noOfResults": 100,
                    "k": role or "Frontend Developer",
                    "l": location or "Bangalore",
                    "experience": exp_value,
                    "jobAge": 7,
                    "pageNo": page,
                    "urlType": "search_by_keyword",
                    "searchType": "adv"
                }

                logger.info(f"Naukri JSON API: Fetching page {page}/{max_pages}...")

                try:
                    async with session.get(NAUKRI_API_URL, params=params) as resp:
                        if resp.status != 200:
                            logger.warning(f"Naukri JSON API page {page} returned status {resp.status}")
                            break

                        data = await resp.json(content_type=None)
                        if not isinstance(data, dict):
                            logger.info(f"Naukri JSON API page {page}: Non-dict payload received.")
                            break

                        job_details = data.get("jobDetails") or []
                        if not job_details:
                            logger.info(f"Naukri JSON API page {page}: No jobDetails returned. Ending pagination.")
                            break

                        page_count = 0
                        for item in job_details:
                            if not isinstance(item, dict):
                                continue

                            title = item.get("title") or item.get("jobTitle") or role
                            company = item.get("companyName") or item.get("company") or "Technology Enterprise"
                            desc = item.get("jobDescription") or item.get("description") or ""
                            date_posted = item.get("postedDate") or item.get("createdDate") or "Recently"

                            # Extract location
                            job_loc = location
                            placeholders = item.get("placeholders") or []
                            for ph in placeholders:
                                if isinstance(ph, dict) and ph.get("type") == "location":
                                    job_loc = ph.get("label", location)
                                    break
                            if job_loc == location and item.get("location"):
                                job_loc = item.get("location")

                            # Extract jobUrl
                            raw_url = item.get("jdURL") or item.get("staticUrl") or ""
                            if raw_url.startswith("/"):
                                apply_url = urllib.parse.urljoin(NAUKRI_BASE_URL, raw_url)
                            elif raw_url.startswith("http"):
                                apply_url = raw_url
                            else:
                                apply_url = f"{NAUKRI_BASE_URL}/job-listings-{item.get('jobId', 'view')}"

                            if apply_url in seen_urls:
                                continue
                            seen_urls.add(apply_url)

                            all_jobs.append({
                                "title": title,
                                "companyName": company,
                                "company": company,
                                "location": job_loc,
                                "jobDescription": desc,
                                "description": desc,
                                "jobUrl": apply_url,
                                "url": apply_url,
                                "postedDate": str(date_posted),
                                "posted_date": str(date_posted),
                                "source": "naukri_api",
                                "raw": item
                            })
                            page_count += 1

                        logger.info(f"Naukri JSON API page {page}: Extracted {page_count} jobs (Total: {len(all_jobs)})")

                except Exception as page_ex:
                    logger.warning(f"Naukri JSON API request error on page {page}: {page_ex}")
                    break

                # 0.5s delay between pages as required
                if page < max_pages:
                    await asyncio.sleep(0.5)

    except Exception as e:
        logger.error(f"Error executing fetch_naukri_json_api: {e}", exc_info=True)

    logger.info(f"Naukri JSON API finished. Total jobs retrieved: {len(all_jobs)}")
    return all_jobs

async def fetch_naukri_comprehensive(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher"
) -> List[Dict[str, Any]]:
    """
    Comprehensive multi-method Naukri aggregator:
    1. Try JSON API first
    2. Fallback to existing Scrapling fetcher
    3. Fallback to JobSpy (filter for naukri source)
    4. Deduplicate by URL & signature
    5. Return unique jobs
    """
    logger.info(f"Starting comprehensive Naukri search for role='{role}', location='{location}', exp='{exp_level}'...")
    unique_jobs: List[Dict[str, Any]] = []
    seen_urls = set()
    seen_sigs = set()

    def add_job(j: Dict[str, Any]) -> None:
        url = j.get("jobUrl") or j.get("url") or j.get("apply_link") or ""
        title = (j.get("title") or "").strip().lower()
        company = (j.get("companyName") or j.get("company") or "").strip().lower()
        sig = f"{title}_{company}"

        if url and url not in seen_urls and sig not in seen_sigs:
            seen_urls.add(url)
            seen_sigs.add(sig)
            # Ensure standard url/apply_link fields
            if "url" not in j and url:
                j["url"] = url
            if "company" not in j and "companyName" in j:
                j["company"] = j["companyName"]
            unique_jobs.append(j)

    # 1. Method 1: JSON API
    try:
        api_jobs = await fetch_naukri_json_api(role, location, exp_level, max_pages=3)
        logger.info(f"Method 1 (Naukri JSON API) retrieved {len(api_jobs)} jobs")
        for job in api_jobs:
            add_job(job)
    except Exception as e:
        logger.warning(f"Method 1 (Naukri JSON API) failed: {e}")

    # 2. Method 2: Fallback to existing Scrapling fetcher
    if len(unique_jobs) < 20:
        logger.info("Method 1 yield below target threshold. Invoking Method 2 (Naukri Scrapling fetcher)...")
        try:
            scrapling_jobs = await fetch_naukri_scrapling(role, location, exp_level)
            logger.info(f"Method 2 (Scrapling) retrieved {len(scrapling_jobs)} jobs")
            for job in scrapling_jobs:
                job_dict = job.model_dump() if hasattr(job, "model_dump") else dict(job)
                add_job(job_dict)
        except Exception as e:
            logger.warning(f"Method 2 (Naukri Scrapling) failed: {e}")

    # 3. Method 3: Fallback / Augment via JobSpy (Naukri only)
    if len(unique_jobs) < 15:
        logger.info("Total Naukri yield still below target threshold. Invoking Method 3 (JobSpy Naukri)...")
        try:
            jobspy_all = await fetch_jobspy_jobs(role, location, exp_level, results_wanted=30)
            jobspy_nk = [j for j in jobspy_all if "naukri" in str(j.get("source", "")).lower() or "naukri" in str(j.get("site", "")).lower()]
            logger.info(f"Method 3 (JobSpy Naukri) retrieved {len(jobspy_nk)} jobs")
            for job in jobspy_nk:
                add_job(job)
        except Exception as e:
            logger.warning(f"Method 3 (JobSpy Naukri) failed: {e}")

    logger.info(f"Comprehensive Naukri search completed. Total unique jobs: {len(unique_jobs)}")
    return unique_jobs

