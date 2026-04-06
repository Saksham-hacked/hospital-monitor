import asyncio
import json
import os
import re
from dotenv import load_dotenv

from ai.gemini_client import gemini_call

load_dotenv()

# Max chars of raw_text per job — ~300 tokens, enough for title/dept/urgency extraction
RAW_TEXT_LIMIT = 400
# Max concurrent Gemini calls — stays within free tier rate limits
CONCURRENCY = 5

NORMALIZATION_PROMPT = """
You are a healthcare job data extraction specialist.

Given raw text from a hospital ATS, extract structured job information.

Raw text:
\"\"\"{raw_text}\"\"\"

Hospital: {hospital_name}
URL: {job_url}

Return ONLY a valid JSON object with these exact fields:
{{
  "job_title": "cleaned job title or null",
  "department": "department/unit or null",
  "location": "city, state or null",
  "job_type": "Full-time | Part-time | PRN | Contract | Per Diem | null",
  "experience_level": "Entry | Mid | Senior | null",
  "specialty": "clinical specialty if applicable or null",
  "is_urgent": true or false,
  "is_healthcare_role": true or false,
  "summary": "1-2 sentence plain English summary of the role"
}}

Rules:
- job_type must be one of the allowed values or null. Use these mapping rules strictly:
  * "PRN", "prn", "as needed", "as-needed", "on call", "on-call" → PRN
  * "per diem", "per-diem", "daily" → Per Diem
  * "part-time", "part time", "PT ", "0.1 FTE" through "0.7 FTE", "casual" → Part-time
  * "full-time", "full time", "FT ", "0.8 FTE" through "1.0 FTE", "permanent" → Full-time
  * "contract", "temporary", "temp ", "travel", "locum", "locums" → Contract
  * If none of the above signals are present → null
- is_urgent = true only if text contains: ASAP, urgent, immediate, critical need
- is_healthcare_role = true if the role is directly healthcare-related: clinical, nursing, pharmacy,
  medical, therapy, radiology, lab, public health, health IT, or healthcare operations.
  is_healthcare_role = false for pure tech (SWE, ML engineer), marketing, sales, legal, finance,
  HR, or general admin roles that happen to be at a health company.
- If text is not a job posting, return null for all fields, summary = "Unable to parse"
- Never hallucinate details not in the text
"""


async def _normalize_one(raw_job: dict, semaphore: asyncio.Semaphore) -> dict:
    raw_text = raw_job.get("raw_text", "")[:RAW_TEXT_LIMIT]
    prompt = NORMALIZATION_PROMPT.format(
        raw_text=raw_text,
        hospital_name=raw_job.get("hospital_name", ""),
        job_url=raw_job.get("job_url", ""),
    )

    async with semaphore:
        try:
            loop = asyncio.get_event_loop()
            # gemini_call is sync + has retry — run in thread pool
            raw_text_response = await loop.run_in_executor(
                None,
                lambda: gemini_call(prompt, caller="normalizer"),
            )
            text = re.sub(r"^```json\s*|\s*```$", "", raw_text_response)
            parsed = json.loads(text)
            return {
                **raw_job,
                "job_title": parsed.get("job_title"),
                "department": parsed.get("department"),
                "location": parsed.get("location"),
                "job_type": parsed.get("job_type"),
                "experience_level": parsed.get("experience_level"),
                "specialty": parsed.get("specialty"),
                "is_urgent": parsed.get("is_urgent", False),
                "is_healthcare_role": parsed.get("is_healthcare_role", True),
                "ai_summary": parsed.get("summary"),
            }
        except Exception as e:
            # All retries exhausted — return a safe fallback so pipeline continues
            return {
                **raw_job,
                "job_title": None,
                "department": None,
                "location": None,
                "job_type": None,
                "experience_level": None,
                "specialty": None,
                "is_urgent": False,
                "ai_summary": "Parsing failed",
            }


def normalize_batch(raw_jobs: list[dict]) -> list[dict]:
    valid = [j for j in raw_jobs if j.get("raw_text") and len(j["raw_text"].strip()) >= 10]
    if not valid:
        return []

    async def _run():
        sem = asyncio.Semaphore(CONCURRENCY)
        return await asyncio.gather(*[_normalize_one(j, sem) for j in valid])

    loop = asyncio.new_event_loop()
    try:
        results = loop.run_until_complete(_run())
    finally:
        loop.close()
    print(f"[Normalizer] {len(results)}/{len(raw_jobs)} jobs normalized (parallel, cap={RAW_TEXT_LIMIT} chars).")
    return list(results)
