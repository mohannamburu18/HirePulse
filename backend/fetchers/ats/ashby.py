import httpx
import asyncio
import re
import json
from typing import List, Optional
from datetime import datetime, timezone
import logging
from ..base import JobListing, is_role_match, is_location_match

logger = logging.getLogger(__name__)

ASHBY_COMPANIES = [
    "linear", "ramp", "retool", "ashby", "quora", "notion", "sentry",
    "elevenlabs", "perplexity", "cursor", "posthog", "monzo", "resend",
    "replicate", "vanta", "loom", "descript", "vercel"
]

async def fetch_company_ashby_jobs(
    client: httpx.AsyncClient,
    company: str,
    role: str = "",
    location: str = "",
    exp: str = "",
    is_remote: bool = False
) -> List[JobListing]:
    """Live fetch postings from Ashby via public board appData."""
    url = f"https://jobs.ashbyhq.com/{company}"
    results: List[JobListing] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    try:
        response = await client.get(url, headers=headers, timeout=10.0)
        if response.status_code != 200:
            return []

        match = re.search(r'window\.__appData\s*=\s*(\{.*?\});', response.text)
        if not match:
            return []

        data = json.loads(match.group(1))
        postings = data.get("jobBoard", {}).get("jobPostings", [])
        if not isinstance(postings, list):
            return []

        for p in postings:
            title = p.get("title", "")
            job_loc = p.get("locationName", "") or "Remote"
            is_job_remote = p.get("isRemote", False) or "remote" in job_loc.lower() or "remote" in title.lower()

            if role and not is_role_match(title, role):
                continue
            if location and not is_location_match(job_loc, location, is_remote):
                continue

            job_id = str(p.get("id", ""))
            apply_url = f"https://jobs.ashbyhq.com/{company}/{job_id}"
            
            published_at = p.get("publishedAt", "")
            date_str = "Recently"
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                    date_str = dt.strftime("%b %d, %Y")
                except Exception:
                    date_str = "Recently"

            tags = []
            if p.get("departmentName"):
                tags.append(p.get("departmentName"))
            if p.get("employmentType"):
                tags.append(p.get("employmentType"))

            results.append(
                JobListing(
                    id=f"ashby_{company}_{job_id}",
                    title=title,
                    company=company.capitalize(),
                    location=job_loc,
                    experience=exp if exp else "Entry / Mid",
                    apply_link=apply_url,
                    posted_date=date_str,
                    source="Ashby",
                    is_remote=is_job_remote,
                    tags=tags[:2],
                    fetched_at=now_iso,
                    posted_datetime=published_at
                )
            )
    except Exception as e:
        logger.debug(f"Ashby fetch skipped for {company}: {e}")
        return []

    return results

async def fetch_ashby_jobs(
    role: str = "",
    location: str = "",
    exp: str = "",
    is_remote: bool = False,
    companies: Optional[List[str]] = None
) -> List[JobListing]:
    """Fetch Ashby jobs across all tracked companies in parallel."""
    target_companies = companies or ASHBY_COMPANIES
    limits = httpx.Limits(max_keepalive_connections=30, max_connections=60)
    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        tasks = [
            fetch_company_ashby_jobs(client, comp, role, location, exp, is_remote)
            for comp in target_companies
        ]
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[JobListing] = []
    for r in results_lists:
        if isinstance(r, list):
            all_jobs.extend(r)

    return all_jobs
