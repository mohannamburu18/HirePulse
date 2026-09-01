import asyncio
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import logging

from fetchers.base import JobListing, normalize_text
from core.location_filter import location_match, clean_location_string
from fetchers.companies import (
    get_lever_companies_for_location,
    get_greenhouse_companies_for_location,
    get_ashby_companies_for_location
)
from fetchers.ats.lever import fetch_lever_jobs
from fetchers.ats.greenhouse import fetch_greenhouse_jobs
from fetchers.ats.ashby import fetch_ashby_jobs
from fetchers.ats.workday import fetch_workday_jobs
from fetchers.boards.linkedin_scrapling import fetch_linkedin_scrapling
from fetchers.boards.linkedin_crawl4ai import fetch_linkedin_crawl4ai
from fetchers.boards.linkedin_scrapegraph import fetch_linkedin_scrapegraph
from fetchers.boards.indeed_scrapling import fetch_indeed_scrapling
from fetchers.boards.indeed_crawl4ai import fetch_indeed_crawl4ai
from fetchers.boards.indeed_scrapegraph import fetch_indeed_scrapegraph
from fetchers.boards.naukri_scrapling import fetch_naukri_scrapling
from fetchers.boards.naukri_crawl4ai import fetch_naukri_crawl4ai
from fetchers.boards.naukri_scrapegraph import fetch_naukri_scrapegraph
from matcher import match_and_rank_jobs

logger = logging.getLogger(__name__)

async def merge_3_scrapers_linkedin(role: str, location: str, exp: str, is_remote: bool = False) -> Dict[str, Any]:
    """Execute 3 scrapers in parallel for LinkedIn guest API."""
    tasks = [
        fetch_linkedin_scrapling(role, location, exp, is_remote),
        fetch_linkedin_crawl4ai(role, location, exp, is_remote),
        fetch_linkedin_scrapegraph(role, location, exp, is_remote)
    ]
    res = await asyncio.gather(*tasks, return_exceptions=True)
    scrapling = res[0] if isinstance(res[0], list) else []
    crawl4ai = res[1] if isinstance(res[1], list) else []
    scrapegraph = res[2] if isinstance(res[2], list) else []

    merged: List[JobListing] = []
    seen = set()
    for job in (scrapling + crawl4ai + scrapegraph):
        sig = f"{normalize_text(job.title)}_{normalize_text(job.company)}"
        if sig not in seen and job.apply_link not in seen:
            seen.add(sig)
            seen.add(job.apply_link)
            merged.append(job)

    return {
        "scrapling": len(scrapling),
        "crawl4ai": len(crawl4ai),
        "scrapegraph": len(scrapegraph),
        "total": len(merged),
        "jobs": merged
    }

async def merge_3_scrapers_indeed(role: str, location: str) -> List[JobListing]:
    """Execute 3 scrapers in parallel for Indeed."""
    tasks = [
        fetch_indeed_scrapling(role, location),
        fetch_indeed_crawl4ai(role, location),
        fetch_indeed_scrapegraph(role, location)
    ]
    res = await asyncio.gather(*tasks, return_exceptions=True)
    merged: List[JobListing] = []
    seen = set()
    for sublist in res:
        if isinstance(sublist, list):
            for job in sublist:
                sig = f"{normalize_text(job.title)}_{normalize_text(job.company)}"
                if sig not in seen:
                    seen.add(sig)
                    merged.append(job)
    return merged

async def merge_3_scrapers_naukri(role: str, location: str, exp: str) -> List[JobListing]:
    """Execute 3 scrapers in parallel for Naukri."""
    tasks = [
        fetch_naukri_scrapling(role, location, exp),
        fetch_naukri_crawl4ai(role, location, exp),
        fetch_naukri_scrapegraph(role, location, exp)
    ]
    res = await asyncio.gather(*tasks, return_exceptions=True)
    merged: List[JobListing] = []
    seen = set()
    for sublist in res:
        if isinstance(sublist, list):
            for job in sublist:
                sig = f"{normalize_text(job.title)}_{normalize_text(job.company)}"
                if sig not in seen:
                    seen.add(sig)
                    merged.append(job)
    return merged

