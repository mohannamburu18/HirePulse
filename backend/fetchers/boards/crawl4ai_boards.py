import httpx
import asyncio
from bs4 import BeautifulSoup
from typing import List
import urllib.parse
import re
from ..base import JobListing

def get_indeed_fromage(posted: str) -> int:
    p = posted.lower().strip()
    if p in ["24h", "1d"]: return 1
    if p in ["3days", "3d"]: return 3
    if p in ["week", "7d"]: return 7
    if p in ["month", "30d"]: return 30
    return 14

async def fetch_crawl4ai_indeed(
    client: httpx.AsyncClient,
    role: str,
    location: str,
    posted: str = "any"
) -> List[JobListing]:
    """Crawl4AI DOM parser for Indeed live jobs."""
    encoded_role = urllib.parse.quote_plus(role or "Software Engineer")
    encoded_loc = urllib.parse.quote_plus(location or "Bangalore")
    fromage = get_indeed_fromage(posted)

    url = f"https://in.indeed.com/jobs?q={encoded_role}&l={encoded_loc}&fromage={fromage}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    results: List[JobListing] = []
    try:
        res = await client.get(url, headers=headers, timeout=7.0)
        if res.status_code != 200:
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        cards = soup.find_all("div", class_=re.compile("job_seen_beacon|jobsearch-SerpJobCard|cardOutline"))

        for card in cards:
            title_tag = card.find("h2", class_=re.compile("jobTitle")) or card.find("a", class_=re.compile("jcs-JobTitle"))
            comp_tag = card.find("span", {"data-testid": "company-name"}) or card.find("span", class_=re.compile("companyName"))
            loc_tag = card.find("div", {"data-testid": "text-location"}) or card.find("div", class_=re.compile("companyLocation"))
            link_tag = card.find("a", href=True)

            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            comp = comp_tag.get_text(strip=True) if comp_tag else "Leading Enterprise"
            job_loc = loc_tag.get_text(strip=True) if loc_tag else location

            raw_href = link_tag["href"] if link_tag else ""
            if raw_href.startswith("/"):
                apply_url = f"https://in.indeed.com{raw_href}"
            elif raw_href.startswith("http"):
                apply_url = raw_href
            else:
                apply_url = f"https://in.indeed.com/jobs?q={encoded_role}&l={encoded_loc}"

            results.append(
                JobListing(
                    id=f"indeed_{abs(hash(title + comp))}",
                    title=title,
                    company=comp,
                    location=job_loc,
                    experience="Entry / Mid",
                    apply_link=apply_url,
                    posted_date="Recently",
                    source="Indeed",
                    is_remote="remote" in job_loc.lower(),
                    tags=["Indeed Live Feed"]
                )
            )
    except Exception:
        pass

    return results

async def fetch_crawl4ai_jobs(
    role: str = "Software Engineer",
    location: str = "Bangalore",
    exp: str = "0-2",
    is_remote: bool = False,
    posted: str = "any"
) -> List[JobListing]:
    """Scraper 2: Crawl4AI multi-feed engine."""
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=40)
    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        return await fetch_crawl4ai_indeed(client, role, location, posted)

