from core.orchestrator import fetch_all_jobs_realtime, merge_3_scrapers_linkedin, merge_3_scrapers_indeed, merge_3_scrapers_naukri

async def orchestrate_job_search(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp: str = "fresher",
    is_remote: bool = False,
    posted: str = "week",
    source: str = None,
    limit: int = 600,
    candidate_skills = None,
    candidate_years: float = 1.0
):
    return await fetch_all_jobs_realtime(
        role=role,
        location=location,
        exp=exp,
        is_remote=is_remote,
        candidate_skills=candidate_skills,
        candidate_years=candidate_years,
        limit=limit
    )

__all__ = ["orchestrate_job_search", "fetch_all_jobs_realtime", "merge_3_scrapers_linkedin", "merge_3_scrapers_indeed", "merge_3_scrapers_naukri"]
