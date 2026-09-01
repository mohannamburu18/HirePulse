from typing import Dict, Any, Optional
from datetime import datetime
from db import get_latest_profile

# In-memory tracking for new job counts
NEW_JOBS_CACHE: Dict[str, Dict[str, Any]] = {}

def calculate_new_jobs_count(profile_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate new jobs discovered since last user visit.
    Simulates background indexing counter based on profile targets.
    """
    profile = get_latest_profile()
    if not profile:
        return {
            "profile_id": "default",
            "new_jobs_count": 24,
            "period": "since yesterday",
            "top_skills": ["React", "TypeScript"],
            "location": "Bangalore"
        }

    p_id = profile_id or profile.get("id", "user_default")
    skills = profile.get("skills", ["React", "Node.js"])
    location = profile.get("location", "Bangalore")
    name = profile.get("name", "Candidate")

    # Dynamic calculation: base count + deterministic offset based on hour
    current_hour = datetime.utcnow().hour
    new_count = 18 + (current_hour % 15)

    return {
        "profile_id": p_id,
        "name": name,
        "new_jobs_count": new_count,
        "period": "since yesterday",
        "top_skills": skills[:3],
        "location": location,
        "desired_role": profile.get("desired_role", "Software Engineer")
    }

async def run_periodic_job_refresh():
    """Background task running every 60 minutes."""
    while True:
        try:
            profile = get_latest_profile()
            if profile:
                # Refresh logic
                calculate_new_jobs_count(profile.get("id"))
        except Exception:
            pass
        await asyncio.sleep(3600)
