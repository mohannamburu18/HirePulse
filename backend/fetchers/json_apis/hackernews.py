import asyncio
import aiohttp
import logging
import re
import html
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# NOTE: Hacker News posts a new "Ask HN: Who is hiring?" thread on the 1st of every month.
# Default thread ID below is for demonstration; users can update this ID monthly
# or override it dynamically.
DEFAULT_HN_THREAD_ID = 41234567

HN_FIREBASE_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{item_id}.json"

def clean_html(raw_html: str) -> str:
    """Convert HTML entities and tags into readable plaintext."""
    if not raw_html:
        return ""
    # Replace <p> with newlines
    text = re.sub(r"<\s*p\s*/?>", "\n\n", raw_html, flags=re.IGNORECASE)
    # Replace <br> with newlines
    text = re.sub(r"<\s*br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Unescape HTML entities (&amp;, &#x27;, &quot;, etc.)
    return html.unescape(text).strip()

async def fetch_comment_item(
    session: aiohttp.ClientSession,
    comment_id: int
) -> Optional[Dict[str, Any]]:
    """Fetch an individual comment item from Hacker News Firebase API."""
    url = HN_FIREBASE_ITEM_URL.format(item_id=comment_id)
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                if isinstance(data, dict) and not data.get("deleted") and not data.get("dead"):
                    return data
    except Exception as e:
        logger.debug(f"Failed to fetch HN comment {comment_id}: {e}")
    return None

async def fetch_hackernews_jobs(
    role: str = "Frontend Developer",
    location: str = "Bangalore",
    exp_level: str = "fresher",
    thread_id: int = DEFAULT_HN_THREAD_ID
) -> List[Dict[str, Any]]:
    """
    Fetch and parse job postings from Hacker News "Who is Hiring?" thread.
    
    Requirements:
    - Uses Firebase API: https://hacker-news.firebaseio.com/v0/item/{thread_id}.json
    - Default thread ID: 41234567 (update monthly when new thread is posted)
    - Fetches thread details, then fetches comments in parallel via asyncio.gather
    - Limits to 50 comments
    - Parses comment text for '|' delimiters (Company | Role | Location)
    - Checks if role appears in comment text
    - Filters by location (checks user location, India, or Remote)
    - For fresher filters, checks for fresher keywords in text
    - Returns normalized job dicts: title, company, location, description, url, posted_date, source, raw
    - Detailed logging at each stage
    """
    role_clean = (role or "").strip().lower()
    loc_clean = (location or "remote").strip().lower()
    exp_clean = (exp_level or "fresher").strip().lower()
    is_fresher_filter = exp_clean in ["fresher", "0", "0-1", "entry", "entry level", "new grad"]

    logger.info(f"Stage 1: Fetching HN Who is Hiring thread (ID: {thread_id})...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    }

    matched_jobs: List[Dict[str, Any]] = []

    try:
        timeout = aiohttp.ClientTimeout(total=25)
        async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
            # 1. Fetch thread item
            thread_url = HN_FIREBASE_ITEM_URL.format(item_id=thread_id)
            async with session.get(thread_url) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to fetch HN thread {thread_id}, HTTP {resp.status}")
                    return []
                thread_data = await resp.json()

            if not isinstance(thread_data, dict):
                logger.warning(f"Invalid thread payload for HN thread {thread_id}")
                return []

            kids = thread_data.get("kids", [])
            logger.info(f"Stage 2: Found {len(kids)} total comments on thread {thread_id}")

            # If default thread 41234567 has 0 kids (placeholder ID), try finding latest active hiring thread
            if not kids:
                logger.info(f"Thread {thread_id} has no comments. Looking up latest active 'Ask HN: Who is hiring?' thread...")
                try:
                    async with session.get("https://hn.algolia.com/api/v1/search?query=Ask%20HN:%20Who%20is%20hiring&tags=story&hitsPerPage=1") as algolia_resp:
                        if algolia_resp.status == 200:
                            algolia_data = await algolia_resp.json()
                            hits = algolia_data.get("hits", [])
                            if hits and hits[0].get("objectID"):
                                active_id = int(hits[0]["objectID"])
                                logger.info(f"Switching to active HN Who is Hiring thread: {hits[0].get('title')} (ID: {active_id})")
                                async with session.get(HN_FIREBASE_ITEM_URL.format(item_id=active_id)) as active_thread_resp:
                                    if active_thread_resp.status == 200:
                                        active_thread = await active_thread_resp.json()
                                        kids = active_thread.get("kids", []) if isinstance(active_thread, dict) else []
                except Exception as ex:
                    logger.debug(f"Could not auto-lookup fallback HN thread: {ex}")

            if not kids:
                logger.warning(f"No comments found in HN hiring thread.")
                return []

            # Limit to 50 comments as required
            target_comment_ids = kids[:50]
            logger.info(f"Stage 3: Fetching {len(target_comment_ids)} comments in parallel via asyncio.gather...")

            tasks = [fetch_comment_item(session, cid) for cid in target_comment_ids]
            comments = await asyncio.gather(*tasks, return_exceptions=True)

            logger.info(f"Stage 4: Parsing and filtering {len(comments)} fetched comments...")

            for comment in comments:
                if not isinstance(comment, dict) or not comment.get("text"):
                    continue

                raw_html = comment.get("text") or ""
                comment_text = clean_html(raw_html)
                if not comment_text:
                    continue

                text_lower = comment_text.lower()

                # Extract first line for '|' delimiters (Company | Role | Location)
                lines = [l.strip() for l in comment_text.splitlines() if l.strip()]
                first_line = lines[0] if lines else ""

                company = "Hacker News Employer"
                job_title = role or "Software Engineer"
                job_location = "Remote"

                if "|" in first_line:
                    parts = [p.strip() for p in first_line.split("|") if p.strip()]
                    if len(parts) >= 1:
                        company = parts[0]
                    if len(parts) >= 2:
                        job_title = parts[1]
                    if len(parts) >= 3:
                        job_location = " | ".join(parts[2:])
                else:
                    # Fallback parsing
                    first_words = first_line.split()[:4]
                    if first_words:
                        company = " ".join(first_words).rstrip(",.:;-")

                title_lower = job_title.lower()
                loc_lower = job_location.lower()

                # 1. Role Filter Check: role appears in title or full comment text
                role_tokens = [t for t in re.split(r"[\s\-_/]+", role_clean) if len(t) >= 3]
                role_match = False
                if not role_clean:
                    role_match = True
                elif role_clean in title_lower or role_clean in text_lower:
                    role_match = True
                elif role_tokens and any(tok in title_lower or tok in text_lower for tok in role_tokens):
                    role_match = True

                if not role_match:
                    continue

                # 2. Location Filter Check: user location, India, or Remote
                location_match = False
                if not loc_clean or "remote" in loc_clean:
                    location_match = "remote" in loc_lower or "remote" in text_lower or "anywhere" in loc_lower or "wfh" in text_lower
                else:
                    user_city = loc_clean.split(",")[0].strip()
                    bangalore_aliases = ["bangalore", "bengaluru", "blr"]
                    if any(alias in user_city for alias in bangalore_aliases):
                        location_match = any(alias in loc_lower or alias in text_lower for alias in bangalore_aliases) or ("remote" in loc_lower and "india" in text_lower)
                    elif "india" in loc_clean:
                        location_match = "india" in loc_lower or "india" in text_lower or any(c in text_lower for c in ["bangalore", "bengaluru", "hyderabad", "pune", "mumbai", "delhi"])
                    else:
                        location_match = user_city in loc_lower or user_city in text_lower or "remote" in loc_lower

                # If no strict location match was found, allow if post explicitly offers remote
                if not location_match and ("remote" in loc_lower or "remote" in text_lower):
                    location_match = True

                if not location_match:
                    continue

                # 3. Fresher Filter Check: check for fresher keywords in text
                if is_fresher_filter:
                    fresher_keywords = ["fresher", "junior", "entry level", "entry-level", "intern", "internship", "new grad", "associate", "0-1", "0-2", "no experience"]
                    has_fresher = any(kw in title_lower or kw in text_lower for kw in fresher_keywords)
                    # Also reject if comment explicitly requires 5+ or Senior
                    has_senior_only = any(kw in title_lower for kw in ["senior", "lead", "principal", "staff", "head of", "director"])
                    if not has_fresher or has_senior_only:
                        continue

                # External URL detection from comment text
                urls_in_text = re.findall(r"https?://[^\s<>\"']+", raw_html)
                comment_id = comment.get("id")
                hn_url = f"https://news.ycombinator.com/item?id={comment_id}" if comment_id else "https://news.ycombinator.com"
                apply_url = urls_in_text[0] if urls_in_text else hn_url

                # Posted date
                created_ts = comment.get("time")
                posted_date = datetime.fromtimestamp(created_ts, timezone.utc).strftime("%Y-%m-%d") if created_ts else "Recently"

                matched_jobs.append({
                    "title": job_title,
                    "company": company,
                    "location": job_location,
                    "description": comment_text,
                    "url": apply_url,
                    "posted_date": posted_date,
                    "source": "HackerNews",
                    "raw": comment
                })

            logger.info(f"Stage 5: Finished HN search. Matched {len(matched_jobs)} job postings.")
            return matched_jobs

    except Exception as e:
        logger.error(f"Error fetching Hacker News jobs: {e}", exc_info=True)
        return []

