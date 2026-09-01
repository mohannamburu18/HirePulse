import sqlite3
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "hirepulse.db")

def init_db():
    """Initialize SQLite database and user_profiles table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_profiles (
            id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT,
            resume_skills TEXT,
            experience_years REAL,
            desired_role TEXT,
            location TEXT,
            is_remote INTEGER,
            last_visited_at TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_user_profile(
    profile_id: str,
    name: str,
    email: Optional[str],
    skills: list,
    experience_years: float,
    desired_role: str,
    location: str,
    is_remote: bool
) -> Dict[str, Any]:
    """Save or update user profile in SQLite."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now_str = datetime.utcnow().isoformat()
    skills_json = json.dumps(skills)

    cursor.execute("""
        INSERT INTO user_profiles (
            id, name, email, resume_skills, experience_years,
            desired_role, location, is_remote, last_visited_at, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            email=excluded.email,
            resume_skills=excluded.resume_skills,
            experience_years=excluded.experience_years,
            desired_role=excluded.desired_role,
            location=excluded.location,
            is_remote=excluded.is_remote,
            last_visited_at=excluded.last_visited_at,
            updated_at=excluded.updated_at
    """, (
        profile_id, name, email, skills_json, experience_years,
        desired_role, location, 1 if is_remote else 0, now_str, now_str, now_str
    ))

    conn.commit()
    conn.close()

    return {
        "id": profile_id,
        "name": name,
        "email": email,
        "skills": skills,
        "experience_years": experience_years,
        "desired_role": desired_role,
        "location": location,
        "is_remote": is_remote,
        "updated_at": now_str
    }

def get_latest_profile() -> Optional[Dict[str, Any]]:
    """Retrieve the most recently updated profile."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM user_profiles ORDER BY updated_at DESC LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "skills": json.loads(row["resume_skills"]) if row["resume_skills"] else [],
        "experience_years": row["experience_years"],
        "desired_role": row["desired_role"],
        "location": row["location"],
        "is_remote": bool(row["is_remote"]),
        "last_visited_at": row["last_visited_at"],
        "updated_at": row["updated_at"]
    }

# Initialize DB on module import
init_db()

