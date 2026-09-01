import httpx
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
from ..base import JobListing, is_role_match, is_location_match

logger = logging.getLogger(__name__)

WORKDAY_ENDPOINTS = [
    {
        "company": "Salesforce",
        "url": "https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/jobs",
        "base_link": "https://salesforce.wd12.myworkdayjobs.com/en-US/External_Career_Site"
    },
    {
        "company": "Adobe",
        "url": "https://adobe.wd5.myworkdayjobs.com/wday/cxs/adobe/external_experienced/jobs",
        "base_link": "https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced"
    },
    {
        "company": "Nvidia",
        "url": "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs",
        "base_link": "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite"
    },
    {
        "company": "Target",
        "url": "https://target.wd5.myworkdayjobs.com/wday/cxs/target/targetcareers/jobs",
        "base_link": "https://target.wd5.myworkdayjobs.com/en-US/targetcareers"
    }
]

async def fetch_workday_single(
    client: httpx.AsyncClient,
    cfg: Dict[str, str],
    role: str = "",
    location: str = "",
    exp: str = "",
    is_remote: bool = False
) -> List[JobListing]:
    """Fetch live postings from Workday CXS API."""
    company = cfg["company"]
    url = cfg["url"]
    base_link = cfg["base_link"]
    results: List[JobListing] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }

    payload = {
        "limit": 20,
        "offset": 0,
        "searchText": role if role else ""
    }

    try:
        res = await client.post(url, json=payload, headers=headers, timeout=12.0)
        if res.status_code != 200:
            return []

        data = res.json()
        postings = data.get("jobPostings", [])
        if not isinstance(postings, list):
            return []

        for p in postings:
            title = p.get("title", "")
            job_loc = p.get("locationsText", "") or "Remote"
            is_job_remote = "remote" in job_loc.lower() or "remote" in title.lower()

            if role and not is_role_match(title, role):
                continue
            if location and not is_location_match(job_loc, location, is_remote):
                continue

            external_path = p.get("externalPath", "")
            apply_url = f"{base_link}{external_path}" if external_path.startswith("/") else f"{base_link}/{external_path}"
            
            posted_on = p.get("postedOn", "Recently")
            bullet_fields = p.get("bulletFields", [])

            results.append(
                JobListing(
                    id=f"workday_{company.lower()}_{abs(hash(title + external_path))}",
                    title=title,
                    company=company,
                    location=job_loc,
                    experience=exp if exp else "Entry / Mid",
                    apply_link=apply_url,
                    posted_date=posted_on,
                    source="Workday",
                    is_remote=is_job_remote,
                    tags=bullet_fields[:2],
                    fetched_at=now_iso,
                    posted_datetime=posted_on
                )
            )
    except Exception as e:
        logger.debug(f"Workday fetch skipped for {company}: {e}")
        return []

    return results

async def fetch_workday_jobs(
    role: str = "",
    location: str = "",
    exp: str = "",
    is_remote: bool = False
) -> List[JobListing]:
    """Fetch Workday jobs across tracked enterprises in parallel."""
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=40)
    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        tasks = [
            fetch_workday_single(client, cfg, role, location, exp, is_remote)
            for cfg in WORKDAY_ENDPOINTS
        ]
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[JobListing] = []
    for r in results_lists:
        if isinstance(r, list):
            all_jobs.extend(r)

    return all_jobs
