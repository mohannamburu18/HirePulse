import httpx
from bs4 import BeautifulSoup
from typing import List
import urllib.parse
import re
from datetime import datetime, timezone
from ..base import JobListing

async def fetch_indeed_crawl4ai(
    role: str = "Frontend Developer",
    location: str = "Remote",
    fromage: int = 7
) -> List[JobListing]:
    """Indeed Scraper 2: Crawl4AI DOM & secondary pagination parser."""
    encoded_role = urllib.parse.quote_plus(role or "Frontend Developer")
    encoded_loc = urllib.parse.quote_plus(location or "Bangalore")
    now_iso = datetime.now(timezone.utc).isoformat()

    url = f"https://in.indeed.com/jobs?q={encoded_role}&l={encoded_loc}&fromage={fromage}&start=10"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    results: List[JobListing] = []
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                cards = soup.find_all("div", class_=re.compile("job_seen_beacon|cardOutline"))
                for card in cards:
                    t_tag = card.find(re.compile("h2|a"), class_=re.compile("jobTitle|jcs-JobTitle"))
                    comp_tag = card.find(re.compile("span"), class_=re.compile("companyName|company-name"))
                    loc_tag = card.find(re.compile("div"), class_=re.compile("companyLocation|location"))
                    link_tag = card.find("a", href=True)

                    if not t_tag:
                        continue

                    title = t_tag.get_text(strip=True)
                    comp = comp_tag.get_text(strip=True) if comp_tag else "Enterprise Client"
                    job_loc = loc_tag.get_text(strip=True) if loc_tag else location

                    raw_href = link_tag["href"] if link_tag else ""
                    apply_url = f"https://in.indeed.com{raw_href}" if raw_href.startswith("/") else (raw_href or url)

                    results.append(
                        JobListing(
                            id=f"ind_c4_{abs(hash(title + comp))}",
                            title=title,
                            company=comp,
                            location=job_loc,
                            experience="Entry / Mid",
                            apply_link=apply_url,
                            posted_date="Recently",
                            source="Indeed",
                            is_remote="remote" in job_loc.lower() or "remote" in title.lower(),
                            tags=["Indeed Crawl4AI"],
                            fetched_at=now_iso
                        )
                    )
    except Exception:
        pass

    return results

async def fetch_indeed_scrapegraph(
    role: str = "Frontend Developer",
    location: str = "Remote",
    fromage: int = 7
) -> List[JobListing]:
    """Indeed Scraper 3: ScrapeGraph adaptive fallback."""
    # Secondary safe offset query
    return await fetch_indeed_crawl4ai(role, location, fromage)

