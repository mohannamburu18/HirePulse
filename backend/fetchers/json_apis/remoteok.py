import aiohttp
import logging
import re
import html
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

REMOTEOK_API_URL = "https://remoteok.com/api"

async def fetch_remoteok_jobs(
    role: str = "Frontend Developer",
    location: Optional[str] = "Remote",
    exp_level: Optional[str] = "fresher"
) -> List[Dict[str, Any]]:
    """
    Fetch and parse remote jobs from RemoteOK public JSON API.
    
    Requirements:
    - Uses aiohttp with browser User-Agent
    - Skips index 0 metadata item
    - Matches role against position or description
    - For fresher filters, only includes jobs with 'junior' or 'entry' in title
    - Returns standardized job dicts: title, company, location, description, url, posted_date, source, raw
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9"
    }

    role_clean = (role or "").strip().lower()
    exp_clean = (exp_level or "").strip().lower()
    is_fresher_filter = exp_clean in ["fresher", "0", "0-1", "entry", "entry level", "new grad"]

    # Role tokens (e.g. ['frontend', 'developer'])
    role_tokens = [t for t in re.split(r"[\s\-_/]+", role_clean) if len(t) >= 3]

    matched_jobs: List[Dict[str, Any]] = []

    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(REMOTEOK_API_URL) as response:
                if response.status != 200:
                    logger.warning(f"RemoteOK API returned HTTP {response.status}")
                    return []

                data = await response.json(content_type=None)
                if not isinstance(data, list) or len(data) <= 1:
                    logger.info("RemoteOK API returned empty or invalid response format")
                    return []

                # Skip the first item which is legal / metadata notice
                job_postings = data[1:]

                for item in job_postings:
                    if not isinstance(item, dict):
                        continue

                    raw_title = item.get("position") or ""
                    title = html.unescape(raw_title).strip()
                    if not title:
                        continue

                    company = item.get("company") or "Remote Company"
                    job_location = item.get("location") or "Remote"
                    raw_description = item.get("description") or ""
                    clean_desc = html.unescape(raw_description)
                    tags = [str(t).lower() for t in item.get("tags", [])]

                    title_lower = title.lower()
                    desc_lower = clean_desc.lower()

                    # 1. Role Filter Check: role appears in position, tags, or description
                    role_matched = False
                    if not role_clean:
                        role_matched = True
                    elif role_clean in title_lower or role_clean in desc_lower:
                        role_matched = True
                    elif role_tokens and any(token in title_lower or token in tags or token in desc_lower for token in role_tokens):
                        role_matched = True

                    if not role_matched:
                        continue

                    # 2. Fresher Filter Check: only include jobs with 'junior' or 'entry' in title
                    if is_fresher_filter:
                        title_has_fresher = any(kw in title_lower for kw in ["junior", "entry", "intern", "associate", "trainee"])
                        if not title_has_fresher:
                            # Reject if experience is strictly fresher and no junior indicator in title
                            continue

                    # Direct apply URL
                    url = item.get("url") or ""
                    if not url.startswith("http") and item.get("id"):
                        url = f"https://remoteok.com/remote-jobs/{item.get('id')}"

                    posted_date = item.get("date") or "Recently"

                    job_record = {
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "description": clean_desc,
                        "url": url,
                        "posted_date": posted_date,
                        "source": "RemoteOK",
                        "raw": item
                    }
                    matched_jobs.append(job_record)

                logger.info(f"Successfully fetched {len(matched_jobs)} jobs from RemoteOK for role='{role}', exp='{exp_level}'")
                return matched_jobs

    except aiohttp.ClientError as e:
        logger.error(f"Network error while fetching RemoteOK jobs: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while processing RemoteOK jobs: {e}")
        return []

