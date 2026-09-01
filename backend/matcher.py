import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from fetchers.base import JobListing, normalize_text

# Common skills dictionary for extraction from job text
POPULAR_TECH_SKILLS = [
    "react", "typescript", "javascript", "python", "fastapi", "django", "node.js", "nodejs",
    "go", "golang", "java", "spring boot", "c++", "c#", ".net", "docker", "kubernetes",
    "aws", "gcp", "azure", "graphql", "rest api", "postgresql", "postgres", "mongodb",
    "redis", "elasticsearch", "ci/cd", "git", "microservices", "system design",
    "machine learning", "pytorch", "tensorflow", "llms", "nlp", "terraform", "linux",
    "tailwind css", "tailwind", "html5", "css3", "redux", "vue.js", "angular", "sql",
    "seo", "sem", "google analytics", "hubspot", "copywriting", "salesforce", "crm",
    "patient care", "hipaa", "emr", "ehr", "financial modeling", "dcf", "gaap", "excel"
]

SENIOR_EXPERIENCE_KEYWORDS = [
    "senior", "sr.", "sr ", "lead", "principal", "staff", "manager", "head of", "director",
    "vp", "architect", "sde 3", "sde-3", "sde iii", "sde-iii", "sde 2", "sde-2", "sde ii",
    "sde-ii", "level 3", "level 2", "3+", "4+", "5+", "6+", "7+", "8+", "10+", "3-5",
    "5-10", "5-8", "4-7", "2-5 years", "3 to 5", "5 to 10", "8 to 10", "experienced"
]

FRESHER_FRIENDLY_KEYWORDS = [
    "fresher", "intern", "internship", "graduate", "trainee", "associate", "entry",
    "junior", "jr.", "jr ", "0-1", "0-2", "sde 1", "sde-1", "sde i", "sde-i", "level 1",
    "0 years", "no experience", "campus", "college", "new grad"
]

def calculate_role_similarity(desired_role: str, job_title: str) -> float:
    """Calculate text similarity between candidate's desired role and job title (0.0 to 1.0)."""
    if not desired_role or desired_role.lower() in ["any", "all"]:
        return 1.0

    d_norm = normalize_text(desired_role)
    j_norm = normalize_text(job_title)

    if d_norm == j_norm or d_norm in j_norm:
        return 1.0

    # Tech family synonyms
    tech_keywords = ["frontend", "front end", "react", "ui", "web", "full stack", "fullstack", "software", "developer", "engineer", "backend", "programmer", "sde", "swe"]
    is_d_tech = any(k in d_norm for k in tech_keywords)
    is_j_tech = any(k in j_norm for k in tech_keywords)

    if is_d_tech and is_j_tech:
        # Check if direct frontend/react match
        if ("frontend" in d_norm or "react" in d_norm or "ui" in d_norm) and ("frontend" in j_norm or "react" in j_norm or "ui" in j_norm or "web" in j_norm):
            return 1.0
        return 0.75

    d_tokens = set(re.findall(r'\w+', d_norm))
    j_tokens = set(re.findall(r'\w+', j_norm))

    if not d_tokens or not j_tokens:
        return 0.5

    overlap = d_tokens.intersection(j_tokens)
    similarity = len(overlap) / len(d_tokens)
    return max(0.1, min(1.0, similarity))

def extract_job_skills(job: Dict[str, Any]) -> List[str]:
    """Extract required skills mentioned in job title, tags, and description."""
    text = (job.get("title", "") + " " + " ".join(job.get("tags", []) or []) + " " + (job.get("description_snippet", "") or "")).lower()
    found = []
    for skill in POPULAR_TECH_SKILLS:
        pattern = r'(?:\b|_)' + re.escape(skill) + r'(?:\b|_)'
        if re.search(pattern, text):
            clean_skill = skill.title()
            if skill in ["fastapi", "node.js", "nodejs", "postgresql", "postgres", "aws", "gcp", "ci/cd", "sql", "seo", "sem", "crm", "hipaa", "emr", "ehr", "dcf", "gaap"]:
                clean_skill = {
                    "fastapi": "FastAPI", "node.js": "Node.js", "nodejs": "Node.js",
                    "postgresql": "PostgreSQL", "postgres": "PostgreSQL", "aws": "AWS",
                    "gcp": "GCP", "ci/cd": "CI/CD", "sql": "SQL", "seo": "SEO",
                    "sem": "SEM", "crm": "CRM", "hipaa": "HIPAA", "emr": "EMR",
                    "ehr": "EHR", "dcf": "DCF", "gaap": "GAAP"
                }.get(skill, clean_skill)
            if clean_skill not in found:
                found.append(clean_skill)
    return found

