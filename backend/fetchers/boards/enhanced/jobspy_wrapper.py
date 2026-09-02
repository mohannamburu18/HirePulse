import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import pandas as pd
from jobspy import scrape_jobs

logger = logging.getLogger(__name__)

def map_experience_level(exp_level: Optional[str]) -> str:
    """
    Map exp_level string to JobSpy experience level parameter.
    Requirements:
    - fresher/0-1/0-2 -> "entry"
    - 2-5 -> "mid"
    - 5+ -> "senior"
    """
    clean_exp = (exp_level or "fresher").strip().lower()
    if clean_exp in ["fresher", "0", "0-1", "0-2", "entry", "entry_level", "junior", "intern"]:
        return "entry"
    elif clean_exp in ["2-5", "2-4", "3-5", "mid", "mid_level", "intermediate"]:
        return "mid"
    elif clean_exp in ["5+", "5-10", "senior", "lead", "sr"]:
        return "senior"
    return "entry"

def _scrape_jobspy_sync(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher",
    results_wanted: int = 200
) -> List[Dict[str, Any]]:
    """
    Synchronous execution of JobSpy multi-board scraper.
    """
    mapped_exp = map_experience_level(exp_level)
    site_names = ["linkedin", "indeed", "google", "zip_recruiter", "glassdoor"]

    logger.info(
        f"JobSpy: Initiating scraper for role='{role}', location='{location}', "
        f"exp_level='{exp_level}' (mapped='{mapped_exp}'), results_wanted={results_wanted}..."
    )

    try:
        # Query JobSpy across specified parameters
        df: pd.DataFrame = scrape_jobs(
            site_name=site_names,
            search_term=role or "Software Engineer",
            location=location or "Bangalore",
            results_wanted=results_wanted,
            hours_old=168,  # 7 days
            country_indeed="India",
            experience_level=mapped_exp,
            linkedin_fetch_description=True
        )

        if df is None or df.empty:
            logger.info("JobSpy returned an empty DataFrame.")
            return []

        logger.info(f"JobSpy: Retrieved DataFrame with {len(df)} rows across sites: {site_names}")

        job_records: List[Dict[str, Any]] = []
        seen_links = set()

        # Convert DataFrame rows into standardized job dicts
        for _, row in df.iterrows():
            row_dict = row.to_dict()

            title = str(row_dict.get("title") or "").strip()
            if not title:
                continue

            company = str(row_dict.get("company") or "Technology Enterprise").strip()
            job_loc = str(row_dict.get("location") or location or "India").strip()
            desc = str(row_dict.get("description") or "").strip()
            site = str(row_dict.get("site") or "JobSpy").capitalize()

            # Prioritize direct application URL over aggregator landing page
            apply_url = str(row_dict.get("job_url_direct") or row_dict.get("job_url") or "").strip()
            if not apply_url:
                continue

            if apply_url in seen_links:
                continue
            seen_links.add(apply_url)

            # Format posted date
            raw_date = row_dict.get("date_posted")
            posted_date_str = str(raw_date).split("T")[0] if raw_date and pd.notna(raw_date) else "Recently"

            # Experience info
            job_level = row_dict.get("job_level") or row_dict.get("experience_range")
            job_exp = str(job_level) if job_level and pd.notna(job_level) else f"{mapped_exp.capitalize()} Level"

            job_records.append({
                "title": title,
                "company": company,
                "location": job_loc,
                "experience": job_exp,
                "description": desc,
                "url": apply_url,
                "posted_date": posted_date_str,
                "source": f"JobSpy-{site}",
                "site": site,
                "is_remote": bool(row_dict.get("is_remote")),
                "raw": {
                    "id": row_dict.get("id"),
                    "site": site,
                    "job_url": apply_url,
                    "skills": row_dict.get("skills")
                }
            })

        logger.info(f"JobSpy: Successfully converted and normalized {len(job_records)} job records.")
        return job_records

    except Exception as e:
        logger.error(f"Error during JobSpy execution: {e}", exc_info=True)
        return []

async def fetch_jobspy_jobs(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher",
    results_wanted: int = 200
) -> List[Dict[str, Any]]:
    """
    Async wrapper executing JobSpy in ThreadPoolExecutor to prevent event-loop blocking.
    """
    loop = asyncio.get_running_loop()
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(
                executor,
                _scrape_jobspy_sync,
                role,
                location,
                exp_level,
                results_wanted
            )
    except Exception as e:
        logger.error(f"Error executing fetch_jobspy_jobs executor: {e}")
        return []

