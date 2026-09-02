import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Core filters and caching
from core.filters.experience_detector import (
    detect_experience_level,
    role_match,
    location_match
)
from core.cache.job_cache import get as cache_get, set as cache_set

# Layer 1: JSON APIs (fastest)
from fetchers.json_apis.remoteok import fetch_remoteok_jobs
from fetchers.json_apis.hackernews import fetch_hackernews_jobs

# Layer 2: Indian Portals (targeted)
from fetchers.indian.internshala import fetch_internshala_jobs
from fetchers.indian.cutshort import fetch_cutshort_jobs
from fetchers.indian.instahyre import fetch_instahyre_jobs

# Layer 3: ATS Endpoints
from fetchers.ats.lever import fetch_lever_jobs
from fetchers.ats.greenhouse import fetch_greenhouse_jobs
from fetchers.ats.ashby import fetch_ashby_jobs
from fetchers.ats.workday import fetch_workday_jobs
from fetchers.companies import (
    get_lever_companies_for_location,
    get_greenhouse_companies_for_location,
    get_ashby_companies_for_location
)

# Layer 4: Enhanced Boards (with multi-method fallbacks)
from fetchers.boards.enhanced.linkedin_enhanced import fetch_linkedin_comprehensive
from fetchers.boards.enhanced.indeed_enhanced import fetch_indeed_comprehensive
from fetchers.boards.enhanced.naukri_enhanced import fetch_naukri_comprehensive

# Backward compatibility imports
from fetchers.base import JobListing, normalize_text
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

# ============================================================================
# Backward Compatibility Mergers
# ============================================================================
async def merge_3_scrapers_linkedin(role: str, location: str, exp: str, is_remote: bool = False) -> Dict[str, Any]:
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


# ============================================================================
# Deduplication and Normalization Helper
# ============================================================================
def merge_jobs(all_job_lists: List[List[Any]]) -> List[Dict[str, Any]]:
    """
    Merge multiple heterogeneous job lists (JobListing models and raw dicts),
    normalize all schema attributes, and deduplicate by URL and signature.
    """
    merged: List[Dict[str, Any]] = []
    seen_urls = set()
    seen_sigs = set()

    for job_list in all_job_lists:
        if not isinstance(job_list, list):
            continue

        for item in job_list:
            if hasattr(item, "model_dump"):
                j = item.model_dump()
            elif isinstance(item, dict):
                j = dict(item)
            else:
                continue

            title = str(j.get("title") or "").strip()
            if not title:
                continue

            company = str(j.get("company") or j.get("companyName") or "Technology Enterprise").strip()
            loc = str(j.get("location") or "India").strip()
            desc = str(j.get("description") or j.get("jobDescription") or "").strip()
            apply_url = str(j.get("apply_link") or j.get("url") or j.get("jobUrl") or "").strip()
            posted_date = str(j.get("posted_date") or j.get("postedDate") or "Recently").strip()
            source = str(j.get("source") or "Live Aggregator").strip()

            if not apply_url:
                continue

            # Normalized deduplication keys
            sig = f"{normalize_text(title)}_{normalize_text(company)}"
            clean_url = apply_url.split("?")[0] if "?" in apply_url else apply_url

            if clean_url in seen_urls or sig in seen_sigs:
                continue

            seen_urls.add(clean_url)
            seen_sigs.add(sig)

            normalized_record = {
                "id": j.get("id") or f"job_{abs(hash(sig + clean_url))}",
                "title": title,
                "company": company,
                "location": loc,
                "description": desc,
                "apply_link": apply_url,
                "url": apply_url,
                "posted_date": posted_date,
                "source": source,
                "raw": j.get("raw") or j
            }
            merged.append(normalized_record)

    return merged


def is_experience_compatible(title: str, description: str, user_exp: str) -> bool:
    """Check if detected experience level conforms to user preference."""
    detected = detect_experience_level(title, description)
    u_exp = (user_exp or "fresher").strip().lower()

    if u_exp in ["fresher", "0", "0-1"]:
        return detected in ["fresher", "0-2"]
    elif u_exp in ["0-2"]:
        return detected in ["fresher", "0-2"]
    elif u_exp in ["2-5", "mid"]:
        return detected in ["2-5", "0-2"]
    elif u_exp in ["5+", "senior"]:
        return detected in ["5+", "2-5"]
    return True


