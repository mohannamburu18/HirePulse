import httpx
import asyncio
from bs4 import BeautifulSoup
import urllib.parse
import re
from typing import List
from .base import JobListing

async def fetch_indeed_rss(
    client: httpx.AsyncClient,
    domain: str,
    role: str,
    location: str,
    exp: str
) -> List[JobListing]:
    """Fetch live Indeed job postings via RSS and direct job feed."""
    encoded_role = urllib.parse.quote_plus(role or "Developer")
    encoded_loc = urllib.parse.quote_plus(location or "India")
    
    url = f"https://{domain}/rss?q={encoded_role}&l={encoded_loc}&sort=date&limit=50"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml,application/xml,text/xml;q=0.9,*/*;q=0.8"
    }

    results: List[JobListing] = []
    try:
        response = await client.get(url, headers=headers, timeout=8.0)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "xml" if "xml" in response.headers.get("content-type", "") else "html.parser")
        items = soup.find_all("item")

        for item in items:
            title_tag = item.find("title")
            link_tag = item.find("link") or item.find("guid")
            source_tag = item.find("source")
            desc_tag = item.find("description")
            pub_tag = item.find("pubDate")

            if not title_tag or not link_tag:
                continue

            raw_title = title_tag.get_text(strip=True)
            # Indeed RSS title format: "Job Title - Company Name - Location"
            parts = [p.strip() for p in raw_title.split(" - ")]
            title = parts[0]
            company = parts[1] if len(parts) > 1 else (source_tag.get_text(strip=True) if source_tag else "Top Employer")
            job_loc = parts[2] if len(parts) > 2 else location

            apply_link = link_tag.get_text(strip=True)
            if not apply_link.startswith("http"):
                apply_link = f"https://{domain}/viewjob?jk={abs(hash(title + company))}"

            job_id_match = re.search(r'jk=([a-zA-Z0-9]+)', apply_link)
            job_id = job_id_match.group(1) if job_id_match else str(abs(hash(apply_link)))

            date_str = pub_tag.get_text(strip=True)[:16] if pub_tag else "Recently"
            is_job_remote = "remote" in job_loc.lower() or "remote" in title.lower()

            results.append(
                JobListing(
                    id=f"indeed_{job_id}",
                    title=title,
                    company=company,
                    location=job_loc,
                    experience=exp if exp else "Any",
                    apply_link=apply_link,
                    posted_date=date_str,
                    source="Indeed",
                    is_remote=is_job_remote,
                    description_snippet=desc_tag.get_text(strip=True)[:180] if desc_tag else None
                )
            )
    except Exception:
        pass

    return results

async def fetch_indeed_jobs(
    role: str = "",
    location: str = "",
    exp: str = "",
    is_remote: bool = False
) -> List[JobListing]:
    """Fetch Indeed jobs across international and India domains."""
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        domains = ["in.indeed.com", "www.indeed.com"]
        tasks = [
            fetch_indeed_rss(client, domain, role, "Remote" if is_remote else location, exp)
            for domain in domains
        ]
        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[JobListing] = []
    seen = set()
    for res in results_lists:
        if isinstance(res, list):
            for job in res:
                if job.id not in seen:
                    seen.add(job.id)
                    all_jobs.append(job)

    return all_jobs

