from typing import List, Dict, Any

# ============================================================================
# 1. LEVER COMPANIES (30+ Active Tech & Product Companies)
# API: GET https://api.lever.co/v0/postings/{company}?mode=json
# ============================================================================
LEVER_COMPANIES: List[str] = [
    # Indian Unicorns & Tech Leaders
    "razorpay", "swiggy", "cred", "meesho", "phonepe", "groww", "zerodha",
    "upstox", "browserstack", "chargebee", "freshworks", "zoho", "postman",
    "hasura", "urbancompany", "curefit", "mpl", "dream11", "lenskart", "spinny",
    # Global Tech & Product Companies
    "spotify", "palantir", "notion", "netlify", "zapier", "canva", "affirm",
    "benchling", "coupa", "sourcegraph", "mux", "docker", "gitlab", "kong",
    "plaid", "brex", "gusto", "airtable", "fullstory", "launchdarkly", "webflow"
]

ALL_LEVER_COMPANIES = LEVER_COMPANIES


# ============================================================================
# 2. GREENHOUSE COMPANIES (30+ High-Growth Tech & AI Enterprises)
# API: GET https://boards-api.greenhouse.io/v1/boards/{company}/jobs
# ============================================================================
GREENHOUSE_COMPANIES: List[str] = [
    # Top Tier Silicon Valley & Global Tech
    "coinbase", "stripe", "airbnb", "datadog", "figma", "notion", "lyft",
    "doordash", "asana", "reddit", "databricks", "openai", "dropbox", "okta",
    "snowflake", "mongodb", "zscaler", "toast", "elastic", "instacart",
    "pinterest", "robinhood", "twilio", "cloudflare", "github", "discord",
    "dataminr", "samsara", "gitlab", "vimeo", "pagerduty", "box", "hashicorp",
    # Indian & Regional Engineering Hubs
    "postman", "hasura", "browserstack", "chargebee", "freshworks",
    "razorpay", "swiggy", "cred", "phonepe", "gojek", "grab", "atlassian"
]

ALL_GREENHOUSE_COMPANIES = GREENHOUSE_COMPANIES


# ============================================================================
# 3. ASHBY COMPANIES (15+ Fast-Moving Startups & Modern Tech Companies)
# Public appData: https://jobs.ashbyhq.com/{company}
# ============================================================================
ASHBY_COMPANIES: List[str] = [
    "ashby", "linear", "ramp", "retool", "quora", "sentry", "elevenlabs",
    "perplexity", "cursor", "posthog", "vanta", "loom", "descript",
    "vercel", "monzo", "resend", "cognition", "modal", "supabase", "clerk",
    "synthesia", "scale", "incidentio", "tldraw"
]

ALL_ASHBY_COMPANIES = ASHBY_COMPANIES


