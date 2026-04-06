from fastapi import APIRouter, Query, BackgroundTasks
from db.supabase_client import (
    fetch_jobs,
    fetch_latest_summary,
    fetch_hospital_stats,
    fetch_department_stats,
)
from scheduler.jobs import run_pipeline

router = APIRouter()


@router.get("/jobs")
def get_jobs(
    limit: int = Query(default=100, le=500),
    only_new: bool = Query(default=False),
):
    """Return job listings, optionally filtered to only newly detected ones."""
    jobs = fetch_jobs(limit=limit, only_new=only_new)
    return {"count": len(jobs), "jobs": jobs}


@router.get("/summary")
def get_summary():
    """Return the latest AI-generated trend summary."""
    summary = fetch_latest_summary()
    if not summary:
        return {"summary": "No summary available yet. Run a scrape cycle first.", "stats": {}}
    return summary


@router.get("/stats/hospitals")
def get_hospital_stats():
    """Return job count per hospital — used for bar charts."""
    return {"data": fetch_hospital_stats()}


@router.get("/stats/departments")
def get_department_stats():
    """Return top departments by job count."""
    return {"data": fetch_department_stats()}


@router.post("/trigger")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """Manually trigger a scrape cycle (useful for demo/testing)."""
    background_tasks.add_task(run_pipeline)
    return {"message": "Scrape pipeline triggered. Check back in ~2 minutes for results."}
