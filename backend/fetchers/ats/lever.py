import httpx
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import logging
from ..base import JobListing, is_role_match, is_location_match

logger = logging.getLogger(__name__)

# Tracked active Lever company boards
LEVER_COMPANIES = [
    "meesho", "cred", "spotify", "palantir", "coupa", "atlassian", "canva",
    "affirm", "benchling", "mux", "hasura", "postman", "sourcegraph",
    "grammarly", "elastic", "browserstack", "chargebee", "upstox", "zoho",
    "razorpay", "swiggy", "phonepe", "groww", "zerodha", "freshworks"
]

async def fetch_company_lever_jobs(
    client: httpx.AsyncClient,
    company: str,
    role: str = "",
    location: str = "",
    exp: str = "",
    is_remote: bool = False
) -> List[JobListing]:
    """Live fetch postings for a company from Lever public JSON API (No seed, real-time only)."""
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    results: List[JobListing] = []
    now_iso = datetime.now(timezone.utc).isoformat()

    try:
        response = await client.get(url, timeout=12.0)
        if response.status_code != 200:
            return []

        postings = response.json()
        if not isinstance(postings, list):
            return []

        for p in postings:
            title = p.get("text", "")
            categories = p.get("categories", {}) or {}
            job_loc = categories.get("location", "") or categories.get("workplaceType", "Remote")
            is_job_remote = "remote" in job_loc.lower() or "remote" in title.lower() or categories.get("workplaceType", "").lower() == "remote"

            # Filter if role or location specified
            if role and not is_role_match(title, role):
                continue
            if location and not is_location_match(job_loc, location, is_remote):
                continue

            posting_id = p.get("id", "")
            apply_url = p.get("hostedUrl") or p.get("applyUrl") or f"https://jobs.lever.co/{company}/{posting_id}"
            
            # Format creation date & raw timestamp
            created_at_ms = p.get("createdAt")
            posted_dt = None
            if created_at_ms and isinstance(created_at_ms, (int, float)):
                posted_dt = datetime.fromtimestamp(created_at_ms / 1000, tz=timezone.utc)
                date_str = posted_dt.strftime("%b %d, %Y")
            else:
                date_str = "Recently"

            tags = []
            if categories.get("team"):
                tags.append(categories.get("team"))
            if categories.get("commitment"):
                tags.append(categories.get("commitment"))

            results.append(
                JobListing(
                    id=f"lever_{company}_{posting_id}",
                    title=title,
                    company=company.capitalize(),
                    location=job_loc,
                    experience=exp if exp else "Entry / Mid",
                    apply_link=apply_url,
                    posted_date=date_str,
                    source="Lever",
                    is_remote=is_job_remote,
                    tags=tags[:2],
                    description_snippet=p.get("descriptionPlain", "")[:200] if p.get("descriptionPlain") else None,
                    fetched_at=now_iso,
                    created_at_ms=created_at_ms
                )
            )
    except Exception as e:
        logger.debug(f"Lever fetch skipped for {company}: {e}")
        return []

    return results

async def fetch_lever_jobs(
    role: str = "",
    location: str = "",
    exp: str = "",
    is_remote: bool = False,
    companies: Optional[List[str]] = None
) -> List[JobListing]:
    """Fetch all Lever jobs in parallel across tracked companies."""
    target_companies = companies or LEVER_COMPANIES
    limits = httpx.Limits(max_keepalive_connections=30, max_connections=60)
    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        tasks = [
            fetch_company_lever_jobs(client, comp, role, location, exp, is_remote)
            for comp in target_companies
        ]
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[JobListing] = []
    for r in results_lists:
        if isinstance(r, list):
            all_jobs.extend(r)

    return all_jobs
