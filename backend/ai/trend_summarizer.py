import os
import re
from dotenv import load_dotenv
from collections import Counter

from ai.gemini_client import gemini_call

load_dotenv()

# Cap jobs fed into the prompt — stats are aggregated so quality doesn't drop
MAX_JOBS_FOR_SUMMARY = 200

TREND_PROMPT = """
You are a healthcare staffing analyst.

Below is a summary of new hospital job postings detected in the last hour.

Data:
{data_summary}

Write a concise, professional hiring trend report (4-6 sentences) covering:
1. Which hospitals are most actively hiring
2. Which departments or specialties are in highest demand
3. Any urgency signals (urgent/ASAP roles)
4. A one-line outlook or recommendation for a staffing agency

Tone: professional, data-driven, direct. No fluff.
"""


def build_data_summary(jobs: list[dict]) -> str:
    hospital_counts = Counter(j.get("hospital_name", "Unknown") for j in jobs)
    dept_counts = Counter(j.get("department") for j in jobs if j.get("department"))
    urgent_count = sum(1 for j in jobs if j.get("is_urgent"))
    job_types = Counter(j.get("job_type") for j in jobs if j.get("job_type"))
    specialties = Counter(j.get("specialty") for j in jobs if j.get("specialty"))

    return "\n".join([
        f"Total new jobs: {len(jobs)}",
        f"Urgent roles: {urgent_count}",
        f"Hospitals (job count): {dict(hospital_counts.most_common(5))}",
        f"Top departments: {dict(dept_counts.most_common(5))}",
        f"Top specialties: {dict(specialties.most_common(5))}",
        f"Job types: {dict(job_types.most_common())}",
    ])


def generate_trend_summary(new_jobs: list[dict]) -> tuple[str, dict]:
    stats = {
        "total_new": len(new_jobs),
        "urgent_count": sum(1 for j in new_jobs if j.get("is_urgent")),
        "hospitals": dict(Counter(j.get("hospital_name") for j in new_jobs).most_common(5)),
        "departments": dict(Counter(j.get("department") for j in new_jobs if j.get("department")).most_common(5)),
    }

    if not new_jobs:
        return "No new job postings detected this cycle.", stats

    jobs = new_jobs[:MAX_JOBS_FOR_SUMMARY]
    prompt = TREND_PROMPT.format(data_summary=build_data_summary(jobs))

    try:
        text = gemini_call(prompt, caller="trend_summarizer")
        summary = re.sub(r"^```[a-z]*\s*|\s*```$", "", text)
        return summary, stats
    except Exception as e:
        return f"Trend summary unavailable. {len(new_jobs)} new jobs detected.", stats
