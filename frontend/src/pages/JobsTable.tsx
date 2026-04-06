import { useEffect, useState } from "react";
import { fetchJobs } from "../lib/api";
import { Search, ExternalLink, AlertTriangle } from "lucide-react";

const JOB_TYPE_COLORS: Record<string, string> = {
  "Full-time": "bg-blue-500/10 text-blue-400 border-blue-500/20",
  "Part-time": "bg-purple-500/10 text-purple-400 border-purple-500/20",
  "PRN": "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  "Contract": "bg-orange-500/10 text-orange-400 border-orange-500/20",
  "Per Diem": "bg-pink-500/10 text-pink-400 border-pink-500/20",
};

export default function JobsTable() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [filtered, setFiltered] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [filterType, setFilterType] = useState("All");
  const [onlyNew, setOnlyNew] = useState(false);

  useEffect(() => {
    setError("");
    fetchJobs(false)
      .then((r) => {
        setJobs(r.jobs || []);
        setFiltered(r.jobs || []);
      })
      .catch(() => setError("Failed to load jobs. Is the backend running?"))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    let data = [...jobs];
    if (onlyNew) data = data.filter((j) => j.is_new);
    if (filterType !== "All") data = data.filter((j) => j.job_type === filterType);
    if (search.trim()) {
      const q = search.toLowerCase();
      data = data.filter(
        (j) =>
          j.job_title?.toLowerCase().includes(q) ||
          j.hospital_name?.toLowerCase().includes(q) ||
          j.department?.toLowerCase().includes(q) ||
          j.location?.toLowerCase().includes(q)
      );
    }
    setFiltered(data);
  }, [search, filterType, onlyNew, jobs]);

  const jobTypes = ["All", "Full-time", "Part-time", "PRN", "Contract", "Per Diem"];

  return (
    <div className="space-y-6 fade-in-up">

      {/* Header */}
      <div>
        <h1 className="font-display text-3xl font-bold text-text-primary tracking-tight">All Jobs</h1>
        <p className="text-text-secondary text-sm mt-1">
          {filtered.length} listings · filtered from {jobs.length} total
        </p>
      </div>

      {error && (
        <div className="text-sm text-urgent bg-urgent/10 border border-urgent/20 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-48">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
          <input
            type="text"
            placeholder="Search title, hospital, department..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-surface border border-border rounded-lg pl-9 pr-4 py-2 text-sm text-text-primary placeholder:text-muted focus:outline-none focus:border-accent/50 transition-colors"
          />
        </div>

        <div className="flex gap-1">
          {jobTypes.map((t) => (
            <button
              key={t}
              onClick={() => setFilterType(t)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                filterType === t
                  ? "bg-accent/10 text-accent border border-accent/20"
                  : "bg-surface border border-border text-text-secondary hover:text-text-primary"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <label className="flex items-center gap-2 text-sm text-text-secondary cursor-pointer select-none">
          <input
            type="checkbox"
            checked={onlyNew}
            onChange={(e) => setOnlyNew(e.target.checked)}
            className="accent-accent rounded"
          />
          New only
        </label>
      </div>

      {/* Table */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              {["Job Title", "Hospital", "Department", "Location", "Type", "Summary", ""].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-mono text-muted uppercase tracking-wider">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              [...Array(6)].map((_, i) => (
                <tr key={i} className="border-b border-border">
                  {[...Array(7)].map((_, j) => (
                    <td key={j} className="px-4 py-3">
                      <div className="h-4 bg-border/50 rounded animate-pulse" />
                    </td>
                  ))}
                </tr>
              ))
            ) : filtered.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center text-muted text-sm">
                  No jobs match your filters.
                </td>
              </tr>
            ) : (
              filtered.map((job: any) => (
                <tr
                  key={job.id ?? job.job_url}
                  className={`border-b border-border hover:bg-border/20 transition-colors ${
                    job.is_new ? "border-l-2 border-l-accent" : ""
                  }`}
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <span className="text-text-primary font-medium">
                        {job.job_title || <span className="text-muted italic">Unknown</span>}
                      </span>
                      {job.is_urgent && <AlertTriangle size={12} className="text-urgent shrink-0" />}
                    </div>
                    {job.is_new && (
                      <span className="text-[10px] font-mono text-accent">● new</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-text-secondary">{job.hospital_name}</td>
                  <td className="px-4 py-3 text-text-secondary">{job.department || "—"}</td>
                  <td className="px-4 py-3 text-text-secondary">{job.location || "—"}</td>
                  <td className="px-4 py-3">
                    {job.job_type ? (
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${JOB_TYPE_COLORS[job.job_type] || "bg-border text-muted border-border"}`}>
                        {job.job_type}
                      </span>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-3 text-text-secondary max-w-xs">
                    <p className="truncate text-xs">{job.ai_summary || "—"}</p>
                  </td>
                  <td className="px-4 py-3">
                    {job.job_url && (
                      <a href={job.job_url} target="_blank" rel="noopener noreferrer" className="text-muted hover:text-accent transition-colors">
                        <ExternalLink size={13} />
                      </a>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