def is_strict_experience_match(
    candidate_bracket: str,
    candidate_years: float,
    job_title: str,
    job_exp: str,
    description: str = ""
) -> bool:
    """
    Step 1: Strict Boolean Rejection Pre-Filter.
    Returns True if job is compatible with candidate's experience tier, False to REJECT immediately.
    """
    title_lower = job_title.lower()
    exp_lower = job_exp.lower()
    desc_lower = description.lower()
    full_text = f"{title_lower} {exp_lower} {desc_lower}"
    bracket_lower = candidate_bracket.lower().strip()

    is_fresher_req = bracket_lower in ["fresher", "0-1", "0-1 year", "0-1 yr"] or candidate_years <= 1.0
    is_entry_req = bracket_lower in ["0-2", "0-2 years", "0-2 yrs"]
    is_mid_req = bracket_lower in ["2-5", "2-5 years", "2-5 yrs"]
    is_senior_req = bracket_lower in ["5-10", "5+", "10+", "5-10 years", "10+ years"] or candidate_years >= 5.0

    # 1. Strict Filter for Fresher / 0-1 Year
    if is_fresher_req:
        # Reject ANY senior/lead/manager/staff/principal title
        if any(k in title_lower for k in ["senior", "sr.", "sr ", "lead", "principal", "staff", "manager", "head of", "director", "vp", "architect", "sde 3", "sde iii", "sde 2", "sde ii", "iii", "ii", "level 3", "level 2"]):
            return False
        # Reject if explicit experienced years are required in title/exp
        if any(k in full_text for k in ["3+", "4+", "5+", "6+", "7+", "8+", "10+", "3-5", "5-10", "5-8", "4-7", "2-5 years", "3 to 5", "5 to 10"]):
            return False
        # Allow if junior/intern/associate/fresher OR general entry developer title
        return True

    # 2. Strict Filter for 0-2 Years
    if is_entry_req:
        if any(k in title_lower for k in ["principal", "staff", "head of", "director", "vp", "architect", "sde 3", "sde iii"]):
            return False
        if any(k in full_text for k in ["5+", "6+", "7+", "8+", "10+", "5-10", "5-8"]):
            return False
        return True

    # 3. Strict Filter for 2-5 Years
    if is_mid_req:
        if any(k in title_lower for k in ["principal", "staff", "head of", "director", "vp", "vp ", "intern", "internship", "trainee"]):
            return False
        if any(k in full_text for k in ["8+", "10+", "10-15"]):
            return False
        return True

    # 4. Strict Filter for 5+ / 5-10 Years
    if is_senior_req:
        if any(k in title_lower for k in ["intern", "internship", "trainee", "fresher", "junior", "jr.", "graduate", "sde 1", "sde i"]):
            return False
        return True

    return True

