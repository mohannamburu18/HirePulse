from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import time
import asyncio
from datetime import datetime, timezone

from parser import parse_resume_content
from intent_builder import PreferenceInput, GeneratedIntentResponse, build_search_intents
from core.orchestrator import (
    fetch_all_jobs_realtime,
    merge_3_scrapers_linkedin,
    merge_3_scrapers_indeed,
    merge_3_scrapers_naukri
)
from db import save_user_profile, get_latest_profile
from scheduler import calculate_new_jobs_count
from fetchers.ats.lever import fetch_lever_jobs
from fetchers.ats.greenhouse import fetch_greenhouse_jobs
from fetchers.ats.ashby import fetch_ashby_jobs
from fetchers.ats.workday import fetch_workday_jobs
from fetchers.boards.linkedin_scrapling import fetch_linkedin_scrapling
from fetchers.boards.linkedin_crawl4ai import fetch_linkedin_crawl4ai
from fetchers.boards.linkedin_scrapegraph import fetch_linkedin_scrapegraph
from fetchers.boards.indeed_scrapling import fetch_indeed_scrapling
from fetchers.boards.naukri_scrapling import fetch_naukri_scrapling

app = FastAPI(
    title="HirePulse API",
    description="Resume-aware universal job engine backend API - 100% Live Real-Time Aggregator",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for active user profile & preferences
active_user_profile: Dict[str, Any] = {
    "name": "Candidate",
    "email": None,
    "phone": None,
    "location": "Bangalore",
    "total_experience_years": 1.0,
    "skills": ["React", "TypeScript", "Node.js", "Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "Tailwind CSS"],
    "categorized_skills": {},
    "work_history": [],
    "education": [],
    "completeness_score": 95
}

active_user_preferences: Dict[str, Any] = {
    "target_roles": ["Frontend Developer", "Software Engineer"],
    "locations": ["Bangalore", "Remote"],
    "is_remote_only": False,
    "experience_bracket": "fresher",
    "job_types": ["Full-time"],
    "generated_intents": []
}

class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    total_experience_years: Optional[float] = None
    skills: Optional[List[str]] = None
    work_history: Optional[List[Dict[str, Any]]] = None

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "HirePulse Universal Job Engine API",
        "version": "1.0.0",
        "realtime": True,
        "sources": ["Lever", "Greenhouse", "Ashby", "Workday", "LinkedIn", "Indeed", "Naukri"]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/api/debug/live")
async def debug_live_fetchers(
    role: str = Query(default="Frontend Developer"),
    location: str = Query(default="Bangalore")
):
    """Debug endpoint verifying all 7 live sources concurrently without seed data."""
    t0 = time.time()
    now_iso = datetime.now(timezone.utc).isoformat()
    
    tasks = [
        fetch_lever_jobs(role, location),
        fetch_greenhouse_jobs(role, location),
        fetch_ashby_jobs(role, location),
        fetch_workday_jobs(role, location),
        fetch_linkedin_scrapling(role, location),
        fetch_linkedin_crawl4ai(role, location),
        fetch_linkedin_scrapegraph(role, location),
        fetch_indeed_scrapling(role, location),
        fetch_naukri_scrapling(role, location)
    ]
    
    res = await asyncio.gather(*tasks, return_exceptions=True)
    
    lever_jobs = res[0] if isinstance(res[0], list) else []
    gh_jobs = res[1] if isinstance(res[1], list) else []
    ashby_jobs = res[2] if isinstance(res[2], list) else []
    wd_jobs = res[3] if isinstance(res[3], list) else []
    
    li_scrapling = res[4] if isinstance(res[4], list) else []
    li_crawl4ai = res[5] if isinstance(res[5], list) else []
    li_scrapegraph = res[6] if isinstance(res[6], list) else []
    
    ind_jobs = res[7] if isinstance(res[7], list) else []
    nk_jobs = res[8] if isinstance(res[8], list) else []

    return {
        "status": "success",
        "is_realtime": True,
        "fetched_at": now_iso,
        "elapsed_seconds": round(time.time() - t0, 2),
        "counts": {
            "lever": len(lever_jobs),
            "greenhouse": len(gh_jobs),
            "ashby": len(ashby_jobs),
            "workday": len(wd_jobs),
            "linkedin_scrapling": len(li_scrapling),
            "linkedin_crawl4ai": len(li_crawl4ai),
            "linkedin_scrapegraph": len(li_scrapegraph),
            "linkedin_total": len(li_scrapling) + len(li_crawl4ai) + len(li_scrapegraph),
            "indeed": len(ind_jobs),
            "naukri": len(nk_jobs),
            "total_raw_live": len(lever_jobs) + len(gh_jobs) + len(ashby_jobs) + len(wd_jobs) + len(li_scrapling) + len(li_crawl4ai) + len(li_scrapegraph) + len(ind_jobs) + len(nk_jobs)
        },
        "samples": {
            "lever": lever_jobs[0].model_dump() if lever_jobs else None,
            "greenhouse": gh_jobs[0].model_dump() if gh_jobs else None,
            "ashby": ashby_jobs[0].model_dump() if ashby_jobs else None,
            "workday": wd_jobs[0].model_dump() if wd_jobs else None,
            "linkedin": li_scrapling[0].model_dump() if li_scrapling else None,
            "indeed": ind_jobs[0].model_dump() if ind_jobs else None,
            "naukri": nk_jobs[0].model_dump() if nk_jobs else None
        }
    }

@app.post("/api/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    filename = file.filename or "resume.pdf"
    ext = os.path.splitext(filename)[1].lower()
    
    if ext not in [".pdf", ".docx", ".doc", ".txt"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload a PDF or DOCX file."
        )

    file_bytes = await file.read()
    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds maximum limit of 5MB."
        )

    try:
        parsed_result = parse_resume_content(file_bytes, filename)
        global active_user_profile
        active_user_profile = parsed_result.copy()
        
        try:
            save_user_profile(
                profile_id="user_active",
                name=parsed_result.get("name", "Candidate"),
                email=parsed_result.get("email"),
                skills=parsed_result.get("skills", []),
                experience_years=float(parsed_result.get("total_experience_years", 1.0)),
                desired_role="Frontend Developer",
                location=parsed_result.get("location", "Bangalore"),
                is_remote=False
            )
        except Exception:
            pass

        return parsed_result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse resume: {str(e)}"
        )

@app.get("/api/profile")
def get_profile():
    return active_user_profile

@app.post("/api/profile")
def update_profile(profile_data: ProfileUpdateRequest):
    global active_user_profile
    data = profile_data.model_dump(exclude_unset=True)
    active_user_profile.update(data)
    
    try:
        save_user_profile(
            profile_id="user_active",
            name=active_user_profile.get("name", "Candidate"),
            email=active_user_profile.get("email"),
            skills=active_user_profile.get("skills", []),
            experience_years=float(active_user_profile.get("total_experience_years", 1.0)),
            desired_role=active_user_preferences.get("target_roles", ["Frontend Developer"])[0],
            location=active_user_profile.get("location", "Bangalore"),
            is_remote=active_user_preferences.get("is_remote_only", False)
        )
    except Exception:
        pass

    return {
        "status": "success",
        "message": "User profile updated successfully",
        "profile": active_user_profile
    }

@app.post("/api/generate-intents", response_model=GeneratedIntentResponse)
def generate_intents(prefs: PreferenceInput):
    global active_user_preferences, active_user_profile

    if not prefs.candidate_skills and active_user_profile.get("skills"):
        prefs.candidate_skills = active_user_profile.get("skills")
    if not prefs.candidate_location and active_user_profile.get("location"):
        prefs.candidate_location = active_user_profile.get("location")
    if prefs.candidate_years is None and active_user_profile.get("total_experience_years"):
        prefs.candidate_years = active_user_profile.get("total_experience_years")

    response = build_search_intents(prefs)
    active_user_preferences = {
        "target_roles": prefs.target_roles,
        "locations": prefs.locations,
        "is_remote_only": prefs.is_remote_only,
        "experience_bracket": prefs.experience_bracket,
        "job_types": prefs.job_types,
        "generated_intents": [intent.model_dump() for intent in response.intents]
    }

    return response

@app.get("/api/preferences")
def get_preferences():
    return active_user_preferences

@app.get("/api/new-jobs-count")
def get_new_jobs_count(profile_id: Optional[str] = None):
    return calculate_new_jobs_count(profile_id)

@app.get("/api/user-profile/latest")
def get_latest_db_profile():
    p = get_latest_profile()
    if p:
        return {"status": "found", "profile": p}
    return {"status": "empty", "profile": active_user_profile}

@app.get("/api/jobs")
async def get_jobs(
    role: str = Query(default="Frontend Developer", description="Target role (e.g. Frontend Developer, Backend Developer, Software Engineer)"),
    location: str = Query(default="Bangalore", description="Target location (e.g. Bangalore, Remote, India)"),
    exp: str = Query(default="fresher", description="Experience tier: fresher, 0-1, 0-2, 2-5, 5+"),
    is_remote: bool = Query(default=False, description="Remote only toggle"),
    limit: int = Query(default=500, description="Max jobs to return")
):
    """
    Live real-time aggregation across all 7 sources concurrently.
    Zero seed data, 100% real apply links, sorted by match score high to low.
    """
    global active_user_profile, active_user_preferences

    try:
        candidate_skills = active_user_profile.get("skills") or ["React", "TypeScript", "Node.js", "Python", "FastAPI"]
        candidate_years = float(active_user_profile.get("total_experience_years") or 1.0)
        candidate_bracket = exp or active_user_preferences.get("experience_bracket") or "fresher"

        result = await fetch_all_jobs_realtime(
            role=role,
            location=location,
            exp=candidate_bracket,
            is_remote=is_remote,
            candidate_skills=candidate_skills,
            candidate_years=candidate_years,
            limit=limit
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Live job aggregation failed: {str(e)}"
        )
