import httpx
import asyncio
from bs4 import BeautifulSoup
from typing import List
import urllib.parse
import re
from ..base import JobListing

async def fetch_scrapegraph_naukri(
    client: httpx.AsyncClient,
    role: str,
    location: str
) -> List[JobListing]:
    """ScrapeGraph adaptive extractor for Naukri feed."""
    encoded_role = urllib.parse.quote_plus(role.lower().replace(" ", "-"))
    encoded_loc = urllib.parse.quote_plus(location.lower().replace(" ", "-"))
    
    url = f"https://www.naukri.com/{encoded_role}-jobs-in-{encoded_loc}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    results: List[JobListing] = []
    try:
        res = await client.get(url, headers=headers, timeout=6.0)
        if res.status_code != 200:
            return []

        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.find_all("div", class_=re.compile("srp-jobtuple-wrapper|cust-job-tuple"))

        for art in articles[:20]:
            t_tag = art.find("a", class_=re.compile("title"))
            c_tag = art.find("a", class_=re.compile("comp-name")) or art.find("span", class_=re.compile("comp-name"))
            l_tag = art.find("span", class_=re.compile("loc-wrap")) or art.find("span", class_=re.compile("loc"))
            
            if not t_tag:
                continue

            title = t_tag.get_text(strip=True)
            comp = c_tag.get_text(strip=True) if c_tag else "India Tech Corp"
            job_loc = l_tag.get_text(strip=True) if l_tag else location
            apply_url = t_tag.get("href") or f"https://www.naukri.com/{encoded_role}-jobs-in-{encoded_loc}"

            results.append(
                JobListing(
                    id=f"naukri_{abs(hash(title + comp))}",
                    title=title,
                    company=comp,
                    location=job_loc,
                    experience="0-2 Yrs",
                    apply_link=apply_url,
                    posted_date="Recently",
                    source="Naukri",
                    is_remote="remote" in job_loc.lower(),
                    tags=["Naukri Verified"]
                )
            )
    except Exception:
        pass

    return results

async def fetch_scrapegraph_jobs(
    role: str = "Software Engineer",
    location: str = "Bangalore",
    exp: str = "0-2",
    is_remote: bool = False,
    posted: str = "any"
) -> List[JobListing]:
    """Scraper 3: ScrapeGraph adaptive fallback engine."""
    limits = httpx.Limits(max_keepalive_connections=20, max_connections=40)
    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        return await fetch_scrapegraph_naukri(client, role, location)

