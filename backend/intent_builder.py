from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class PreferenceInput(BaseModel):
    target_roles: List[str]
    locations: List[str]
    is_remote_only: bool = False
    experience_bracket: str = "2-5"
    job_types: List[str] = ["Full-time"]
    candidate_skills: Optional[List[str]] = None
    candidate_location: Optional[str] = None
    candidate_years: Optional[float] = None

class SearchIntent(BaseModel):
    id: str
    role: str
    primary_skills: List[str]
    location: str
    is_remote: bool
    exp_range: str
    job_types: List[str]
    search_query: str
    platforms: List[str]

class GeneratedIntentResponse(BaseModel):
    status: str
    intents: List[SearchIntent]
    summary: Dict[str, Any]

ROLE_SKILL_AFFINITY: Dict[str, List[str]] = {
    "frontend": ["React", "TypeScript", "JavaScript", "Next.js", "Vue.js", "Tailwind CSS", "HTML5", "CSS3", "Redux", "GraphQL"],
    "backend": ["Python", "FastAPI", "Django", "Node.js", "Go", "Java", "PostgreSQL", "MongoDB", "Redis", "Docker", "AWS", "REST APIs", "Microservices"],
    "full stack": ["React", "TypeScript", "Node.js", "Python", "FastAPI", "PostgreSQL", "Docker", "AWS", "GraphQL", "Tailwind CSS"],
    "devops": ["AWS", "Docker", "Kubernetes", "CI/CD", "Terraform", "Linux", "GitHub Actions", "GitLab", "GCP", "Azure"],
    "machine learning": ["Python", "PyTorch", "TensorFlow", "Machine Learning", "LLMs", "NLP", "Pandas", "NumPy", "Scikit-Learn"],
    "data": ["Python", "SQL", "PostgreSQL", "Pandas", "Spark", "Snowflake", "dbt", "Airflow", "Data Engineering"],
    "product manager": ["Agile", "Scrum", "Roadmap Planning", "User Stories", "Product Management", "JIRA", "OKRs", "KPIs"],
    "marketing": ["SEO", "SEM", "Google Analytics", "Content Marketing", "PPC", "HubSpot", "Brand Strategy", "A/B Testing", "Email Marketing", "CRO"],
    "sales": ["B2B Sales", "Salesforce", "CRM", "Lead Generation", "Cold Calling", "Pipeline Management", "Account Management", "Negotiation", "Deal Closing"],
    "nurse": ["Patient Care", "HIPAA", "EMR Systems", "Triage", "Vital Signs", "Pharmacology", "CPR / BLS", "Nursing", "Clinical Diagnosis"],
    "doctor": ["Clinical Diagnosis", "Patient Care", "Pharmacology", "Clinical Research", "HIPAA", "Medical Records", "Patient Assessment"],
    "finance": ["Financial Modeling", "DCF Valuation", "GAAP", "QuickBooks", "Excel", "FP&A", "Risk Management", "Portfolio Management", "Budgeting"]
}

def build_search_intents(prefs: PreferenceInput) -> GeneratedIntentResponse:
    intents: List[SearchIntent] = []
    candidate_skills = prefs.candidate_skills or []
    all_platforms = ["LinkedIn", "Indeed", "Naukri", "Lever", "Greenhouse", "Workday", "Ashby"]

    primary_location = "Remote" if prefs.is_remote_only else (prefs.locations[0] if prefs.locations else "Worldwide")

    for idx, role in enumerate(prefs.target_roles):
        role_clean = role.strip()
        if not role_clean:
            continue

        role_lower = role_clean.lower()
        relevant_skills: List[str] = []
        for key, aff_skills in ROLE_SKILL_AFFINITY.items():
            if key in role_lower:
                for s in aff_skills:
                    for cs in candidate_skills:
                        if cs.lower() == s.lower() and cs not in relevant_skills:
                            relevant_skills.append(cs)

        if not relevant_skills:
            relevant_skills = candidate_skills[:4]
        else:
            relevant_skills = relevant_skills[:5]

        skills_subquery = " OR ".join([f'"{s}"' for s in relevant_skills[:3]])
        if prefs.is_remote_only:
            query = f'"{role_clean}" {f"({skills_subquery})" if skills_subquery else ""} remote'
        else:
            query = f'"{role_clean}" {f"({skills_subquery})" if skills_subquery else ""} "{primary_location}"'

        intents.append(
            SearchIntent(
                id=f"intent_{idx + 1}_{role_lower.replace(' ', '_')}",
                role=role_clean,
                primary_skills=relevant_skills,
                location="Remote Only" if prefs.is_remote_only else primary_location,
                is_remote=prefs.is_remote_only,
                exp_range=prefs.experience_bracket,
                job_types=prefs.job_types,
                search_query=query.strip(),
                platforms=all_platforms
            )
        )

    summary = {
        "total_intents": len(intents),
        "target_roles": prefs.target_roles,
        "locations": ["Remote"] if prefs.is_remote_only else prefs.locations,
        "is_remote_only": prefs.is_remote_only,
        "experience_bracket": prefs.experience_bracket,
        "job_types": prefs.job_types,
        "platforms_count": len(all_platforms)
    }

    return GeneratedIntentResponse(
        status="success",
        intents=intents,
        summary=summary
    )

