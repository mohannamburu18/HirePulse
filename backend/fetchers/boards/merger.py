import asyncio
from typing import List, Dict, Any
from ..base import JobListing, normalize_text
from .linkedin_scrapling import fetch_linkedin_scrapling
from .linkedin_crawl4ai import fetch_linkedin_crawl4ai
from .linkedin_scrapegraph import fetch_linkedin_scrapegraph
from .indeed_scrapling import fetch_indeed_scrapling
from .indeed_crawl4ai import fetch_indeed_crawl4ai
from .indeed_scrapegraph import fetch_indeed_scrapegraph
from .naukri_scrapling import fetch_naukri_scrapling
from .naukri_crawl4ai import fetch_naukri_crawl4ai
from .naukri_scrapegraph import fetch_naukri_scrapegraph

async def run_linkedin_3scrapers(
    role: str = "Frontend Developer",
    location: str = "Remote",
    exp: str = "0-2",
    is_remote: bool = False,
    f_tpr: str = "r604800"
) -> Dict[str, Any]:
    """Run Scrapling, Crawl4AI, and ScrapeGraph in parallel for LinkedIn."""
    tasks = [
        fetch_linkedin_scrapling(role, location, exp, is_remote, f_tpr),
        fetch_linkedin_crawl4ai(role, location, exp, is_remote, f_tpr),
        fetch_linkedin_scrapegraph(role, location, exp, is_remote, f_tpr)
    ]
    res = await asyncio.gather(*tasks, return_exceptions=True)
    scrapling = res[0] if isinstance(res[0], list) else []
    crawl4ai = res[1] if isinstance(res[1], list) else []
    scrapegraph = res[2] if isinstance(res[2], list) else []

    all_jobs: List[JobListing] = []
    seen = set()
    for job in (scrapling + crawl4ai + scrapegraph):
        sig = f"{normalize_text(job.title)}_{normalize_text(job.company)}"
        if sig not in seen and job.apply_link not in seen:
            seen.add(sig)
            seen.add(job.apply_link)
            all_jobs.append(job)

    return {
        "stats": {"scrapling": len(scrapling), "crawl4ai": len(crawl4ai), "scrapegraph": len(scrapegraph), "merged": len(all_jobs)},
        "jobs": all_jobs
    }

async def run_indeed_3scrapers(
    role: str = "Frontend Developer",
    location: str = "Remote",
    fromage: int = 7
) -> List[JobListing]:
    """Run Indeed 3-scraper suite."""
    tasks = [
        fetch_indeed_scrapling(role, location, fromage),
        fetch_indeed_crawl4ai(role, location, fromage),
        fetch_indeed_scrapegraph(role, location, fromage)
    ]
    res = await asyncio.gather(*tasks, return_exceptions=True)
    all_jobs: List[JobListing] = []
    seen = set()
    for sublist in res:
        if isinstance(sublist, list):
            for job in sublist:
                sig = f"{normalize_text(job.title)}_{normalize_text(job.company)}"
                if sig not in seen:
                    seen.add(sig)
                    all_jobs.append(job)
    return all_jobs

async def run_naukri_3scrapers(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp: str = "0-2"
) -> List[JobListing]:
    """Run Naukri 3-scraper suite."""
    tasks = [
        fetch_naukri_scrapling(role, location, exp),
        fetch_naukri_crawl4ai(role, location, exp),
        fetch_naukri_scrapegraph(role, location, exp)
    ]
    res = await asyncio.gather(*tasks, return_exceptions=True)
    all_jobs: List[JobListing] = []
    seen = set()
    for sublist in res:
        if isinstance(sublist, list):
            for job in sublist:
                sig = f"{normalize_text(job.title)}_{normalize_text(job.company)}"
                if sig not in seen:
                    seen.add(sig)
                    all_jobs.append(job)
    return all_jobs

async def run_multi_scraper_boards(
    role: str = "Frontend Developer",
    location: str = "Remote",
    exp: str = "0-2",
    is_remote: bool = False,
    posted: str = "week"
) -> Dict[str, Any]:
    """Parallel multi-scraper for LinkedIn, Indeed, and Naukri."""
    fromage = 7
    f_tpr = "r604800"
    if posted == "month":
        f_tpr = "r2592000"
        fromage = 30

    tasks = [
        run_linkedin_3scrapers(role, location, exp, is_remote, f_tpr),
        run_indeed_3scrapers(role, location, fromage),
        run_naukri_3scrapers(role, location, exp)
    ]

    res = await asyncio.gather(*tasks, return_exceptions=True)
    li_res = res[0] if isinstance(res[0], dict) else {"stats": {}, "jobs": []}
    ind_jobs = res[1] if isinstance(res[1], list) else []
    nk_jobs = res[2] if isinstance(res[2], list) else []

    all_jobs: List[JobListing] = []
    all_jobs.extend(li_res.get("jobs", []))
    all_jobs.extend(ind_jobs)
    all_jobs.extend(nk_jobs)

    return {
        "linkedin_stats": li_res.get("stats", {}),
        "indeed_count": len(ind_jobs),
        "naukri_count": len(nk_jobs),
        "total_board_jobs": len(all_jobs),
        "jobs": all_jobs
    }
