import httpx
import asyncio
from typing import List, Optional
from datetime import datetime, timezone
import logging
from ..base import JobListing, is_role_match, is_location_match

logger = logging.getLogger(__name__)

GREENHOUSE_COMPANIES = [
    "datadog", "figma", "notion", "airbnb", "coinbase", "stripe", "robinhood",
    "doordash", "asana", "lyft", "reddit", "databricks", "openai", "dropbox",
    "atlassian", "okta", "zscaler", "toast", "gitlab", "elastic", "mongodb",
    "checkr", "duolingo", "gusto", "samsara", "airtable", "brex", "carta",
    "plaid", "pinterest", "snap", "benchling", "lucid", "pagerduty", "quizlet",
    "snowflake", "squarespace", "unity", "zendesk"
]

async def fetch_company_greenhouse_jobs(
    client: httpx.AsyncClient,
    company: str,
    role: str = "",
    location: str = "",
    exp: str = "",
    is_remote: bool = False
) -> List[JobListing]:
    """Live fetch postings from Greenhouse public board API."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
    results: List[JobListing] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        response = await client.get(url, timeout=12.0)
        if response.status_code != 200:
            return []

        data = response.json()
        jobs = data.get("jobs", [])
        if not isinstance(jobs, list):
            return []

        for j in jobs:
            title = j.get("title", "")
            location_obj = j.get("location", {}) or {}
            job_loc = location_obj.get("name", "") or "Remote"
            is_job_remote = "remote" in job_loc.lower() or "remote" in title.lower()

            if role and not is_role_match(title, role):
                continue
            if location and not is_location_match(job_loc, location, is_remote):
                continue

            job_id = str(j.get("id", ""))
            apply_url = j.get("absolute_url") or f"https://boards.greenhouse.io/{company}/jobs/{job_id}"
            
            updated_at = j.get("updated_at", "")
            date_str = "Recently"
            if updated_at:
                try:
                    dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    date_str = dt.strftime("%b %d, %Y")
                except Exception:
                    date_str = "Recently"

            tags = []
            departments = j.get("departments", [])
            if departments and isinstance(departments, list):
                for d in departments:
                    if d.get("name"):
                        tags.append(d.get("name"))

            results.append(
                JobListing(
                    id=f"gh_{company}_{job_id}",
                    title=title,
                    company=company.capitalize(),
                    location=job_loc,
                    experience=exp if exp else "Entry / Mid",
                    apply_link=apply_url,
                    posted_date=date_str,
                    source="Greenhouse",
                    is_remote=is_job_remote,
                    tags=tags[:2],
                    fetched_at=now_iso,
                    posted_datetime=updated_at
                )
            )
    except Exception as e:
        logger.debug(f"Greenhouse fetch skipped for {company}: {e}")
        return []

    return results

async def fetch_greenhouse_jobs(
    role: str = "",
    location: str = "",
    exp: str = "",
    is_remote: bool = False,
    companies: Optional[List[str]] = None
) -> List[JobListing]:
    """Fetch Greenhouse jobs across companies in parallel."""
    target_companies = companies or GREENHOUSE_COMPANIES
    limits = httpx.Limits(max_keepalive_connections=30, max_connections=60)
    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        tasks = [
            fetch_company_greenhouse_jobs(client, comp, role, location, exp, is_remote)
            for comp in target_companies
        ]
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[JobListing] = []
    for r in results_lists:
        if isinstance(r, list):
            all_jobs.extend(r)

    return all_jobs
