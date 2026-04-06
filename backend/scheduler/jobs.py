from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
import logging
import threading

from scraper.greenhouse_fetcher import fetch_greenhouse_jobs
from scraper.lever_fetcher import fetch_lever_jobs
from ai.normalizer import normalize_batch
from ai.trend_summarizer import generate_trend_summary
from db.supabase_client import upsert_job, mark_jobs_old, save_summary, fetch_existing_keys, make_content_hash

logger = logging.getLogger(__name__)
scheduler = BackgroundScheduler()


def run_pipeline():
    """
    Hourly pipeline:
    1. Scrape Greenhouse + Lever APIs
    2. Stamp content_hash on every raw job
    3. Pre-dedup against DB — filter already-seen jobs before Gemini is called
    4. Normalize only new jobs (parallel, token-capped)
    5. Insert into Supabase
    6. Generate AI trend summary
    """
    logger.info("[Pipeline] Starting scrape cycle...")

    # Step 1: Mark previous new jobs as old
    mark_jobs_old()

    # Step 2: Scrape
    raw_jobs = fetch_greenhouse_jobs() + fetch_lever_jobs()
    logger.info(f"[Pipeline] {len(raw_jobs)} raw jobs fetched.")

    if not raw_jobs:
        logger.warning("[Pipeline] No jobs fetched. Check API tokens.")
        return

    # Step 3: Stamp content_hash
    for job in raw_jobs:
        job["content_hash"] = make_content_hash(job.get("raw_text", ""))

    # Step 4: Pre-dedup — one DB round-trip, filter before Gemini
    existing_keys = fetch_existing_keys()
    new_raw = [j for j in raw_jobs if not _is_duplicate(j, existing_keys)]
    logger.info(
        f"[Pipeline] Pre-dedup: {len(raw_jobs)} fetched, "
        f"{len(raw_jobs) - len(new_raw)} already in DB, "
        f"{len(new_raw)} going to normalizer."
    )

    if not new_raw:
        logger.info("[Pipeline] No new jobs this cycle. Skipping normalization.")
        return

    # Step 5: Normalize only new jobs
    normalized = normalize_batch(new_raw)

    # Drop non-healthcare roles (e.g. SWE, marketing, legal at health companies)
    healthcare = [j for j in normalized if j.get("is_healthcare_role", True)]
    dropped = len(normalized) - len(healthcare)
    if dropped:
        logger.info(f"[Pipeline] Filtered {dropped} non-healthcare roles.")

    # Step 6: Insert
    new_jobs = []
    for job in healthcare:
        result = upsert_job(job)
        if result:
            new_jobs.append(result)
    logger.info(f"[Pipeline] {len(new_jobs)} new jobs inserted.")

    # Step 7: Trend summary (only if we actually inserted jobs)
    if new_jobs:
        summary_text, stats = generate_trend_summary(new_jobs)
        save_summary(summary_text, stats)
        logger.info("[Pipeline] Trend summary saved.")
    else:
        logger.info("[Pipeline] No new jobs inserted — skipping trend summary.")
    logger.info("[Pipeline] Cycle complete.")


def _is_duplicate(job: dict, existing_keys: set[tuple]) -> bool:
    """
    Duplicate if (hospital_name, job_url) matches OR content_hash matches.
    URL match covers Greenhouse/Lever stable URLs.
    Hash match covers edge cases where URL is empty or unstable.
    """
    hospital = job.get("hospital_name", "")
    url = job.get("job_url", "") or ""
    chash = job.get("content_hash", "") or ""

    for ex_hospital, ex_url, ex_hash in existing_keys:
        if ex_hospital != hospital:
            continue
        if url and ex_url and url == ex_url:
            return True
        if chash and ex_hash and chash == ex_hash:
            return True
    return False


def start_scheduler():
    scheduler.add_job(
        run_pipeline,
        trigger=IntervalTrigger(hours=1),
        id="scrape_pipeline",
        name="Hospital Career Scrape Pipeline",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[Scheduler] Pipeline scheduled — runs every hour.")

    # Run immediately on startup so dashboard has data right away
    threading.Thread(target=run_pipeline, daemon=True).start()


def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[Scheduler] Shut down.")
