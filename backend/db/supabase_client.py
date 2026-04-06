from supabase import create_client, Client
from dotenv import load_dotenv
from collections import Counter
import os
import hashlib

load_dotenv()

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        # Simple init — no options dict (compatible with all supabase-py versions)
        _client = create_client(url, key)
    return _client


SCHEMA_COLUMNS = {
    "extracted_at", "hospital_name", "job_title", "department", "location",
    "job_type", "experience_level", "specialty", "is_urgent", "is_healthcare_role",
    "ai_summary", "job_url", "source_url", "raw_text", "is_new", "content_hash",
}


def make_content_hash(raw_text: str) -> str:
    return hashlib.md5(raw_text.encode("utf-8", errors="ignore")).hexdigest()


def fetch_existing_keys() -> set[tuple]:
    """
    Returns a set of (hospital_name, job_url, content_hash) tuples already in DB.
    Used for pre-dedup before normalization so we don't waste Gemini tokens.
    """
    client = get_client()
    result = (
        client.table("jobs")
        .select("hospital_name, job_url, content_hash")
        .limit(50000)
        .execute()
    )
    keys = set()
    for row in (result.data or []):
        keys.add((
            row.get("hospital_name", ""),
            row.get("job_url", "") or "",
            row.get("content_hash", "") or "",
        ))
    return keys


def upsert_job(job: dict) -> dict | None:
    """
    Direct insert — pre-dedup in pipeline means this should only
    receive genuinely new jobs. SELECT check removed to save DB round-trips.
    """
    client = get_client()
    clean = {k: v for k, v in job.items() if k in SCHEMA_COLUMNS}
    clean["is_new"] = True
    try:
        result = client.table("jobs").insert(clean).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        # Catch any constraint violations from the safety-net DB index
        logger_warning = f"[DB] Insert skipped (likely duplicate): {e}"
        print(logger_warning)
        return None


def mark_jobs_old():
    try:
        client = get_client()
        client.table("jobs").update({"is_new": False}).eq("is_new", True).execute()
    except Exception as e:
        print(f"[DB] Warning: mark_jobs_old failed: {e}")


def fetch_jobs(limit: int = 100, only_new: bool = False) -> list[dict]:
    client = get_client()
    query = (
        client.table("jobs")
        .select("*")
        .order("extracted_at", desc=True)
        .limit(limit)
    )
    if only_new:
        query = query.eq("is_new", True)
    result = query.execute()
    return result.data or []


def fetch_latest_summary() -> dict | None:
    client = get_client()
    result = (
        client.table("trend_summaries")
        .select("*")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def save_summary(summary_text: str, stats: dict):
    client = get_client()
    client.table("trend_summaries").insert({
        "summary": summary_text,
        "stats": stats,
    }).execute()


def fetch_hospital_stats() -> list[dict]:
    client = get_client()
    result = client.table("jobs").select("hospital_name").execute()
    counts = Counter(row["hospital_name"] for row in (result.data or []))
    return [{"hospital": k, "count": v} for k, v in counts.most_common()]


def fetch_department_stats() -> list[dict]:
    client = get_client()
    result = client.table("jobs").select("department").execute()
    counts = Counter(
        row["department"] for row in (result.data or []) if row.get("department")
    )
    return [{"department": k, "count": v} for k, v in counts.most_common(10)]
