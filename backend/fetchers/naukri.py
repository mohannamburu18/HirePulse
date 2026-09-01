import httpx
import asyncio
import urllib.parse
from typing import List
from .base import JobListing

async def fetch_naukri_jobs(
    role: str = "",
    location: str = "",
    exp: str = "",
    is_remote: bool = False
) -> List[JobListing]:
    """Fetch live jobs from Naukri public search API."""
    encoded_role = urllib.parse.quote_plus(role or "Software Engineer")
    encoded_loc = urllib.parse.quote_plus("Remote" if is_remote else (location or "Bangalore"))

    url = f"https://www.naukri.com/jobapi/v3/search?noOfResults=50&urlType=search_by_keyword&searchType=adv&keyword={encoded_role}&location={encoded_loc}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "appid": "109",
        "systemid": "109",
        "clientid": "d3419729"
    }

    results: List[JobListing] = []
    try:
        async with httpx.AsyncClient(headers=headers, timeout=8.0, follow_redirects=True) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                job_details = data.get("jobDetails", [])
                for item in job_details:
                    title = item.get("title", "")
                    company = item.get("companyName", "Top Tech Enterprise")
                    job_id = str(item.get("jobId", ""))
                    jd_url = item.get("jdURL", "")
                    placeholders = item.get("placeholders", [])
                    
                    loc_name = location
                    exp_text = exp or "0-3 Yrs"
                    salary_text = None
                    
                    for p in placeholders:
                        p_type = p.get("type", "")
                        if p_type == "location":
                            loc_name = p.get("label", loc_name)
                        elif p_type == "experience":
                            exp_text = p.get("label", exp_text)
                        elif p_type == "salary":
                            salary_text = p.get("label")

                    if not jd_url.startswith("http"):
                        jd_url = f"https://www.naukri.com/job-listings-{job_id}"

                    tags = [t.get("label") for t in item.get("tagsAndSkills", []) if t.get("label")]

                    results.append(
                        JobListing(
                            id=f"naukri_{job_id}",
                            title=title,
                            company=company,
                            location=loc_name,
                            experience=exp_text,
                            apply_link=jd_url,
                            posted_date="Recently",
                            source="Naukri",
                            is_remote="remote" in loc_name.lower(),
                            salary_range=salary_text,
                            tags=tags[:3]
                        )
                    )
    except Exception:
        pass

    return results

