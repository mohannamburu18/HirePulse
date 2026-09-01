from typing import List

ALL_LEVER_COMPANIES = [
    "spotify", "palantir", "coupa", "canva", "affirm", "benchling",
    "mux", "sourcegraph", "elastic", "hasura", "postman", "browserstack",
    "chargebee", "freshworks", "zoho", "upstox", "groww", "zerodha",
    "razorpay", "swiggy", "cred", "meesho", "phonepe"
]

ALL_GREENHOUSE_COMPANIES = [
    "mongodb", "zscaler", "toast", "elastic", "datadog", "figma",
    "notion", "airbnb", "coinbase", "stripe", "lyft", "doordash",
    "asana", "reddit", "databricks", "openai", "dropbox", "okta",
    "snowflake", "postman", "hasura", "browserstack", "chargebee",
    "freshworks", "razorpay", "swiggy", "cred", "phonepe", "gojek", "grab"
]

ALL_ASHBY_COMPANIES = [
    "linear", "ramp", "retool", "ashby", "quora", "notion", "sentry",
    "elevenlabs", "perplexity", "cursor", "posthog", "vanta", "loom",
    "descript", "vercel", "monzo", "resend"
]

def get_lever_companies_for_location(user_location: str) -> List[str]:
    return ALL_LEVER_COMPANIES

def get_greenhouse_companies_for_location(user_location: str) -> List[str]:
    return ALL_GREENHOUSE_COMPANIES

def get_ashby_companies_for_location(user_location: str) -> List[str]:
    return ALL_ASHBY_COMPANIES

