import aiohttp
import logging
from typing import List, Dict, Any, Optional
from core.filters.experience_detector import get_experience_params

logger = logging.getLogger(__name__)

# NOTE: The Cutshort API endpoint below is a placeholder structure.
# Because Cutshort periodically updates its internal search microservice routes and CSRF tokens,
# users can inspect their active search API route via browser DevTools (Network tab -> Fetch/XHR -> search)
# and update this CUTSHORT_API_ENDPOINT accordingly.
CUTSHORT_API_ENDPOINT = "https://www.cutshort.io/api/job-search"

async def fetch_cutshort_jobs(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher"
) -> List[Dict[str, Any]]:
    """
    Fetch job openings from Cutshort (Indian product companies).
    
    Requirements:
    - Uses aiohttp with browser headers
    - Uses get_experience_params() for experience mapping
    - Parameters: q=role, location=location, experience=exp_value, limit=50
    - Parses response for jobs list
    - Extracts: title, company, location, description, url, posted_date, source="cutshort"
    - Graceful error handling and stage logging
    """
    exp_params = get_experience_params(exp_level)
    exp_value = exp_params.get("naukri_exp", 0)  # Numerical experience value (e.g. 0, 1, 3, 5)

    params = {
        "q": role or "Software Engineer",
        "location": location or "Bangalore",
        "experience": exp_value,
        "limit": 50
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://cutshort.io/"
    }

    logger.info(f"Querying Cutshort API at {CUTSHORT_API_ENDPOINT} for role='{role}', location='{location}', exp='{exp_level}'...")

    try:
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            async with session.get(CUTSHORT_API_ENDPOINT, params=params) as response:
                if response.status != 200:
                    logger.warning(
                        f"Cutshort endpoint {CUTSHORT_API_ENDPOINT} returned HTTP {response.status}. "
                        f"(Note: Please verify the active internal endpoint via DevTools -> Network tab)"
                    )
                    return []

                data = await response.json(content_type=None)
                if not data:
                    logger.info("Cutshort API returned empty response payload.")
                    return []

                # Extract list of jobs from payload
                raw_jobs: List[Dict[str, Any]] = []
                if isinstance(data, list):
                    raw_jobs = data
                elif isinstance(data, dict):
                    raw_jobs = data.get("jobs") or data.get("data") or data.get("results") or []

                parsed_jobs: List[Dict[str, Any]] = []
                for item in raw_jobs:
                    if not isinstance(item, dict):
                        continue

                    title = item.get("title") or item.get("jobTitle") or item.get("role") or role
                    company = item.get("company") or item.get("companyName") or item.get("company_name") or "Tech Enterprise"
                    job_location = item.get("location") or item.get("city") or location
                    description = item.get("description") or item.get("summary") or item.get("jobDescription") or ""
                    url = item.get("url") or item.get("applyUrl") or item.get("jobUrl") or f"https://cutshort.io/jobs?q={role}"
                    posted_date = item.get("posted_date") or item.get("createdAt") or item.get("date") or "Recently"

                    parsed_jobs.append({
                        "title": title,
                        "company": company,
                        "location": job_location,
                        "description": description,
                        "url": url,
                        "posted_date": posted_date,
                        "source": "cutshort",
                        "raw": item
                    })

                logger.info(f"Successfully processed {len(parsed_jobs)} jobs from Cutshort.")
                return parsed_jobs

    except aiohttp.ClientError as e:
        logger.warning(f"Network error accessing Cutshort API: {e}")
        return []
    except Exception as e:
        logger.error(f"Error parsing Cutshort jobs: {e}", exc_info=True)
        return []

