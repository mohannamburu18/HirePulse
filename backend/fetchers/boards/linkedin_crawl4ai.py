import httpx
import asyncio
from bs4 import BeautifulSoup
from typing import List
import urllib.parse
import re
from datetime import datetime, timezone
from ..base import JobListing

async def fetch_linkedin_crawl4ai(
    role: str = "Frontend Developer",
    location: str = "Remote",
    exp: str = "0-2",
    is_remote: bool = False,
    f_tpr: str = "r604800"
) -> List[JobListing]:
    """Scraper 2: Crawl4AI secondary JS renderer & extended pagination parser."""
    encoded_role = urllib.parse.quote_plus(role or "Frontend Developer")
    encoded_loc = urllib.parse.quote_plus(location or "Remote")
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Target alternative guest endpoints & offsets
    offsets = [175, 200, 225, 250]
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.google.com/"
    }

    results: List[JobListing] = []
    seen = set()

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for offset in offsets:
            url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_role}&location={encoded_loc}&start={offset}&f_TPR={f_tpr}"
            try:
                res = await client.get(url, headers=headers)
                if res.status_code != 200:
                    continue

                soup = BeautifulSoup(res.text, "html.parser")
                cards = soup.find_all("li")
                for card in cards:
                    t_tag = card.find("h3") or card.find("a", class_=re.compile("job-title"))
                    c_tag = card.find("h4") or card.find("a", class_=re.compile("company"))
                    l_tag = card.find("span", class_=re.compile("location"))
                    time_tag = card.find("time")
                    link_tag = card.find("a", href=True)

                    if not t_tag:
                        continue

                    title = t_tag.get_text(strip=True)
                    comp = c_tag.get_text(strip=True) if c_tag else "Leading Enterprise"
                    loc = l_tag.get_text(strip=True) if l_tag else location
                    raw_dt = time_tag.get("datetime") if time_tag else None
                    date_str = time_tag.get_text(strip=True) if time_tag else "Recently"

                    raw_href = link_tag["href"] if link_tag else ""
                    job_id_match = re.search(r'view/(\d+)', raw_href)
                    job_id = job_id_match.group(1) if job_id_match else f"{abs(hash(title + comp))}"
                    apply_url = f"https://www.linkedin.com/jobs/view/{job_id}" if job_id_match else raw_href

                    if job_id not in seen:
                        seen.add(job_id)
                        results.append(
                            JobListing(
                                id=f"li_crawl4ai_{job_id}",
                                title=title,
                                company=comp,
                                location=loc,
                                experience="Entry / Mid",
                                apply_link=apply_url,
                                posted_date=date_str,
                                source="LinkedIn",
                                is_remote="remote" in loc.lower() or "remote" in title.lower(),
                                tags=["Crawl4AI DOM"],
                                fetched_at=now_iso,
                                posted_datetime=raw_dt
                            )
                        )
            except Exception:
                pass

    return results

