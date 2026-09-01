import httpx
import asyncio
from bs4 import BeautifulSoup
from typing import List
import urllib.parse
import re
from datetime import datetime, timezone
from ..base import JobListing

def map_exp_filter(exp: str) -> str:
    exp_clean = exp.lower()
    if "0-1" in exp_clean or "fresher" in exp_clean:
        return "1,2"
    if "0-2" in exp_clean:
        return "1,2,3"
    if "2-5" in exp_clean:
        return "3,4"
    if "5-10" in exp_clean or "5+" in exp_clean:
        return "5,6"
    return ""

async def fetch_scrapling_page(
    client: httpx.AsyncClient,
    role: str,
    location: str,
    f_e: str,
    f_tpr: str = "r604800",
    start: int = 0
) -> List[JobListing]:
    """Scrapling fast anti-bot bulk fetcher for LinkedIn."""
    encoded_role = urllib.parse.quote_plus(role or "Frontend Developer")
    encoded_loc = urllib.parse.quote_plus(location or "Remote")
    now_iso = datetime.now(timezone.utc).isoformat()
    
    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={encoded_role}&location={encoded_loc}&start={start}&f_TPR={f_tpr}"
    if f_e:
        url += f"&f_E={f_e}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.linkedin.com/jobs/search",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    results: List[JobListing] = []
    try:
        response = await client.get(url, headers=headers, timeout=10.0)
        if response.status_code != 200:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        job_cards = soup.find_all("li")

        for card in job_cards:
            title_tag = card.find("h3", class_=re.compile("base-search-card__title|job-title"))
            company_tag = card.find("h4", class_=re.compile("base-search-card__subtitle"))
            location_tag = card.find("span", class_=re.compile("job-search-card__location"))
            time_tag = card.find("time")
            link_tag = card.find("a", class_=re.compile("base-card__full-link|job-link")) or card.find("a", href=True)

            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            company = company_tag.get_text(strip=True) if company_tag else "Technology Enterprise"
            job_loc = location_tag.get_text(strip=True) if location_tag else location
            date_str = time_tag.get_text(strip=True) if time_tag else "Recently"
            raw_dt = time_tag.get("datetime") if time_tag else None
            
            raw_href = link_tag["href"] if link_tag and link_tag.has_attr("href") else ""
            job_id_match = re.search(r'view/(\d+)', raw_href) or re.search(r'jobPosting:(\d+)', str(card))
            
            if job_id_match:
                job_id = job_id_match.group(1)
                apply_url = f"https://www.linkedin.com/jobs/view/{job_id}"
            elif raw_href.startswith("http"):
                apply_url = raw_href.split("?")[0]
                job_id = apply_url.split("-")[-1]
            else:
                job_id = f"{abs(hash(title + company))}"
                apply_url = f"https://www.linkedin.com/jobs/search/?keywords={encoded_role}&location={encoded_loc}"

            is_job_remote = "remote" in job_loc.lower() or "remote" in title.lower()

            results.append(
                JobListing(
                    id=f"li_scrapling_{job_id}",
                    title=title,
                    company=company,
                    location=job_loc,
                    experience="Entry / Mid",
                    apply_link=apply_url,
                    posted_date=date_str,
                    source="LinkedIn",
                    is_remote=is_job_remote,
                    tags=["Scrapling Stealth"],
                    fetched_at=now_iso,
                    posted_datetime=raw_dt
                )
            )
    except Exception:
        pass

    return results

async def fetch_linkedin_scrapling(
    role: str = "Frontend Developer",
    location: str = "Remote",
    exp: str = "0-2",
    is_remote: bool = False,
    f_tpr: str = "r604800"
) -> List[JobListing]:
    """Scraper 1: Scrapling LinkedIn Engine (Primary)."""
    f_e = map_exp_filter(exp)
    search_loc = "Remote" if is_remote else (location or "Remote")
    offsets = [0, 25, 50, 75, 100, 125, 150]

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=40)
    async with httpx.AsyncClient(limits=limits, follow_redirects=True) as client:
        tasks = [
            fetch_scrapling_page(client, role, search_loc, f_e, f_tpr, start=offset)
            for offset in offsets
        ]
        pages_results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[JobListing] = []
    seen = set()
    for page in pages_results:
        if isinstance(page, list):
            for j in page:
                if j.id not in seen:
                    seen.add(j.id)
                    all_jobs.append(j)

    return all_jobs

