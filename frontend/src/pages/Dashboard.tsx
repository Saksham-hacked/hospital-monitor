import { useEffect, useState } from "react";
import { fetchSummary, fetchHospitalStats, fetchDepartmentStats, fetchJobs, triggerPipeline } from "../lib/api";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell,
} from "recharts";
import { Zap, TrendingUp, Building2, AlertTriangle, RefreshCw, Sparkles } from "lucide-react";

const ACCENT = "#6ee7b7";
const COLORS = ["#6ee7b7", "#34d399", "#10b981", "#059669", "#047857"];

export default function Dashboard() {
  const [summary, setSummary] = useState<any>(null);
  const [hospitalStats, setHospitalStats] = useState<any[]>([]);
  const [deptStats, setDeptStats] = useState<any[]>([]);
  const [newJobs, setNewJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [triggering, setTriggering] = useState(false);
  const [triggerMsg, setTriggerMsg] = useState("");

  async function loadAll() {
    setLoading(true);
    setError("");
    try {
      const [s, h, d, j] = await Promise.all([
        fetchSummary(),
        fetchHospitalStats(),
        fetchDepartmentStats(),
        fetchJobs(true),
      ]);
      setSummary(s);
      setHospitalStats(h.data || []);
      setDeptStats(d.data || []);
      setNewJobs(j.jobs || []);
    } catch (e) {
      console.error(e);
      setError("Failed to load dashboard data. backend might take 50s to warm up");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { loadAll(); }, []);

  async function handleTrigger() {
    setTriggering(true);
    setTriggerMsg("");
    try {
      const r = await triggerPipeline();
      setTriggerMsg(r.message);
      setTimeout(loadAll, 15000);
    } catch {
      setTriggerMsg("Failed to trigger pipeline.");
    } finally {
      setTriggering(false);
    }
  }

  const stats = summary?.stats || {};

  return (
    <div className="space-y-8 fade-in-up">

      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="font-display text-3xl font-bold text-text-primary tracking-tight">
            Hiring Intelligence
          </h1>
          <p className="text-text-secondary text-sm mt-1">
            Real-time hospital career monitoring · AI-powered trend analysis
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-accent font-mono">
            <span className="w-2 h-2 rounded-full bg-accent live-dot" />
            Live
          </div>
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent/10 border border-accent/20 text-accent text-sm hover:bg-accent/20 transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={triggering ? "animate-spin" : ""} />
            {triggering ? "Running..." : "Run Now"}
          </button>
        </div>
      </div>

      {triggerMsg && (
        <div className="text-xs font-mono text-accent/80 bg-accent/5 border border-accent/10 rounded-lg px-4 py-2">
          {triggerMsg}
        </div>
      )}

      {error && (
        <div className="text-sm text-urgent bg-urgent/10 border border-urgent/20 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {/* Stat Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "New Jobs", value: stats.total_new ?? newJobs.length, icon: Zap, color: "text-accent" },
          { label: "Urgent Roles", value: stats.urgent_count ?? 0, icon: AlertTriangle, color: "text-urgent" },
          { label: "Hospitals Tracked", value: hospitalStats.length, icon: Building2, color: "text-blue-400" },
          { label: "Departments Active", value: deptStats.length, icon: TrendingUp, color: "text-purple-400" },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="bg-surface border border-border rounded-xl p-5">
            <div className={`${color} mb-3`}><Icon size={18} /></div>
            <div className="font-display text-3xl font-bold text-text-primary">
              {loading ? "—" : value}
            </div>
            <div className="text-text-secondary text-xs mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* AI Summary */}
      <div className="bg-surface border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Sparkles size={16} className="text-accent" />
          <span className="font-display font-semibold text-text-primary text-sm tracking-wide uppercase">
            AI Trend Summary
          </span>
          {summary?.created_at && (
            <span className="ml-auto text-xs font-mono text-muted">
              {new Date(summary.created_at).toLocaleTimeString()}
            </span>
          )}
        </div>
        {loading ? (
          <div className="h-16 bg-border/30 rounded-lg animate-pulse" />
        ) : (
          <p className="text-text-secondary text-sm leading-relaxed">
            {summary?.summary || "No summary yet. Trigger a scrape cycle to generate insights."}
          </p>
        )}
      </div>

      {/* Charts */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Hospital Chart */}
        <div className="bg-surface border border-border rounded-xl p-6">
          <h2 className="font-display font-semibold text-text-primary text-sm uppercase tracking-wide mb-5">
            Jobs by Hospital
          </h2>
          {loading ? (
            <div className="h-48 bg-border/30 rounded-lg animate-pulse" />
          ) : hospitalStats.length === 0 ? (
            <p className="text-muted text-sm">No data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={hospitalStats} layout="vertical" margin={{ left: 0 }}>
                <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="hospital" type="category" tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} width={120} />
                <Tooltip
                  contentStyle={{ background: "#111118", border: "1px solid #1e1e2e", borderRadius: 8 }}
                  labelStyle={{ color: "#e2e8f0" }}
                  itemStyle={{ color: ACCENT }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {hospitalStats.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Department Chart */}
        <div className="bg-surface border border-border rounded-xl p-6">
          <h2 className="font-display font-semibold text-text-primary text-sm uppercase tracking-wide mb-5">
            Top Departments
          </h2>
          {loading ? (
            <div className="h-48 bg-border/30 rounded-lg animate-pulse" />
          ) : deptStats.length === 0 ? (
            <p className="text-muted text-sm">No data yet.</p>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={deptStats} layout="vertical">
                <XAxis type="number" tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis dataKey="department" type="category" tick={{ fill: "#94a3b8", fontSize: 11 }} axisLine={false} tickLine={false} width={120} />
                <Tooltip
                  contentStyle={{ background: "#111118", border: "1px solid #1e1e2e", borderRadius: 8 }}
                  labelStyle={{ color: "#e2e8f0" }}
                  itemStyle={{ color: ACCENT }}
                />
                <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                  {deptStats.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* New Jobs Feed */}
      <div className="bg-surface border border-border rounded-xl p-6">
        <h2 className="font-display font-semibold text-text-primary text-sm uppercase tracking-wide mb-5">
          Latest Detections
        </h2>
        {loading ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-12 bg-border/30 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : newJobs.length === 0 ? (
          <p className="text-muted text-sm">No new jobs in this cycle. Trigger a scrape to populate data.</p>
        ) : (
          <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
            {newJobs.slice(0, 20).map((job: any) => (
              <div
                key={job.id ?? job.job_url}
                className="flex items-center justify-between px-4 py-3 rounded-lg border border-border hover:border-accent/30 transition-colors group"
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-text-primary text-sm font-medium truncate">
                      {job.job_title || "Untitled Role"}
                    </span>
                    {job.is_urgent && (
                      <span className="text-[10px] font-mono px-1.5 py-0.5 bg-urgent/10 text-urgent border border-urgent/20 rounded">
                        URGENT
                      </span>
                    )}
                  </div>
                  <div className="text-text-secondary text-xs mt-0.5">
                    {job.hospital_name} · {job.department || "—"} · {job.job_type || "—"}
                  </div>
                </div>
                {job.job_url && (
                  <a
                    href={job.job_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-muted group-hover:text-accent transition-colors ml-4 shrink-0"
                  >
                    View →
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
