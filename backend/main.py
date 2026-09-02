from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import time
import asyncio
import logging
from datetime import datetime, timezone

from parser import parse_resume_content
from intent_builder import PreferenceInput, GeneratedIntentResponse, build_search_intents
from core.orchestrator import (
    orchestrate,
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

# Configure standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("hirepulse.api")

app = FastAPI(
    title="HirePulse API",
    description="Resume-aware universal job engine backend API - 100% Live Real-Time Multi-Layer Aggregator",
    version="2.0.0"
)

# 1. CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Request Logging Middleware
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"--> [{request.method}] {request.url.path} from {client_ip}")

    try:
        response = await call_next(request)
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.info(f"<-- [{request.method}] {request.url.path} completed with HTTP {response.status_code} in {duration_ms}ms")
        return response
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(f"<-- [{request.method}] {request.url.path} FAILED in {duration_ms}ms: {exc}", exc_info=True)
        raise exc

# 3. Global Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception intercepted on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": "Internal Server Error during job engine processing",
            "detail": str(exc),
            "path": request.url.path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
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
        "version": "2.0.0",
        "realtime": True,
        "layers": [
            "Layer 1: JSON APIs (RemoteOK, Hacker News)",
            "Layer 2: Indian Tech Portals (Internshala, Cutshort, Instahyre)",
            "Layer 3: ATS Direct Endpoints (Lever, Greenhouse, Ashby, Workday)",
            "Layer 4: Enhanced Boards (LinkedIn, Indeed, Naukri with JobSpy)"
        ]
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "HirePulse Backend"
    }

@app.get("/api/debug/live")
async def debug_live_fetchers(
    role: str = Query(default="Frontend Developer"),
    location: str = Query(default="Bangalore")
):
    """Telemetry endpoint verifying all live sources concurrently without seed data."""
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
        }
    }

@app.post("/api/parse-resume")
async def parse_resume(file: UploadFile = File(...)):
    """Parse resume PDF/DOCX into structured skills and profile information."""
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
        logger.error(f"Failed to parse resume {filename}: {e}", exc_info=True)
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
    exp_level: Optional[str] = Query(default=None, description="Alternative alias for exp parameter"),
    is_remote: bool = Query(default=False, description="Remote only toggle"),
    limit: int = Query(default=500, description="Max jobs to return"),
    resume_skills: Optional[str] = Query(default=None, description="Comma-separated resume skills for ranking"),
    force_refresh: bool = Query(default=False, description="Bypass SQLite cache and force fresh scraping")
):
    """
    Live real-time aggregation across all 4 layers concurrently using the enhanced orchestrator:
    - Layer 1: JSON APIs (RemoteOK, Hacker News)
    - Layer 2: Indian Tech Portals (Internshala, Cutshort, Instahyre)
    - Layer 3: Direct ATS APIs (Lever, Greenhouse, Ashby, Workday with 130+ companies)
    - Layer 4: Enhanced Boards (LinkedIn, Indeed, Naukri with JobSpy)
    
    Zero seed data, 100% live apply links, client-side filtered, and ranked by resume match score.
    """
    global active_user_profile, active_user_preferences

    try:
        # Determine candidate skills for matching
        if resume_skills:
            candidate_skills = [s.strip() for s in resume_skills.split(",") if s.strip()]
        else:
            candidate_skills = active_user_profile.get("skills") or ["React", "TypeScript", "Node.js", "Python", "FastAPI"]

        candidate_years = float(active_user_profile.get("total_experience_years") or 1.0)
        candidate_bracket = exp_level or exp or active_user_preferences.get("experience_bracket") or "fresher"

        logger.info(
            f"API /api/jobs called: role='{role}', location='{location}', "
            f"exp='{candidate_bracket}', is_remote={is_remote}, limit={limit}"
        )

        result = await orchestrate(
            role=role,
            location=location,
            exp=candidate_bracket,
            is_remote=is_remote,
            candidate_skills=candidate_skills,
            candidate_years=candidate_years,
            limit=limit,
            force_refresh=force_refresh
        )

        return result
    except Exception as e:
        logger.error(f"Live job aggregation endpoint failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Live job aggregation failed: {str(e)}"
        )
