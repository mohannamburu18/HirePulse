import re
from typing import Optional

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

def location_match(job_location: str, user_location: str, is_remote_only: bool = False) -> bool:
    """
    Client-side location filter to ensure strict geographic relevance.
    Filters out US-only/overseas jobs when Bangalore, India, or Remote India is targeted.
    """
    if not job_location:
        return True

    jl = job_location.lower().strip()
    ul = (user_location or "").lower().strip()

    # 1. Check for explicit Remote-Only constraint
    if is_remote_only:
        # Reject if explicit US/UK/Canada only remote
        if any(x in jl for x in ["usa only", "us only", "us remote", "remote (us)", "remote - us", "remote - united states", "americas only", "canada only", "uk only"]):
            return False
        return "remote" in jl or "anywhere" in jl or "worldwide" in jl or "global" in jl or "work from home" in jl

    # 2. Bangalore / Bengaluru targeted
    if "bangalore" in ul or "bengaluru" in ul:
        # Check if job contains overseas location without India / Bangalore
        has_overseas = any(x in jl for x in OVERSEAS_ONLY_INDICATORS)
        has_india_or_blore = any(x in jl for x in ["bangalore", "bengaluru", "india", "karnataka"])
        
        if has_overseas and not has_india_or_blore:
            return False

        # Must have Bangalore, Bengaluru, India, Remote, Hybrid, or Work from Home
        return any(x in jl for x in ["bangalore", "bengaluru", "india", "remote", "hybrid", "work from home", "karnataka", "anywhere", "worldwide"])

    # 3. India General targeted
    if "india" in ul:
        has_overseas = any(x in jl for x in OVERSEAS_ONLY_INDICATORS)
        has_india = any(x in jl for x in INDIA_LOCATIONS)
        if has_overseas and not has_india:
            return False
        return any(x in jl for x in INDIA_LOCATIONS + ["remote", "hybrid", "work from home", "anywhere", "worldwide"])

    # 4. Remote / Worldwide targeted
    if "remote" in ul or "worldwide" in ul or "any" in ul or not ul:
        if any(x in jl for x in ["usa only", "us only", "us remote", "remote (us)", "remote - us", "remote - united states", "americas only", "canada only", "uk only"]):
            return False
        return "remote" in jl or "anywhere" in jl or "worldwide" in jl or "global" in jl or "india" in jl or "bangalore" in jl or True

    # 5. US / Specific Country targeted
    user_tokens = [t for t in re.findall(r'\w+', ul) if len(t) > 2]
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

