import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import JobsTable from "./pages/JobsTable";
import { Activity, Table2, Stethoscope } from "lucide-react";

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen flex flex-col">
        {/* Navbar */}
        <nav className="border-b border-border px-6 py-4 flex items-center justify-between sticky top-0 z-50 bg-bg/80 backdrop-blur">
          <div className="flex items-center gap-2">
            <Stethoscope className="text-accent" size={20} />
            <span className="font-display text-lg font-bold tracking-tight text-text-primary">
              CareerPulse
            </span>
            <span className="text-xs font-mono text-muted ml-1">/ hospital monitor</span>
          </div>
          <div className="flex items-center gap-1">
            <NavLink
              to="/"
              end
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-accent/10 text-accent"
                    : "text-text-secondary hover:text-text-primary"
                }`
              }
            >
              <Activity size={14} />
              Dashboard
            </NavLink>
            <NavLink
              to="/jobs"
              className={({ isActive }) =>
                `flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm transition-colors ${
                  isActive
                    ? "bg-accent/10 text-accent"
                    : "text-text-secondary hover:text-text-primary"
                }`
              }
            >
              <Table2 size={14} />
              All Jobs
            </NavLink>
          </div>
        </nav>

        {/* Page content */}
        <main className="flex-1 px-6 py-8 max-w-7xl mx-auto w-full">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/jobs" element={<JobsTable />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
