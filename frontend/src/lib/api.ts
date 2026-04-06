const BASE = import.meta.env.VITE_API_URL ?? "/api";

export async function fetchJobs(onlyNew = false) {
  const res = await fetch(`${BASE}/jobs?only_new=${onlyNew}&limit=200`);
  if (!res.ok) throw new Error("Failed to fetch jobs");
  return res.json();
}

export async function fetchSummary() {
  const res = await fetch(`${BASE}/summary`);
  if (!res.ok) throw new Error("Failed to fetch summary");
  return res.json();
}

export async function fetchHospitalStats() {
  const res = await fetch(`${BASE}/stats/hospitals`);
  if (!res.ok) throw new Error("Failed to fetch hospital stats");
  return res.json();
}

export async function fetchDepartmentStats() {
  const res = await fetch(`${BASE}/stats/departments`);
  if (!res.ok) throw new Error("Failed to fetch department stats");
  return res.json();
}

export async function triggerPipeline() {
  const res = await fetch(`${BASE}/trigger`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to trigger pipeline");
  return res.json();
}
