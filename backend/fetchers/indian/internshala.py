import asyncio
import logging
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

INTERNSHALA_BASE_URL = "https://internshala.com"
INTERNSHALA_FRESHER_URL = "https://internshala.com/fresher-jobs/{category}-jobs/page-{page}/"

def map_role_to_category(role: str) -> str:
    """Map user role to an Internshala fresher category slug."""
    r = (role or "").strip().lower()
    data_keywords = ["data", "analytics", "analyst", "machine learning", "ml", "ai", "scientist", "deep learning"]
    if any(kw in r for kw in data_keywords):
        return "data-science"
    return "software-development"

def check_location_match(job_loc: str, user_loc: str) -> bool:
    """Filter job location against target user location."""
    if not job_loc or not user_loc:
        return True

    jl = job_loc.lower().strip()
    ul = user_loc.lower().strip()

    if "remote" in ul or "work from home" in ul:
        return any(term in jl for term in ["remote", "work from home", "wfh", "anywhere"])

    bangalore_aliases = ["bangalore", "bengaluru", "blr"]
    if any(alias in ul for alias in bangalore_aliases):
        if any(alias in jl for alias in bangalore_aliases):
            return True
        if "remote" in jl or "work from home" in jl or "india" in jl:
            return True
        return False

    if "india" in ul:
        return True

    user_city = ul.split(",")[0].strip()
    if user_city in jl:
        return True

    if "remote" in jl or "work from home" in jl:
        return True

    return False

def _scrape_internshala_sync(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher",
    max_pages: int = 5
) -> List[Dict[str, Any]]:
    """
    Synchronous Internshala scraping implementation across up to 5 pages.
    """
    category = map_role_to_category(role)
    logger.info(f"Scraping Internshala category '{category}' for role '{role}', location '{location}' (up to {max_pages} pages)...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://internshala.com/fresher-jobs"
    }

    session = requests.Session()
    all_jobs: List[Dict[str, Any]] = []
    seen_urls = set()

    for page in range(1, max_pages + 1):
        url = INTERNSHALA_FRESHER_URL.format(category=category, page=page)
        logger.info(f"Internshala: Fetching page {page} from {url}")

        try:
            resp = session.get(url, headers=headers, timeout=12)
            if resp.status_code != 200:
                logger.warning(f"Internshala page {page} returned status {resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "html.parser")
            cards = soup.find_all(class_="individual_internship")

            if not cards:
                logger.info(f"Internshala page {page}: No more job cards found. Stopping pagination.")
                break

            for card in cards:
                # 1. Title & URL
                title_elem = (
                    card.find(class_="job-internship-name") or
                    card.find(class_="job-title-href") or
                    card.find("h3")
                )
                link_elem = card.find(class_="job-title-href") or card.find("a", href=True)

                if not title_elem or not link_elem:
                    continue

                title = title_elem.get_text(strip=True)
                raw_href = link_elem.get("href", "")
                if not raw_href:
                    continue
                apply_url = urllib.parse.urljoin(INTERNSHALA_BASE_URL, raw_href)

                if apply_url in seen_urls:
                    continue
                seen_urls.add(apply_url)

                # 2. Company
                comp_elem = (
                    card.find(class_="company-name") or
                    card.find(class_="heading_6") or
                    card.find(class_="company_name")
                )
                company = comp_elem.get_text(strip=True) if comp_elem else "Hiring Company"

                # 3. Location
                loc_elem = (
                    card.find(class_="location_link") or
                    card.find(class_="locations") or
                    card.find(class_="location_name")
                )
                job_loc = loc_elem.get_text(strip=True) if loc_elem else "India"

                # 4. CTC
                ctc_elem = (
                    card.find(class_="desktop") or
                    card.find(class_="salary") or
                    card.find(class_="stipend")
                )
                ctc = ctc_elem.get_text(strip=True) if ctc_elem else "Competitive"

                # Filter by location
                if not check_location_match(job_loc, location):
                    continue

                job_record = {
                    "title": title,
                    "company": company,
                    "location": job_loc,
                    "ctc": ctc,
                    "url": apply_url,
                    "posted_date": "Recently",
                    "source": "internshala",
                    "raw": {
                        "title": title,
                        "company": company,
                        "location": job_loc,
                        "ctc": ctc,
                        "page": page
                    }
                }
                all_jobs.append(job_record)

            logger.info(f"Internshala page {page}: Extracted {len(cards)} cards (Total matched: {len(all_jobs)})")

            # Rate limit delay between requests
            if page < max_pages:
                time.sleep(1.5)

        except requests.RequestException as e:
            logger.error(f"Internshala request error on page {page}: {e}")
            break
        except Exception as e:
            logger.error(f"Internshala parsing error on page {page}: {e}", exc_info=True)
            break

    logger.info(f"Internshala scraping complete. Total matched jobs: {len(all_jobs)}")
    return all_jobs

async def fetch_internshala_jobs(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher"
) -> List[Dict[str, Any]]:
    """
    Async wrapper for synchronous Internshala scraper using ThreadPoolExecutor.
    """
    loop = asyncio.get_running_loop()
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(
                executor,
                _scrape_internshala_sync,
                role,
                location,
                exp_level,
                3  # Scrapes first 3 pages by default for speed and fresh jobs
            )
    except Exception as e:
        logger.error(f"Error executing fetch_internshala_jobs in executor: {e}")
        return []