async def fetch_all_jobs_realtime(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp: str = "fresher",
    is_remote: bool = False,
    candidate_skills: Optional[List[str]] = None,
    candidate_years: float = 1.0,
    limit: int = 600
) -> Dict[str, Any]:
    """
    Live real-time aggregation across all 7 sources concurrently.
    Zero seed data, 100% live fetched now.
    """
    start_time = time.time()
    now_iso = datetime.now(timezone.utc).isoformat()

    lever_comps = get_lever_companies_for_location(location)
    gh_comps = get_greenhouse_companies_for_location(location)
    ashby_comps = get_ashby_companies_for_location(location)

    # 7 sources in parallel
    tasks = [
        fetch_lever_jobs(role, location, exp, is_remote, companies=lever_comps),
        fetch_greenhouse_jobs(role, location, exp, is_remote, companies=gh_comps),
        fetch_ashby_jobs(role, location, exp, is_remote, companies=ashby_comps),
        fetch_workday_jobs(role, location, exp, is_remote),
        merge_3_scrapers_linkedin(role, location, exp, is_remote),
        merge_3_scrapers_indeed(role, location),
        merge_3_scrapers_naukri(role, location, exp)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    lever_jobs = results[0] if isinstance(results[0], list) else []
    greenhouse_jobs = results[1] if isinstance(results[1], list) else []
    ashby_jobs = results[2] if isinstance(results[2], list) else []
    workday_jobs = results[3] if isinstance(results[3], list) else []
    
    li_data = results[4] if isinstance(results[4], dict) else {"total": 0, "jobs": []}
    linkedin_jobs = li_data.get("jobs", [])
    
    indeed_jobs = results[5] if isinstance(results[5], list) else []
    naukri_jobs = results[6] if isinstance(results[6], list) else []

    all_raw: List[JobListing] = []
    all_raw.extend(lever_jobs)
    all_raw.extend(greenhouse_jobs)
    all_raw.extend(ashby_jobs)
    all_raw.extend(workday_jobs)
    all_raw.extend(linkedin_jobs)
    all_raw.extend(indeed_jobs)
    all_raw.extend(naukri_jobs)

    # Filter by Location & Deduplicate
    unique_jobs: List[Dict[str, Any]] = []
    seen_sigs = set()
    seen_links = set()

    for job in all_raw:
        if not location_match(job.location, location, is_remote):
            continue

        sig = f"{normalize_text(job.title)}_{normalize_text(job.company)}"
        if sig in seen_sigs or job.apply_link in seen_links:
            continue
        seen_sigs.add(sig)
        seen_links.add(job.apply_link)

        j_dict = job.model_dump()
        j_dict["location"] = clean_location_string(job.location, default_location=location)
        unique_jobs.append(j_dict)

    # Score and rank using resume skills (Phase 1)
    skills_for_scoring = candidate_skills or ["React", "TypeScript", "Node.js", "Python", "FastAPI"]
    ranked_jobs = match_and_rank_jobs(
        jobs=unique_jobs,
        candidate_skills=skills_for_scoring,
        candidate_years=candidate_years,
        candidate_bracket=exp,
        desired_role=role,
        target_location=location,
        is_remote_only=is_remote
    )

    # Calculate sources count on final ranked set
    sources_count = {
        "Lever": 0,
        "Greenhouse": 0,
        "Ashby": 0,
        "Workday": 0,
        "LinkedIn": 0,
        "Indeed": 0,
        "Naukri": 0
    }
    for j in ranked_jobs:
        src = j.get("source", "Other")
        if src in sources_count:
            sources_count[src] += 1

    elapsed = round(time.time() - start_time, 2)
    avg_score = round(sum(j.get("match_score", 85) for j in ranked_jobs) / max(1, len(ranked_jobs))) if ranked_jobs else 85

    return {
        "status": "success",
        "is_realtime": True,
        "fetched_at": now_iso,
        "total": len(ranked_jobs[:limit]),
        "average_match_score": avg_score,
        "elapsed_seconds": elapsed,
        "query": {
            "role": role,
            "location": location,
            "exp": exp,
            "is_remote": is_remote
        },
        "sources_breakdown": sources_count,
        "raw_counts": {
            "lever": len(lever_jobs),
            "greenhouse": len(greenhouse_jobs),
            "ashby": len(ashby_jobs),
            "workday": len(workday_jobs),
            "linkedin": len(linkedin_jobs),
            "indeed": len(indeed_jobs),
            "naukri": len(naukri_jobs),
            "total_raw": len(all_raw)
        },
        "jobs": ranked_jobs[:limit]
    }

