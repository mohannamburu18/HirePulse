import re
from typing import Dict, Any, Optional

def detect_experience_level(title: Optional[str], description: Optional[str] = "") -> str:
    """
    Detect experience level from job title and description.
    Priority order: Senior ("5+") -> Mid ("2-5") -> Fresher ("fresher") -> Default ("0-2").
    """
    if not title and not description:
        return "0-2"

    t = (title or "").lower()
    d = (description or "").lower()
    combined = f"{t} {d}"

    # 1. Check for Senior keywords (5+ years, senior, lead, manager, director, principal, architect, etc.)
    senior_title_patterns = [
        r"\bsenior\b", r"\bsr\b", r"\bsr\.", r"\blead\b", r"\bprincipal\b",
        r"\bstaff\b", r"\barchitect\b", r"\bmanager\b", r"\bdirector\b",
        r"\bhead of\b", r"\bvp\b", r"\btech lead\b", r"\bengineering lead\b"
    ]
    for pattern in senior_title_patterns:
        if re.search(pattern, t):
            return "5+"

    senior_exp_patterns = [
        r"\b(?:5\+|6\+|7\+|8\+|9\+|10\+)\s*(?:years?|yrs?|yoe)\b",
        r"\b(?:5|6|7|8|9|10)\s*(?:-|to)\s*(?:8|10|12|15)\s*(?:years?|yrs?|yoe)\b",
        r"\b(?:minimum|at least)\s*(?:5|6|7|8)\s*(?:years?|yrs?|yoe)\b",
        r"\b5\+\s*years\b", r"\b7\+\s*years\b", r"\b8\+\s*years\b", r"\b10\+\s*years\b"
    ]
    for pattern in senior_exp_patterns:
        if re.search(pattern, combined):
            return "5+"

    # 2. Check for Mid-Level keywords (2-5 years, 3+ years, mid, intermediate, etc.)
    mid_title_patterns = [
        r"\bmid\b", r"\bmid-level\b", r"\bmidlevel\b", r"\bintermediate\b",
        r"\bii\b", r"\b2\b", r"\blevel 2\b", r"\bsde 2\b", r"\bsde ii\b",
        r"\bengineer 2\b", r"\bdeveloper 2\b"
    ]
    for pattern in mid_title_patterns:
        if re.search(pattern, t):
            return "2-5"

    mid_exp_patterns = [
        r"\b(?:2|3|4)\s*(?:-|to)\s*(?:4|5)\s*(?:years?|yrs?|yoe)\b",
        r"\b(?:3\+|4\+)\s*(?:years?|yrs?|yoe)\b",
        r"\b(?:2\s*\+)\s*(?:years?|yrs?|yoe)\b",
        r"\b(?:minimum|at least)\s*(?:2|3|4)\s*(?:years?|yrs?|yoe)\b"
    ]
    for pattern in mid_exp_patterns:
        if re.search(pattern, combined):
            return "2-5"

    # 3. Check for Fresher keywords (fresher, entry level, 0-1 year, new grad, etc.)
    fresher_patterns = [
        r"\bfresher\b", r"\bfreshers\b", r"\bentry\s*level\b", r"\bentrylevel\b",
        r"\bnew\s*grad\b", r"\bnew\s*graduate\b", r"\bgraduate\b", r"\bintern\b",
        r"\binternship\b", r"\btrainee\b", r"\bjunior\b", r"\bjr\b", r"\bjr\.",
        r"\bassociate\b", r"\b0-1\s*(?:years?|yrs?|yoe)\b", r"\b0\s*(?:-|to)\s*1\s*(?:years?|yrs?|yoe)\b",
        r"\b0\s*(?:years?|yrs?|yoe)\b", r"\b0\+\s*(?:years?|yrs?|yoe)\b",
        r"\bno\s*experience\b", r"\bcollege\s*grad\b", r"\bcampus\b"
    ]
    for pattern in fresher_patterns:
        if re.search(pattern, combined):
            return "fresher"

    # 4. Conservative default
    return "0-2"


def role_match(title: Optional[str], user_role: Optional[str]) -> bool:
    """
    Check if a job title matches the user's target role using family keyword mappings.
    Accepts if both contain generic terms like 'developer' or 'engineer'.
    """
    if not title or not user_role:
        return False

    t = title.lower().strip()
    r = user_role.lower().strip()

    # Direct substring match
    if r in t or t in r:
        return True

    # Generic developer/engineer overlap fallback
    dev_eng_keywords = {"developer", "engineer", "programmer", "specialist"}
    title_has_dev_eng = any(kw in t for kw in dev_eng_keywords)
    role_has_dev_eng = any(kw in r for kw in dev_eng_keywords)

    # Keyword mappings for major tech categories
    role_mappings = {
        "frontend": [
            "frontend", "front-end", "front end", "react", "vue", "angular",
            "next.js", "nextjs", "ui", "web developer", "javascript", "typescript"
        ],
        "backend": [
            "backend", "back-end", "back end", "node", "python", "django",
            "fastapi", "flask", "java", "spring", "golang", "go", ".net",
            "c#", "ruby", "rails", "php", "laravel", "api"
        ],
        "fullstack": [
            "fullstack", "full-stack", "full stack", "mern", "mean",
            "web developer", "software developer", "software engineer"
        ],
        "data": [
            "data", "analyst", "analytics", "data engineer", "data scientist",
            "machine learning", "ml", "ai", "artificial intelligence", "deep learning",
            "nlp", "computer vision", "bi", "business intelligence", "sql"
        ],
        "devops": [
            "devops", "cloud", "aws", "azure", "gcp", "sre", "site reliability",
            "infrastructure", "platform", "kubernetes", "docker", "ci/cd",
            "sysadmin", "system administrator"
        ],
        "software": [
            "software", "sde", "swe", "software engineer", "software developer",
            "application developer", "app developer", "systems engineer"
        ]
    }

    # Determine which category user_role belongs to
    matched_categories = []
    for category, keywords in role_mappings.items():
        if any(kw in r for kw in keywords):
            matched_categories.append(category)

    # If user_role matched any category, verify if title contains keywords from that category
    if matched_categories:
        for category in matched_categories:
            if any(kw in t for kw in role_mappings[category]):
                return True

    # If both explicitly mention developer or engineer
    if title_has_dev_eng and role_has_dev_eng:
        # Prevent cross-discipline collision (e.g. data science vs frontend developer)
        if any(kw in r for kw in role_mappings["frontend"]) and any(kw in t for kw in ["devops", "data scientist", "data analyst"]):
            return False
        if any(kw in r for kw in role_mappings["backend"]) and any(kw in t for kw in ["graphic designer", "ui designer", "product designer"]):
            return False
        return True

    return False


