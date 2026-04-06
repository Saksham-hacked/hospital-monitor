-- Run this in your Supabase SQL editor before starting the app

create table if not exists jobs (
  id uuid primary key default gen_random_uuid(),
  extracted_at timestamptz not null,
  hospital_name text not null,
  job_title text,
  department text,
  location text,
  job_type text,
  experience_level text,
  specialty text,
  is_urgent boolean default false,
  is_healthcare_role boolean default true,
  ai_summary text,
  job_url text,
  source_url text,
  raw_text text,
  content_hash text,
  is_new boolean default true,
  created_at timestamptz default now()
);

create table if not exists trend_summaries (
  id uuid primary key default gen_random_uuid(),
  summary text not null,
  stats jsonb,
  created_at timestamptz default now()
);

-- Fast dedup lookups
create index if not exists idx_jobs_dedup on jobs (hospital_name, job_url);
create index if not exists idx_jobs_hash on jobs (content_hash);
create index if not exists idx_jobs_new on jobs (is_new) where is_new = true;
create index if not exists idx_jobs_extracted on jobs (extracted_at desc);
