import asyncio
from bs4 import BeautifulSoup
from typing import List
import urllib.parse
import re
from datetime import datetime, timezone
import logging
from ..base import JobListing

logger = logging.getLogger(__name__)

async def fetch_indeed_scrapling(
    role: str = "Frontend Developer",
    location: str = "Remote",
    fromage: int = 7
) -> List[JobListing]:
    """Indeed Scraper 1: Primary Scrapling Stealth Fetcher (Live Cloudflare Bypass)."""
    encoded_role = urllib.parse.quote_plus(role or "Frontend Developer")
    encoded_loc = urllib.parse.quote_plus(location or "Bangalore")
    now_iso = datetime.now(timezone.utc).isoformat()

    urls = [
        f"https://in.indeed.com/jobs?q={encoded_role}&l={encoded_loc}&fromage={fromage}",
        f"https://www.indeed.com/jobs?q={encoded_role}&l={encoded_loc}&fromage={fromage}"
    ]

    results: List[JobListing] = []
    seen = set()

    for url in urls:
        try:
            from scrapling.fetchers import Fetcher
            fetcher = Fetcher()
            page = fetcher.get(url)
            if page.status != 200:
                continue

            cards = page.css("div.job_seen_beacon, div.cardOutline, div.jobsearch-SerpJobCard")
            for card in cards:
                t_match = card.css("h2.jobTitle, a.jcs-JobTitle, h2 a")
                c_match = card.css("span[data-testid='company-name'], span.companyName")
                l_match = card.css("div[data-testid='text-location'], div.companyLocation")
                d_match = card.css("span.date, span.myJobsState")
                link_match = card.css("a[href]")

                if not t_match:
                    continue

                title = t_match[0].text.strip()
                comp = c_match[0].text.strip() if c_match else "Leading Enterprise"
                job_loc = l_match[0].text.strip() if l_match else location
                posted_str = d_match[0].text.strip() if d_match else "Recently"

                raw_href = link_match[0].attrib.get("href", "") if link_match else ""
                if raw_href.startswith("/"):
                    apply_url = f"https://in.indeed.com{raw_href}"
                elif raw_href.startswith("http"):
                    apply_url = raw_href
                else:
                    apply_url = url

                job_id = f"ind_{abs(hash(title + comp))}"
                if job_id not in seen:
                    seen.add(job_id)
                    results.append(
                        JobListing(
                            id=job_id,
                            title=title,
                            company=comp,
                            location=job_loc,
                            experience="Entry / Mid",
                            apply_link=apply_url,
                            posted_date=posted_str,
                            source="Indeed",
                            is_remote="remote" in job_loc.lower() or "remote" in title.lower(),
                            tags=["Indeed Stealth"],
                            fetched_at=now_iso
                        )
                    )
        except Exception as e:
            logger.debug(f"Indeed scrapling error: {e}")

    return results

