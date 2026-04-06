import httpx
from datetime import datetime, timezone

# Health systems using Lever ATS — verified working company IDs
LEVER_HOSPITALS = [
    # US — verified via api.lever.co/v0/postings/<company_id>
    {"name": "UCSF Health", "company_id": "ucsf"},
    {"name": "Aledade (Primary Care Network)", "company_id": "aledade"},
    {"name": "Circle Medical", "company_id": "circlemedical"},
    {"name": "Included Health", "company_id": "includedhealth"},
]

LEVER_API = "https://api.lever.co/v0/postings/{company_id}?mode=json"


def fetch_lever_jobs() -> list[dict]:
    """
    Fetches jobs from hospitals using Lever ATS via their public JSON API.
    Returns normalized raw job dicts ready for the AI normalizer.
    """
    all_jobs = []

    with httpx.Client(timeout=15) as client:
        for hospital in LEVER_HOSPITALS:
            try:
                url = LEVER_API.format(company_id=hospital["company_id"])
                resp = client.get(url)

                if resp.status_code != 200:
                    print(f"[Lever] {hospital['name']} returned {resp.status_code}")
                    continue

                jobs = resp.json()
                if not isinstance(jobs, list):
                    continue

                for job in jobs[:30]:
                    categories = job.get("categories", {})
                    location = categories.get("location", "")
                    department = categories.get("department", "")
                    team = categories.get("team", "")

                    # Build raw_text from available fields for AI normalizer
                    raw_parts = [
                        job.get("text", ""),
                        department,
                        team,
                        job.get("descriptionPlain", "")[:300],
                    ]
                    raw_text = " | ".join(p for p in raw_parts if p).strip()

                    all_jobs.append({
                        "hospital_name": hospital["name"],
                        "raw_text": raw_text[:500],
                        "job_url": job.get("hostedUrl", ""),
                        "source_url": url,
                        "location": location,
                        "department": department or None,
                        "extracted_at": datetime.now(timezone.utc).isoformat(),
                        "source_type": "lever",
                    })

                print(f"[Lever] {hospital['name']}: {len(jobs)} jobs fetched")

            except Exception as e:
                print(f"[Lever] Error fetching {hospital['name']}: {e}")

    return all_jobs
