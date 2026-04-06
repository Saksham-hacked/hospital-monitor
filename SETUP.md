# Setup Guide

## Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account → https://supabase.com
- Google Gemini API key → https://aistudio.google.com/app/apikey

---

## 1. Supabase Setup

1. Create a new project at https://supabase.com
2. Go to **SQL Editor** and run `backend/schema.sql`
3. Go to **Project Settings → API** and copy:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`

---

## 2. Backend Setup

```bash
cd backend

# Configure env
cp .env.example .env
# Fill in GEMINI_API_KEY, SUPABASE_URL, SUPABASE_KEY, FRONTEND_URL

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn main:app --reload --port 8000
```

Backend: http://localhost:8000  
API docs: http://localhost:8000/docs

The pipeline runs automatically on startup and then every hour.

---

## 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173

> **For production deployment**, create a `.env` file in the `frontend/` directory:
> ```
> VITE_API_URL=https://your-deployed-backend-url/api
> ```
> Without this, the frontend will only work in local dev (where Vite's proxy handles `/api`).

---

## 4. Manual Trigger (for demo/testing)

```bash
curl -X POST http://localhost:8000/api/trigger
```

Or click **Run Now** in the dashboard.

---

## 5. Add More Hospital Sources

**Greenhouse** — find the board token from `boards.greenhouse.io/<token>` and add to `GREENHOUSE_HOSPITALS` in `scraper/greenhouse_fetcher.py`:

```python
{"name": "Hospital Name", "board_token": "token"},
```

**Lever** — find the company ID from `jobs.lever.co/<company_id>` and add to `LEVER_HOSPITALS` in `scraper/lever_fetcher.py`:

```python
{"name": "Hospital Name", "company_id": "company_id"},
```

Only add tokens you have verified return 200 from the public API.

---

## 6. Deploy

**Backend** → Railway or Render  
Start command: `uvicorn main:app --host 0.0.0.0 --port 8000`  
Set env vars in the platform dashboard.

**Frontend** → Vercel  
Set `VITE_API_URL` to your deployed backend URL (e.g. `https://your-app.railway.app/api`) in Vercel's Environment Variables dashboard before deploying.
