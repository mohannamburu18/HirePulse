import asyncio
import logging
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

INSTAHYRE_BASE_URL = "https://www.instahyre.com"

def map_role_to_instahyre_category(role: str) -> str:
    """Map user role to an Instahyre category slug."""
    r = (role or "").strip().lower()
    if any(kw in r for kw in ["data", "machine learning", "ml", "ai", "analyst"]):
        return "data-science"
    return "software-engineering"

def _scrape_instahyre_sync(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher"
) -> List[Dict[str, Any]]:
    """
    Synchronous scraper for Instahyre using Scrapling StealthyFetcher.
    
    Requirements:
    - Use Scrapling with StealthyFetcher (stealth=True, headless=True, adaptive=True)
    - URL: https://www.instahyre.com/{category}-jobs/
    - Categories: software-engineering (mapped from role)
    - Wait 3 seconds for dynamic content
    - Parse with BeautifulSoup
    - Find job cards: '.job-card' or '.job-item'
    - Extract: title (.job-title), company (.company-name), location (.location), experience (.experience), link (a)
    - Return job dicts with source: 'instahyre'
    - Handle Scrapling failures gracefully
    """
    category = map_role_to_instahyre_category(role)
    url = f"{INSTAHYRE_BASE_URL}/{category}-jobs/"
    logger.info(f"Instahyre: Fetching {url} with StealthyFetcher for role='{role}', location='{location}'...")

    matched_jobs: List[Dict[str, Any]] = []
    seen_urls = set()
    page_html = ""

    try:
        from scrapling.fetchers import StealthyFetcher
        fetcher = StealthyFetcher(headless=True)
        response = fetcher.fetch(url)

        # Wait 3 seconds for dynamic content to settle
        time.sleep(3)

        # Extract HTML payload from response body or content
        if hasattr(response, "body") and response.body:
            page_html = response.body.decode("utf-8", errors="ignore") if isinstance(response.body, bytes) else str(response.body)
        elif hasattr(response, "html_content") and response.html_content:
            page_html = response.html_content
        elif hasattr(response, "text") and response.text:
            page_html = response.text

        logger.info(f"Instahyre: Fetched HTML payload ({len(page_html)} characters).")

    except Exception as ex:
        logger.warning(f"Instahyre: StealthyFetcher encountered issue: {ex}. Attempting fallback fetcher...")
        try:
            from scrapling.fetchers import Fetcher
            fallback_fetcher = Fetcher()
            resp = fallback_fetcher.get(url)
            page_html = resp.text
        except Exception as fallback_ex:
            logger.error(f"Instahyre: Fallback fetcher also failed: {fallback_ex}")
            return []

    if not page_html:
        logger.warning("Instahyre: Received empty HTML payload.")
        return []

    try:
        soup = BeautifulSoup(page_html, "html.parser")

        # Select cards: .job-card or .job-item (with resilient fallbacks for employer rows)
        cards = soup.select(".job-card, .job-item, .employer-block, .employer-row, .opportunity-row, div[id^='job-']")
        if not cards:
            cards = soup.find_all("div", class_=lambda c: c and any(k in c for k in ["job-card", "job-item", "employer-row", "opportunity"]))

        logger.info(f"Instahyre: Found {len(cards)} candidate job cards")

        for card in cards:
            # 1. Title (.job-title)
            title_elem = (
                card.select_one(".job-title") or
                card.select_one(".designation") or
                card.select_one("h2") or
                card.select_one("h3") or
                card.select_one(".position")
            )
            title = title_elem.get_text(strip=True) if title_elem else ""

            # 2. Company (.company-name)
            comp_elem = (
                card.select_one(".company-name") or
                card.select_one(".employer-name") or
                card.select_one(".employer") or
                card.select_one(".company")
            )
            company = comp_elem.get_text(strip=True) if comp_elem else "Tech Startup"

            # 3. Location (.location)
            loc_elem = (
                card.select_one(".location") or
                card.select_one(".job-locations") or
                card.select_one(".city")
            )
            job_loc = loc_elem.get_text(strip=True) if loc_elem else "India"

            # 4. Experience (.experience)
            exp_elem = (
                card.select_one(".experience") or
                card.select_one(".exp") or
                card.select_one(".years")
            )
            job_exp = exp_elem.get_text(strip=True) if exp_elem else "0-2 Years"

            # 5. Link (a)
            link_elem = card.find("a", href=True)
            raw_href = link_elem.get("href", "") if link_elem else ""
            if raw_href.startswith("/"):
                apply_url = urllib.parse.urljoin(INSTAHYRE_BASE_URL, raw_href)
            elif raw_href.startswith("http"):
                apply_url = raw_href
            else:
                apply_url = url

            if apply_url in seen_urls:
                continue
            seen_urls.add(apply_url)

            # Skip cards with no title
            if not title:
                continue

            matched_jobs.append({
                "title": title,
                "company": company,
                "location": job_loc,
                "experience": job_exp,
                "url": apply_url,
                "posted_date": "Recently",
                "source": "instahyre",
                "raw": {
                    "title": title,
                    "company": company,
                    "location": job_loc,
                    "experience": job_exp
                }
            })

        logger.info(f"Instahyre: Successfully extracted {len(matched_jobs)} job postings.")
        return matched_jobs

    except Exception as e:
        logger.error(f"Error parsing Instahyre job cards: {e}", exc_info=True)
        return []

async def fetch_instahyre_jobs(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher"
) -> List[Dict[str, Any]]:
    """
    Async wrapper for Instahyre scraper using ThreadPoolExecutor.
    """
    loop = asyncio.get_running_loop()
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(
                executor,
                _scrape_instahyre_sync,
                role,
                location,
                exp_level
            )
    except Exception as e:
        logger.error(f"Error executing fetch_instahyre_jobs: {e}")
        return []