def match_and_rank_jobs(
    jobs: List[Dict[str, Any]],
    candidate_skills: List[str],
    candidate_years: float,
    candidate_bracket: str,
    desired_role: str,
    target_location: str,
    is_remote_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Step 1: Strict Pre-filtering (REJECT mismatches).
    Step 2: Score qualified jobs (Skills 50%, Experience 30%, Role 20%).
    Step 3: Fresher Boost & Metadata Enrichment.
    """
    matched_results = []
    candidate_skills_norm = {s.lower(): s for s in candidate_skills}

    d_norm = normalize_text(desired_role)
    is_tech_role = any(k in d_norm for k in ["software", "developer", "engineer", "full stack", "frontend", "backend", "devops", "cloud", "data"])
    is_marketing_role = any(k in d_norm for k in ["marketing", "growth", "seo", "content"])
    is_sales_role = any(k in d_norm for k in ["sales", "sdr", "account executive", "b2b"])
    is_health_role = any(k in d_norm for k in ["nurse", "clinical", "doctor", "health"])

    is_user_fresher = candidate_bracket.lower() in ["fresher", "0-1", "0-1 year", "0-1 yr"] or candidate_years <= 1.0

    for job in jobs:
        title = job.get("title", "")
        title_norm = normalize_text(title)
        title_lower = title.lower()
        job_loc = job.get("location", "")
        job_exp = job.get("experience", "Not Specified")
        snippet = job.get("description_snippet", "") or ""

        # =========================================================================
        # STEP 1: STRICT PRE-FILTERING (REJECT IMMEDIATELY)
        # =========================================================================

        # 1A. Strict Cross-Domain Mismatch Rejection
        if is_tech_role and any(k in title_norm for k in ["nurse", "physician", "doctor", "sales rep", "account executive", "dental", "legal counsel", "marketing manager", "recruiter", "talent", "client partner", "account manager", "hr manager", "people partner", "business recruiter", "sales manager"]):
            continue
        if is_marketing_role and any(k in title_norm for k in ["registered nurse", "devops engineer", "embedded firmware", "software engineer", "backend developer"]):
            continue
        if is_health_role and any(k in title_norm for k in ["react developer", "full stack engineer", "python backend", "devops"]):
            continue

        # 1B. Strict Role Similarity Rejection (threshold >= 0.30)
        role_sim = calculate_role_similarity(desired_role, title)
        if role_sim < 0.30:
            continue

        # 1C. Strict Experience Tier Rejection
        if not is_strict_experience_match(candidate_bracket, candidate_years, title, job_exp, snippet):
            continue

        # 1D. Strict Location / Remote Rejection
        from fetchers.base import is_location_match, clean_location_string
        if not is_location_match(job_loc, target_location, is_remote_only):
            continue

        # =========================================================================
        # STEP 2: SCORE FILTERED JOBS
        # =========================================================================

        # Factor 1: Skill Overlap (Weight 50%)
        job_detected_skills = extract_job_skills(job)
        matched_skills_list = []
        missing_skills_list = []

        for j_skill in job_detected_skills:
            if j_skill.lower() in candidate_skills_norm:
                matched_skills_list.append(candidate_skills_norm[j_skill.lower()])
            else:
                missing_skills_list.append(j_skill)

        # Check direct resume skill mentions in title
        for c_skill_lower, c_skill_original in candidate_skills_norm.items():
            if c_skill_lower in title_norm and c_skill_original not in matched_skills_list:
                matched_skills_list.append(c_skill_original)

        if job_detected_skills:
            skill_score = len(matched_skills_list) / len(job_detected_skills)
        else:
            skill_score = 0.80 if matched_skills_list else 0.65

        # Factor 2: Experience Alignment (Weight 30%)
        is_fresher_friendly = any(k in title_lower or k in job_exp.lower() or k in snippet.lower() for k in FRESHER_FRIENDLY_KEYWORDS)
        
        if is_user_fresher:
            exp_score = 1.0 if is_fresher_friendly else 0.85
        elif candidate_bracket in ["2-5", "2-5 years"]:
            exp_score = 1.0 if "senior" in title_lower or "2-5" in job_exp.lower() else 0.85
        elif is_user_fresher:
            exp_score = 1.0
        else:
            exp_score = 0.90

        # Factor 3: Role Similarity (Weight 20%)
        # role_sim is calculated above

        # Weighted Total Score (0 - 100%)
        total_score_raw = (skill_score * 0.50) + (exp_score * 0.30) + (role_sim * 0.20)
        final_percentage = int(min(99, max(50, total_score_raw * 100)))

        # =========================================================================
        # STEP 3: FRESHER BOOST & METADATA
        # =========================================================================
        if is_user_fresher and is_fresher_friendly:
            final_percentage = min(99, final_percentage + 10)

        # Construct explanation reason
        skill_reasons = ", ".join(matched_skills_list[:2]) if matched_skills_list else (candidate_skills[:2] if candidate_skills else ["Core skills"])
        if isinstance(skill_reasons, list):
            skill_reasons = ", ".join(skill_reasons)
            
        if is_fresher_friendly:
            reason_text = f"Fresher friendly, matches {skill_reasons}"
        else:
            reason_text = f"Matches your {skill_reasons}, {candidate_years} yrs exp"

        enriched_job = job.copy()
        enriched_job["location"] = clean_location_string(job_loc, default_location=target_location)
        enriched_job["match_score"] = final_percentage
        enriched_job["matched_skills"] = matched_skills_list
        enriched_job["missing_skills"] = missing_skills_list[:2]
        enriched_job["is_fresher_friendly"] = is_fresher_friendly
        enriched_job["reason"] = reason_text

        matched_results.append(enriched_job)

    # Sort by match score DESC, then freshness
    matched_results.sort(key=lambda x: (x.get("match_score", 0), x.get("posted_date", "")), reverse=True)
    return matched_results
