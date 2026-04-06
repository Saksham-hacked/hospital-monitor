# Hospital Career Monitor

An AI-powered staffing intelligence tool that aggregates hospital job postings from Greenhouse and Lever ATS APIs, normalizes them with Gemini, and surfaces hiring trends through a React dashboard.

Built for healthcare staffing agencies and recruiters who need real-time visibility across multiple hospital systems — without manually checking dozens of career pages.

---

## What It Does

- **Aggregates** job postings hourly from 8 hospital/health systems via Greenhouse and Lever public APIs
- **Normalizes** raw job data into structured fields (title, department, location, job type, urgency flag) using Gemini AI
- **Deduplicates** intelligently — pre-filters already-seen jobs before Gemini is called, so token usage stays near zero in steady state
- **Detects urgency** — flags ASAP/critical roles across the network in real time
- **Summarizes trends** — generates a plain-English hiring trend report after each cycle
- **Exposes** clean REST endpoints consumed by a React + Tailwind dashboard

---

## Architecture

```
hospital-monitor/
├── backend/
│   ├── main.py                  # FastAPI entry point + lifespan
│   ├── requirements.txt
│   ├── schema.sql               # Supabase table + index definitions
│   ├── .env.example
│   ├── scraper/
│   │   ├── greenhouse_fetcher.py  # Greenhouse public JSON API
│   │   └── lever_fetcher.py       # Lever public JSON API
│   ├── ai/
│   │   ├── gemini_client.py       # Shared Gemini wrapper with retry + logging
│   │   ├── normalizer.py          # Gemini: raw text → structured fields (parallel)
│   │   └── trend_summarizer.py    # Gemini: hourly trend report
│   ├── db/
│   │   └── supabase_client.py     # Supabase client + dedup logic
│   ├── scheduler/
│   │   └── jobs.py                # APScheduler hourly pipeline
│   └── api/
│       └── routes.py              # REST endpoints
└── frontend/
    ├── src/
    │   ├── App.tsx
    │   ├── pages/
    │   │   ├── Dashboard.tsx      # Stats, charts, AI summary, new jobs feed
    │   │   └── JobsTable.tsx      # Searchable, filterable jobs table
    │   └── lib/
    │       └── api.ts             # API client
    └── package.json
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Job APIs | Greenhouse API + Lever API (public, no auth) |
| Scheduler | APScheduler (hourly) |
| AI | Google Gemini 2.5 Flash |
| Database | Supabase (PostgreSQL + pgrest) |
| Backend | FastAPI + Uvicorn |
| Frontend | React + TypeScript + Tailwind CSS + Recharts |

---

## Pipeline Design

```
fetch (GH + Lever) → stamp content_hash → pre-dedup against DB
  → normalize only NEW jobs (parallel, 5 concurrent Gemini calls)
    → insert → trend summary → done
```

In steady state (after cycle 1), almost all jobs are already in the DB. The pre-dedup filter means Gemini is called for only the handful of genuinely new postings each hour — token usage is near zero until new jobs actually appear.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/jobs` | All jobs (`?only_new=true`, `?limit=100`) |
| GET | `/api/summary` | Latest AI trend summary |
| GET | `/api/stats/hospitals` | Job counts per hospital |
| GET | `/api/stats/departments` | Top departments |
| POST | `/api/trigger` | Manually trigger scrape pipeline |

---

## Setup

See `SETUP.md` for step-by-step instructions.