# ============================================================================
# 4. WORKDAY COMPANIES (20+ Fortune 500 & Global Enterprise Tech)
# API: POST https://{domain}/wday/cxs/{company_name}/{wd_identifier}/jobs
# ============================================================================
WORKDAY_COMPANIES: List[Dict[str, str]] = [
    {
        "company_name": "Salesforce",
        "domain": "salesforce.wd12.myworkdayjobs.com",
        "wd_identifier": "External_Career_Site",
        "company": "Salesforce",
        "url": "https://salesforce.wd12.myworkdayjobs.com/wday/cxs/salesforce/External_Career_Site/jobs",
        "base_link": "https://salesforce.wd12.myworkdayjobs.com/en-US/External_Career_Site"
    },
    {
        "company_name": "Adobe",
        "domain": "adobe.wd5.myworkdayjobs.com",
        "wd_identifier": "external_experienced",
        "company": "Adobe",
        "url": "https://adobe.wd5.myworkdayjobs.com/wday/cxs/adobe/external_experienced/jobs",
        "base_link": "https://adobe.wd5.myworkdayjobs.com/en-US/external_experienced"
    },
    {
        "company_name": "Nvidia",
        "domain": "nvidia.wd5.myworkdayjobs.com",
        "wd_identifier": "NVIDIAExternalCareerSite",
        "company": "Nvidia",
        "url": "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs",
        "base_link": "https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite"
    },
    {
        "company_name": "Target",
        "domain": "target.wd5.myworkdayjobs.com",
        "wd_identifier": "targetcareers",
        "company": "Target",
        "url": "https://target.wd5.myworkdayjobs.com/wday/cxs/target/targetcareers/jobs",
        "base_link": "https://target.wd5.myworkdayjobs.com/en-US/targetcareers"
    },
    {
        "company_name": "Walmart",
        "domain": "walmart.wd5.myworkdayjobs.com",
        "wd_identifier": "WalmartExternal",
        "company": "Walmart",
        "url": "https://walmart.wd5.myworkdayjobs.com/wday/cxs/walmart/WalmartExternal/jobs",
        "base_link": "https://walmart.wd5.myworkdayjobs.com/en-US/WalmartExternal"
    },
    {
        "company_name": "Dell",
        "domain": "dell.wd1.myworkdayjobs.com",
        "wd_identifier": "External",
        "company": "Dell Technologies",
        "url": "https://dell.wd1.myworkdayjobs.com/wday/cxs/dell/External/jobs",
        "base_link": "https://dell.wd1.myworkdayjobs.com/en-US/External"
    },
    {
        "company_name": "Cisco",
        "domain": "cisco.wd5.myworkdayjobs.com",
        "wd_identifier": "Cisco_Careers",
        "company": "Cisco",
        "url": "https://cisco.wd5.myworkdayjobs.com/wday/cxs/cisco/Cisco_Careers/jobs",
        "base_link": "https://cisco.wd5.myworkdayjobs.com/en-US/Cisco_Careers"
    },
    {
        "company_name": "HP",
        "domain": "hp.wd5.myworkdayjobs.com",
        "wd_identifier": "ExternalCareerSite",
        "company": "HP",
        "url": "https://hp.wd5.myworkdayjobs.com/wday/cxs/hp/ExternalCareerSite/jobs",
        "base_link": "https://hp.wd5.myworkdayjobs.com/en-US/ExternalCareerSite"
    },
    {
        "company_name": "Intel",
        "domain": "intel.wd1.myworkdayjobs.com",
        "wd_identifier": "External",
        "company": "Intel",
        "url": "https://intel.wd1.myworkdayjobs.com/wday/cxs/intel/External/jobs",
        "base_link": "https://intel.wd1.myworkdayjobs.com/en-US/External"
    },
    {
        "company_name": "AMD",
        "domain": "amd.wd1.myworkdayjobs.com",
        "wd_identifier": "AMD_External",
        "company": "AMD",
        "url": "https://amd.wd1.myworkdayjobs.com/wday/cxs/amd/AMD_External/jobs",
        "base_link": "https://amd.wd1.myworkdayjobs.com/en-US/AMD_External"
    },
    {
        "company_name": "Qualcomm",
        "domain": "qualcomm.wd5.myworkdayjobs.com",
        "wd_identifier": "External",
        "company": "Qualcomm",
        "url": "https://qualcomm.wd5.myworkdayjobs.com/wday/cxs/qualcomm/External/jobs",
        "base_link": "https://qualcomm.wd5.myworkdayjobs.com/en-US/External"
    },
    {
        "company_name": "PayPal",
        "domain": "paypal.wd1.myworkdayjobs.com",
        "wd_identifier": "jobs",
        "company": "PayPal",
        "url": "https://paypal.wd1.myworkdayjobs.com/wday/cxs/paypal/jobs/jobs",
        "base_link": "https://paypal.wd1.myworkdayjobs.com/en-US/jobs"
    },
    {
        "company_name": "Intuit",
        "domain": "intuit.wd5.myworkdayjobs.com",
        "wd_identifier": "External",
        "company": "Intuit",
        "url": "https://intuit.wd5.myworkdayjobs.com/wday/cxs/intuit/External/jobs",
        "base_link": "https://intuit.wd5.myworkdayjobs.com/en-US/External"
    },
    {
        "company_name": "Autodesk",
        "domain": "autodesk.wd1.myworkdayjobs.com",
        "wd_identifier": "Ext",
        "company": "Autodesk",
        "url": "https://autodesk.wd1.myworkdayjobs.com/wday/cxs/autodesk/Ext/jobs",
        "base_link": "https://autodesk.wd1.myworkdayjobs.com/en-US/Ext"
    },
    {
        "company_name": "ServiceNow",
        "domain": "servicenow.wd1.myworkdayjobs.com",
        "wd_identifier": "External",
        "company": "ServiceNow",
        "url": "https://servicenow.wd1.myworkdayjobs.com/wday/cxs/servicenow/External/jobs",
        "base_link": "https://servicenow.wd1.myworkdayjobs.com/en-US/External"
    },
    {
        "company_name": "VMware",
        "domain": "vmware.wd1.myworkdayjobs.com",
        "wd_identifier": "VMware",
        "company": "VMware",
        "url": "https://vmware.wd1.myworkdayjobs.com/wday/cxs/vmware/VMware/jobs",
        "base_link": "https://vmware.wd1.myworkdayjobs.com/en-US/VMware"
    },
    {
        "company_name": "Workday",
        "domain": "workday.wd5.myworkdayjobs.com",
        "wd_identifier": "Workday",
        "company": "Workday Inc",
        "url": "https://workday.wd5.myworkdayjobs.com/wday/cxs/workday/Workday/jobs",
        "base_link": "https://workday.wd5.myworkdayjobs.com/en-US/Workday"
    },
    {
        "company_name": "Mastercard",
        "domain": "mastercard.wd1.myworkdayjobs.com",
        "wd_identifier": "CorporateCareers",
        "company": "Mastercard",
        "url": "https://mastercard.wd1.myworkdayjobs.com/wday/cxs/mastercard/CorporateCareers/jobs",
        "base_link": "https://mastercard.wd1.myworkdayjobs.com/en-US/CorporateCareers"
    },
    {
        "company_name": "Visa",
        "domain": "visa.wd1.myworkdayjobs.com",
        "wd_identifier": "Visa_External",
        "company": "Visa",
        "url": "https://visa.wd1.myworkdayjobs.com/wday/cxs/visa/Visa_External/jobs",
        "base_link": "https://visa.wd1.myworkdayjobs.com/en-US/Visa_External"
    },
    {
        "company_name": "Accenture",
        "domain": "accenture.wd3.myworkdayjobs.com",
        "wd_identifier": "AccentureCareers",
        "company": "Accenture",
        "url": "https://accenture.wd3.myworkdayjobs.com/wday/cxs/accenture/AccentureCareers/jobs",
        "base_link": "https://accenture.wd3.myworkdayjobs.com/en-US/AccentureCareers"
    },
    {
        "company_name": "IBM",
        "domain": "ibm.wd3.myworkdayjobs.com",
        "wd_identifier": "IBM_Careers",
        "company": "IBM",
        "url": "https://ibm.wd3.myworkdayjobs.com/wday/cxs/ibm/IBM_Careers/jobs",
        "base_link": "https://ibm.wd3.myworkdayjobs.com/en-US/IBM_Careers"
    },
    {
        "company_name": "General Electric",
        "domain": "ge.wd5.myworkdayjobs.com",
        "wd_identifier": "GE_Jobs",
        "company": "General Electric",
        "url": "https://ge.wd5.myworkdayjobs.com/wday/cxs/ge/GE_Jobs/jobs",
        "base_link": "https://ge.wd5.myworkdayjobs.com/en-US/GE_Jobs"
    }
]

ALL_WORKDAY_COMPANIES = WORKDAY_COMPANIES


def get_lever_companies_for_location(user_location: str) -> List[str]:
    return ALL_LEVER_COMPANIES

def get_greenhouse_companies_for_location(user_location: str) -> List[str]:
    return ALL_GREENHOUSE_COMPANIES

def get_ashby_companies_for_location(user_location: str) -> List[str]:
    return ALL_ASHBY_COMPANIES

def get_workday_companies_for_location(user_location: str) -> List[Dict[str, str]]:
    return ALL_WORKDAY_COMPANIES