def location_match(job_location: Optional[str], user_location: Optional[str]) -> bool:
    """
    Check if a job location matches the user's target location.
    - Check if user city appears in job location
    - Handle Bangalore/Bengaluru variations
    - Check for India in location
    - Reject empty or unknown locations
    """
    if not job_location or not user_location:
        return False

    jl = job_location.strip().lower()
    ul = user_location.strip().lower()

    # Reject empty or unknown locations
    invalid_locations = {"", "unknown", "n/a", "na", "null", "none", "unspecified", "any", "tbd"}
    if jl in invalid_locations or ul in invalid_locations:
        return False

    # Handle Bangalore / Bengaluru variations
    bangalore_aliases = {"bangalore", "bengaluru", "blr"}
    user_is_bangalore = any(alias in ul for alias in bangalore_aliases)
    job_has_bangalore = any(alias in jl for alias in bangalore_aliases)

    if user_is_bangalore:
        if job_has_bangalore:
            return True
        # Remote India or general India allowed for Bangalore search
        if ("remote" in jl or "hybrid" in jl or "work from home" in jl or "wfh" in jl) and ("india" in jl or "anywhere" in jl):
            # Ensure no US/overseas exclusivity
            overseas_exclusions = ["usa only", "us only", "san francisco", "new york", "london", "uk only"]
            if not any(exc in jl for exc in overseas_exclusions):
                return True
        return False

    # Check for direct user city match
    if ul in jl:
        return True

    # Check for India in location
    if "india" in ul:
        indian_tech_cities = [
            "india", "bangalore", "bengaluru", "hyderabad", "pune", "mumbai",
            "delhi", "noida", "gurgaon", "gurugram", "chennai", "kolkata",
            "ahmedabad", "remote"
        ]
        return any(city in jl for city in indian_tech_cities)

    # Check for Remote / Anywhere
    if "remote" in ul:
        remote_indicators = ["remote", "anywhere", "work from home", "wfh", "telecommute"]
        return any(ind in jl for ind in remote_indicators)

    # Fallback: check if job is remote
    if "remote" in jl:
        return True

    return False


def get_experience_params(exp_level: Optional[str]) -> Dict[str, Any]:
    """
    Return dictionary mapping user experience level to platform-specific parameters:
    - linkedin_f_e: LinkedIn experience level filter code (e.g. 1=Internship, 2=Entry level, 3=Associate, 4=Mid-Senior, 5=Director, 6=Executive)
    - naukri_exp: Naukri experience parameter integer
    - jobspy_exp: JobSpy experience level string ('internship', 'entry_level', 'mid_level', 'senior_level')
    - indeed_boolean: Indeed experience filter query term
    - workday_exp: Workday CXS experience tag
    """
    clean_exp = (exp_level or "fresher").strip().lower()

    if clean_exp in ["fresher", "0", "0-1", "entry", "entry level", "new grad", "intern"]:
        return {
            "exp_level": "fresher",
            "min_years": 0,
            "max_years": 1,
            "linkedin_f_e": "1,2",
            "naukri_exp": 0,
            "jobspy_exp": "entry_level",
            "indeed_boolean": "entry_level",
            "workday_exp": "Entry_Level"
        }
    elif clean_exp in ["0-2", "1-2", "junior"]:
        return {
            "exp_level": "0-2",
            "min_years": 0,
            "max_years": 2,
            "linkedin_f_e": "1,2,3",
            "naukri_exp": 1,
            "jobspy_exp": "entry_level",
            "indeed_boolean": "entry_level",
            "workday_exp": "Entry_Level"
        }
    elif clean_exp in ["2-5", "2-4", "3-5", "mid", "mid-level"]:
        return {
            "exp_level": "2-5",
            "min_years": 2,
            "max_years": 5,
            "linkedin_f_e": "3,4",
            "naukri_exp": 3,
            "jobspy_exp": "mid_level",
            "indeed_boolean": "mid_level",
            "workday_exp": "Mid_Senior_Level"
        }
    elif clean_exp in ["5+", "5-10", "senior", "lead", "sr"]:
        return {
            "exp_level": "5+",
            "min_years": 5,
            "max_years": 10,
            "linkedin_f_e": "4,5,6",
            "naukri_exp": 5,
            "jobspy_exp": "senior_level",
            "indeed_boolean": "senior_level",
            "workday_exp": "Director_Executive"
        }
    else:
        # Default conservative fallback
        return {
            "exp_level": "0-2",
            "min_years": 0,
            "max_years": 2,
            "linkedin_f_e": "1,2,3",
            "naukri_exp": 1,
            "jobspy_exp": "entry_level",
            "indeed_boolean": "entry_level",
            "workday_exp": "Entry_Level"
        }

