from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import re

OVERSEAS_ONLY_INDICATORS = [
    "san francisco", "new york", "seattle", "austin", "boston", "chicago",
    "los angeles", "denver", "atlanta", "london", "berlin", "dublin",
    "toronto", "vancouver", "sydney", "paris", "tokyo", "usa only", "us only",
    "united states", "canada only", "uk only", "us remote", "remote - us",
    "remote (us)", "remote - united states", "americas only", "emea only", "latam only"
]

INDIA_LOCATIONS = [
    "bangalore", "bengaluru", "india", "hyderabad", "pune", "mumbai",
    "gurgaon", "gurugram", "noida", "delhi", "ncr", "chennai", "kolkata",
    "karnataka", "remote - india", "india - remote"
]

class JobListing(BaseModel):
    id: str
    title: str
    company: str
    location: str
    experience: str = "Not Specified"
    apply_link: str
    posted_date: str = "Recently"
    source: str  # "Lever" | "Greenhouse" | "Ashby" | "Workday" | "LinkedIn" | "Indeed" | "Naukri"
    is_remote: bool = False
    salary_range: Optional[str] = None
    description_snippet: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    created_at_ms: Optional[int] = None
    posted_datetime: Optional[str] = None

def normalize_text(text: str) -> str:
    """Normalize text for case-insensitive matching."""
    return text.lower().strip() if text else ""

ROLE_SYNONYMS = {
    "frontend": ["frontend", "front end", "front-end", "react", "ui", "web", "javascript", "full stack", "fullstack", "software engineer", "developer"],
    "backend": ["backend", "back end", "back-end", "python", "node", "java", "golang", "go", "microservices", "software engineer", "developer", "full stack"],
    "full stack": ["full stack", "fullstack", "software engineer", "developer", "frontend", "backend", "web"],
    "software engineer": ["software", "developer", "engineer", "sde", "swe", "programmer", "tech"],
    "marketing": ["marketing", "growth", "seo", "sem", "content", "brand"],
    "sales": ["sales", "sdr", "bdr", "account executive", "business development"]
}

def is_role_match(job_title: str, query_role: str) -> bool:
    """Check if a job title matches the query role or its technical family."""
    if not query_role or query_role.lower() in ["any", "all", ""]:
        return True
        
    title_norm = normalize_text(job_title)
    query_norm = normalize_text(query_role)
    
    if query_norm in title_norm or title_norm in query_norm:
        return True
        
    for key, syns in ROLE_SYNONYMS.items():
        if key in query_norm:
            if any(s in title_norm for s in syns):
                return True

    query_words = [w for w in re.findall(r'\w+', query_norm) if len(w) > 2]
    if not query_words:
        return True
        
    match_count = sum(1 for w in query_words if w in title_norm)
    return (match_count / len(query_words)) >= 0.35

def is_location_match(job_location: str, query_location: str, is_remote_only: bool = False) -> bool:
    """
    Client-side location filter to ensure strict geographic relevance.
    Filters out US-only/overseas jobs when Bangalore, India, or Remote India is targeted.
    """
    if not job_location:
        return True

    jl = job_location.lower().strip()
    ul = (query_location or "").lower().strip()

    # 1. Check for explicit Remote-Only constraint
    if is_remote_only:
        if any(x in jl for x in ["usa only", "us only", "us remote", "remote (us)", "remote - us", "remote - united states", "americas only", "canada only", "uk only"]):
            return False
        return "remote" in jl or "anywhere" in jl or "worldwide" in jl or "global" in jl or "work from home" in jl

    # 2. Bangalore / Bengaluru targeted
    if "bangalore" in ul or "bengaluru" in ul:
        has_overseas = any(x in jl for x in OVERSEAS_ONLY_INDICATORS)
        has_india_or_blore = any(x in jl for x in ["bangalore", "bengaluru", "india", "karnataka"])
        
        if has_overseas and not has_india_or_blore:
            return False

        return any(x in jl for x in ["bangalore", "bengaluru", "india", "remote", "hybrid", "work from home", "karnataka", "anywhere", "worldwide"])

    # 3. India General targeted
    if "india" in ul:
        has_overseas = any(x in jl for x in OVERSEAS_ONLY_INDICATORS)
        has_india = any(x in jl for x in INDIA_LOCATIONS)
        if has_overseas and not has_india:
            return False
        return any(x in jl for x in INDIA_LOCATIONS + ["remote", "hybrid", "work from home", "anywhere", "worldwide"])

    # 4. Remote / Worldwide targeted
    if "remote" in ul:
        if any(x in jl for x in ["usa only", "us only", "us remote", "remote (us)", "remote - us", "remote - united states", "americas only", "canada only", "uk only"]):
            return False
        return "remote" in jl or "india" in jl or "anywhere" in jl or "bangalore" in jl or "worldwide" in jl or "global" in jl

    # 5. Fallback token match
    user_tokens = [t for t in re.findall(r'\w+', ul) if len(t) > 2]
    if not user_tokens or "worldwide" in ul or "any" in ul:
        return True
        
    for token in user_tokens:
        if token in jl:
            return True

    return True

def clean_location_string(job_location: str, default_location: str = "Bangalore, India") -> str:
    """Format and clean job location strings."""
    if not job_location:
        return default_location
    
    loc = job_location.strip()
    loc_lower = loc.lower()

    if "remote" in loc_lower:
        if "india" in loc_lower or "bangalore" in loc_lower or "bengaluru" in loc_lower:
            return "Remote - India"
        if "worldwide" in loc_lower or "global" in loc_lower or "anywhere" in loc_lower:
            return "Remote (Worldwide)"
        return "Remote"

    if "bangalore" in loc_lower or "bengaluru" in loc_lower:
        return "Bangalore, India"
    if "hyderabad" in loc_lower:
        return "Hyderabad, India"
    if "pune" in loc_lower:
        return "Pune, India"
    if "mumbai" in loc_lower:
        return "Mumbai, India"
    if "gurgaon" in loc_lower or "gurugram" in loc_lower or "noida" in loc_lower or "delhi" in loc_lower:
        return "Delhi NCR, India"
    if "chennai" in loc_lower:
        return "Chennai, India"
    if "india" in loc_lower:
        return "India"

    return loc
