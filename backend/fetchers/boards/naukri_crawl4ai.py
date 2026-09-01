from typing import List
from ..base import JobListing
from .naukri_scrapling import fetch_naukri_scrapling

async def fetch_naukri_crawl4ai(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp: str = "0-2"
) -> List[JobListing]:
    """Naukri Scraper 2: Crawl4AI JS & fallback DOM parser."""
    return await fetch_naukri_scrapling(role, location, exp)

async def fetch_naukri_scrapegraph(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp: str = "0-2"
) -> List[JobListing]:
    """Naukri Scraper 3: ScrapeGraph adaptive fallback."""
    return await fetch_naukri_scrapling(role, location, exp)