# ============================================================================
# Main Orchestrator Function
# ============================================================================
async def fetch_all_jobs_realtime(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp: str = "fresher",
    is_remote: bool = False,
    candidate_skills: Optional[List[str]] = None,
    candidate_years: float = 1.0,
    limit: int = 600,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Multi-Layer Live Real-Time Universal Job Engine:
    
    1. Check SQLite JobCache for key f"{role}_{location}_{exp}"
    2. Concurrent 4-Layer Scraping:
       - Layer 1: JSON APIs (RemoteOK, Hacker News)
       - Layer 2: Indian Portals (Internshala, Cutshort, Instahyre)
       - Layer 3: ATS Endpoints (Lever, Greenhouse, Ashby, Workday)
       - Layer 4: Enhanced Boards (LinkedIn, Indeed, Naukri with fallbacks)
    3. Merge and deduplicate via merge_jobs()
    4. Strict client-side filters:
       - Experience (detect_experience_level)
       - Location (location_match)
       - Role (role_match)
    5. Match and rank using resume skills
    6. Cache and return ranked results
    """
    start_time = time.time()
    now_iso = datetime.now(timezone.utc).isoformat()
    cache_key = f"{role}_{location}_{exp}".strip().lower().replace(" ", "_")

    logger.info(f"=== Starting HirePulse Orchestrator Search (Key: {cache_key}) ===")

    # 1. Check JobCache
    if not force_refresh:
        cached_data = cache_get(cache_key)
        if cached_data is not None and isinstance(cached_data, list) and len(cached_data) > 0:
            logger.info(f"CACHE HIT: Found {len(cached_data)} fresh cached jobs for {cache_key}")
            elapsed = round(time.time() - start_time, 2)
            cached_sources_count: Dict[str, int] = {}
            for j in cached_data[:limit]:
                src = j.get("source", "Other")
                cached_sources_count[src] = cached_sources_count.get(src, 0) + 1

            return {
                "status": "success",
                "is_realtime": False,
                "cached": True,
                "fetched_at": now_iso,
                "total": len(cached_data[:limit]),
                "elapsed_seconds": elapsed,
                "query": {"role": role, "location": location, "exp": exp, "is_remote": is_remote},
                "sources_breakdown": cached_sources_count,
                "jobs": cached_data[:limit]
            }


    logger.info("CACHE MISS: Executing live multi-layer aggregation concurrently...")

    lever_comps = get_lever_companies_for_location(location)
    gh_comps = get_greenhouse_companies_for_location(location)
    ashby_comps = get_ashby_companies_for_location(location)

    # 2. Build 4-Layer Concurrent Tasks
    # Layer 1: JSON APIs (fastest)
    layer1_tasks = [
        fetch_remoteok_jobs(role, location, exp),
        fetch_hackernews_jobs(role, location, exp)
    ]

    # Layer 2: Indian Portals (targeted)
    layer2_tasks = [
        fetch_internshala_jobs(role, location, exp),
        fetch_cutshort_jobs(role, location, exp),
        fetch_instahyre_jobs(role, location, exp)
    ]

    # Layer 3: ATS Endpoints
    layer3_tasks = [
        fetch_lever_jobs(role, location, exp, is_remote, companies=lever_comps),
        fetch_greenhouse_jobs(role, location, exp, is_remote, companies=gh_comps),
        fetch_ashby_jobs(role, location, exp, is_remote, companies=ashby_comps),
        fetch_workday_jobs(role, location, exp, is_remote)
    ]

    # Layer 4: Enhanced Boards (with comprehensive fallbacks)
    layer4_tasks = [
        fetch_linkedin_comprehensive(role, location, exp),
        fetch_indeed_comprehensive(role, location, exp),
        fetch_naukri_comprehensive(role, location, exp)
    ]

    all_tasks = layer1_tasks + layer2_tasks + layer3_tasks + layer4_tasks
    logger.info(f"Dispatching {len(all_tasks)} fetcher tasks across 4 layers concurrently...")

    results = await asyncio.gather(*all_tasks, return_exceptions=True)

    # Unpack results
    remoteok_jobs = results[0] if isinstance(results[0], list) else []
    hackernews_jobs = results[1] if isinstance(results[1], list) else []
    internshala_jobs = results[2] if isinstance(results[2], list) else []
    cutshort_jobs = results[3] if isinstance(results[3], list) else []
    instahyre_jobs = results[4] if isinstance(results[4], list) else []
    lever_jobs = results[5] if isinstance(results[5], list) else []
    greenhouse_jobs = results[6] if isinstance(results[6], list) else []
    ashby_jobs = results[7] if isinstance(results[7], list) else []
    workday_jobs = results[8] if isinstance(results[8], list) else []
    linkedin_jobs = results[9] if isinstance(results[9], list) else []
    indeed_jobs = results[10] if isinstance(results[10], list) else []
    naukri_jobs = results[11] if isinstance(results[11], list) else []

    layer_breakdown = {
        "Layer 1 (JSON APIs)": len(remoteok_jobs) + len(hackernews_jobs),
        "Layer 2 (Indian Portals)": len(internshala_jobs) + len(cutshort_jobs) + len(instahyre_jobs),
        "Layer 3 (ATS Endpoints)": len(lever_jobs) + len(greenhouse_jobs) + len(ashby_jobs) + len(workday_jobs),
        "Layer 4 (Enhanced Boards)": len(linkedin_jobs) + len(indeed_jobs) + len(naukri_jobs)
    }
    logger.info(f"Raw Scraping Results: {layer_breakdown}")

    # 3. Merge & Deduplicate
    merged_pool = merge_jobs([
        remoteok_jobs, hackernews_jobs,
        internshala_jobs, cutshort_jobs, instahyre_jobs,
        lever_jobs, greenhouse_jobs, ashby_jobs, workday_jobs,
        linkedin_jobs, indeed_jobs, naukri_jobs
    ])
    logger.info(f"Total deduplicated candidates after merge: {len(merged_pool)}")

    # 4. Strict Client-Side Filtering
    filtered_jobs: List[Dict[str, Any]] = []
    for job in merged_pool:
        title = job.get("title", "")
        job_loc = job.get("location", "")
        desc = job.get("description", "")

        # A. Role Match
        if not role_match(title, role):
            continue

        # B. Location Match
        if not location_match(job_loc, location):
            continue

        # C. Experience Detection Match
        if not is_experience_compatible(title, desc, exp):
            continue

        filtered_jobs.append(job)

    logger.info(f"Filtered jobs passing Role, Location & Experience checks: {len(filtered_jobs)}")

    # If strict filtering produced too few results due to edge cases, retain merged_pool with location match
    if len(filtered_jobs) < 10 and len(merged_pool) >= 10:
        logger.info("Applying relaxed safety fallback to ensure sufficient candidates...")
        filtered_jobs = [j for j in merged_pool if location_match(j.get("location", ""), location)]

    # 5. Calculate Matching Scores with Resume Skills
    skills_for_scoring = candidate_skills or ["React", "TypeScript", "Node.js", "Python", "FastAPI", "SQL"]
    ranked_jobs = match_and_rank_jobs(
        jobs=filtered_jobs,
        candidate_skills=skills_for_scoring,
        candidate_years=candidate_years,
        candidate_bracket=exp,
        desired_role=role,
        target_location=location,
        is_remote_only=is_remote
    )

    # 6. Sort by match_score descending
    ranked_jobs.sort(key=lambda x: x.get("match_score", 0), reverse=True)

    # 7. Store in Cache (6-hour TTL)
    if ranked_jobs:
        cache_set(cache_key, ranked_jobs, ttl_hours=6)
        logger.info(f"Stored {len(ranked_jobs)} ranked jobs into SQLite JobCache (Key: {cache_key})")

    elapsed = round(time.time() - start_time, 2)
    avg_score = round(sum(j.get("match_score", 85) for j in ranked_jobs) / max(1, len(ranked_jobs))) if ranked_jobs else 85

    sources_count: Dict[str, int] = {}
    for j in ranked_jobs:
        src = j.get("source", "Other")
        sources_count[src] = sources_count.get(src, 0) + 1

    return {
        "status": "success",
        "is_realtime": True,
        "cached": False,
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
        "layers_breakdown": layer_breakdown,
        "sources_breakdown": sources_count,
        "raw_counts": {
            "remoteok": len(remoteok_jobs),
            "hackernews": len(hackernews_jobs),
            "internshala": len(internshala_jobs),
            "cutshort": len(cutshort_jobs),
            "instahyre": len(instahyre_jobs),
            "lever": len(lever_jobs),
            "greenhouse": len(greenhouse_jobs),
            "ashby": len(ashby_jobs),
            "workday": len(workday_jobs),
            "linkedin": len(linkedin_jobs),
            "indeed": len(indeed_jobs),
            "naukri": len(naukri_jobs),
            "total_deduplicated": len(merged_pool),
            "total_filtered": len(filtered_jobs)
        },
        "jobs": ranked_jobs[:limit]
    }

# Function alias for orchestrator callers
orchestrate = fetch_all_jobs_realtime
