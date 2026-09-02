import asyncio
import json
import os
import sys
import time
from typing import List, Dict, Any

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from core.orchestrator import orchestrate

async def run_orchestrator_test(
    role: str = "Frontend Developer",
    location: str = "Bangalore, India",
    exp_level: str = "fresher",
    resume_skills: List[str] = None,
    limit: int = 100,
    output_file: str = "test_results.json"
) -> Dict[str, Any]:
    """
    Test and validate all multi-layer fetchers through orchestrate().
    """
    if resume_skills is None:
        resume_skills = ["React", "JavaScript", "HTML", "CSS"]

    print("=" * 70)
    print("🚀 HIREPULSE UNIVERSAL JOB ENGINE: ORCHESTRATOR VALIDATION TEST")
    print("=" * 70)
    print(f"Role:           {role}")
    print(f"Location:       {location}")
    print(f"Experience:     {exp_level}")
    print(f"Resume Skills:  {', '.join(resume_skills)}")
    print(f"Target Limit:   {limit}")
    print("-" * 70)
    print("Executing 4-layer concurrent aggregation...")

    start_time = time.time()

    # Run orchestrator
    result = await orchestrate(
        role=role,
        location=location,
        exp=exp_level,
        candidate_skills=resume_skills,
        limit=limit,
        force_refresh=False
    )

    elapsed_time = round(time.time() - start_time, 2)
    jobs = result.get("jobs", [])
    total_found = result.get("total", len(jobs))
    sources_breakdown = result.get("sources_breakdown", {})
    layers_breakdown = result.get("layers_breakdown", {})
    is_cached = result.get("cached", False)

    print("\n" + "=" * 70)
    print("📊 VALIDATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"Total Jobs Found:     {total_found}")
    print(f"Time Taken:           {elapsed_time}s ({'Cache Hit' if is_cached else 'Live Fetch'})")
    if layers_breakdown:
        print("\nLayer Breakdown:")
        for layer, count in layers_breakdown.items():
            print(f"  • {layer:<28}: {count:>4} jobs")

    print("\nSources Breakdown:")
    for src, count in sorted(sources_breakdown.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {src:<28}: {count:>4} jobs")

    print("\n" + "-" * 70)
    print("🏆 TOP 5 MATCHED JOBS (Ranked by Resume Skills Match Score):")
    print("-" * 70)

    for idx, job in enumerate(jobs[:5], start=1):
        title = job.get("title", "N/A")
        company = job.get("company", "N/A")
        loc = job.get("location", "N/A")
        score = job.get("match_score", "N/A")
        source = job.get("source", "N/A")
        url = job.get("apply_link") or job.get("url") or "N/A"

        print(f"\n[{idx}] {title}")
        print(f"    Company:     {company}")
        print(f"    Location:    {loc}")
        print(f"    Match Score: {score}%")
        print(f"    Source:      {source}")
        print(f"    Apply URL:   {url}")

    # Save to JSON file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(script_dir, output_file)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 70)
    print(f"💾 Full results successfully saved to: {json_path}")
    print("=" * 70)

    return result

if __name__ == "__main__":
    asyncio.run(run_orchestrator_test())

