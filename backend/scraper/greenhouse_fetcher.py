import httpx
import re
from datetime import datetime, timezone


def _strip_html(text: str) -> str:
    """Remove HTML tags and collapse whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()

# Hospitals/health systems using Greenhouse ATS — verified working board tokens
GREENHOUSE_HOSPITALS = [
    # US — verified via boards.greenhouse.io/<token>
    {"name": "Vail Health", "board_token": "vailclinicincdbavailhealthhospital"},
    {"name": "Integrity Rehab Group", "board_token": "integrityrehabgroup"},
    {"name": "Shields Health Solutions", "board_token": "shieldshealthsolutions"},
    {"name": "Cohere Health", "board_token": "coherehealth"},
]

GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"


def fetch_greenhouse_jobs() -> list[dict]:
    """
    Fetches jobs from hospitals using Greenhouse ATS via their public JSON API.
    Returns normalized raw job dicts ready for the AI normalizer.
    """
    all_jobs = []

    with httpx.Client(timeout=15) as client:
        for hospital in GREENHOUSE_HOSPITALS:
            try:
                url = GREENHOUSE_API.format(token=hospital["board_token"])
                resp = client.get(url)

                if resp.status_code != 200:
                    print(f"[Greenhouse] {hospital['name']} returned {resp.status_code}")
                    continue

                data = resp.json()
                jobs = data.get("jobs", [])

                for job in jobs[:30]:  # cap per hospital
                    location = ""
                    offices = job.get("offices", [])
                    if offices:
                        location = offices[0].get("name", "")

                    all_jobs.append({
                        "hospital_name": hospital["name"],
                        "raw_text": f"{job.get('title', '')} {_strip_html(job.get('content', ''))[:300]}".strip(),
                        "job_url": job.get("absolute_url", ""),
                        "source_url": url,
                        "location": location,
                        "extracted_at": datetime.now(timezone.utc).isoformat(),
                        "source_type": "greenhouse",
                    })

                print(f"[Greenhouse] {hospital['name']}: {len(jobs)} jobs fetched")

            except Exception as e:
                print(f"[Greenhouse] Error fetching {hospital['name']}: {e}")

    return all_jobs


# {
#     "hospital_name": "Vail Health",
#     "raw_text": "Registered Nurse Medical Surgical Unit <first 300 chars of cleaned job content>",
#     "job_url": "https://job-boards.greenhouse.io/.../jobs/1234567",
#     "source_url": "https://boards-api.greenhouse.io/v1/boards/vailclinicincdbavailhealthhospital/jobs?content=true",
#     "location": "Vail, CO",
#     "extracted_at": "2026-04-08T10:15:23.456789+00:00",
#     "source_type": "greenhouse",
# }