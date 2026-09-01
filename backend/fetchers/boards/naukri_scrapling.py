import httpx
from bs4 import BeautifulSoup
from typing import List
import urllib.parse
import re
from datetime import datetime, timezone
import logging
from ..base import JobListing

logger = logging.getLogger(__name__)

async def fetch_naukri_scrapling(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp: str = "0-2"
) -> List[JobListing]:
    """Naukri Scraper 1: Scrapling / HTTP Stealth scraper."""
    clean_role = role.lower().replace(" ", "-")
    clean_loc = location.lower().replace(" ", "-")
    now_iso = datetime.now(timezone.utc).isoformat()

    url = f"https://www.naukri.com/{clean_role}-jobs-in-{clean_loc}?jobAge=7&experience=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    results: List[JobListing] = []
    seen = set()

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, "html.parser")
                articles = soup.find_all("article") or soup.find_all("div", class_=re.compile("jobtuple|srp-tuple|row"))

                for art in articles:
                    t_tag = art.find("a", class_=re.compile("title|job-title")) or art.find("a", title=True)
                    c_tag = art.find("a", class_=re.compile("comp-name|company")) or art.find("span", class_=re.compile("comp-name"))
                    l_tag = art.find("span", class_=re.compile("loc|location"))
                    
                    if not t_tag:
                        continue

                    title = t_tag.get_text(strip=True)
                    comp = c_tag.get_text(strip=True) if c_tag else "Indian IT Leader"
                    job_loc = l_tag.get_text(strip=True) if l_tag else location
                    apply_url = t_tag.get("href") or url

                    job_id = f"nk_{abs(hash(title + comp))}"
                    if job_id not in seen:
                        seen.add(job_id)
                        results.append(
                            JobListing(
                                id=job_id,
                                title=title,
                                company=comp,
                                location=job_loc,
                                experience="0-1 Yrs",
                                apply_link=apply_url,
                                posted_date="Recently",
                                source="Naukri",
                                is_remote="remote" in job_loc.lower(),
                                tags=["Naukri Live"],
                                fetched_at=now_iso
                            )
                        )
    except Exception as e:
        logger.debug(f"Naukri scrapling error: {e}")

    return results

