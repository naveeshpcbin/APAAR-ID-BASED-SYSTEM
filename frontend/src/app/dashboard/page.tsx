"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import {
  Users,
  ShieldAlert,
  GitCompare,
  TrendingUp,
  AlertCircle,
  ExternalLink,
  ArrowUpRight,
  Activity,
  CheckCircle,
  Clock,
} from "lucide-react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

const CATEGORY_COLORS = ["#0d9488", "#3b82f6", "#f59e0b", "#ec4899", "#8b5cf6"];

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadMetrics() {
      try {
        setLoading(true);
        const res = await apiRequest("/dashboards/metrics?academic_year=2026-27");
        setData(res);
        setError(null);
      } catch (err: any) {
        setError(err.message || "Failed to load dashboard metrics");
      } finally {
        setLoading(false);
      }
    }
    loadMetrics();
  }, [user]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="text-center">
          <div className="inline-block w-8 h-8 border-3 border-govTeal-600 border-t-transparent rounded-full animate-spin mb-2" />
          <p className="text-xs text-slate-500 font-medium">Reconciling live national metrics...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
        <div className="font-semibold flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          Unable to fetch dashboard intelligence
        </div>
        <div className="mt-1 text-xs text-red-600">{error}</div>
      </div>
    );
  }

  const { summary, programme_utilization, category_distribution, recent_audits } = data;

  return (
    <div className="space-y-6">
      {/* Top Banner / Heading */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Regulatory Intelligence & Intake Compliance Overview
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Continuous validation against AICTE Sanctioned Intake, APAAR Identity Registry, and Cross-Institution Boundaries.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Link
            href="/uploads"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-govTeal-600 hover:bg-govTeal-700 text-white text-xs font-semibold rounded-lg shadow-xs transition"
          >
            <span>Smart Uploader</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
          <Link
            href="/verification"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-xs transition"
          >
            <span>Scan QR Receipt</span>
          </Link>
        </div>
      </div>

      {/* 4 Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Total Enrolled */}
        <div className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs hover:border-slate-300 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Active Admissions
            </span>
            <div className="w-8 h-8 rounded-lg bg-teal-50 text-govTeal-700 flex items-center justify-center">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">
              {summary.active_admissions.toLocaleString()}
            </span>
            <span className="text-xs font-medium text-slate-500">
              / {summary.distinct_students} unique APAARs
            </span>
          </div>
          <div className="mt-2 text-[11px] text-slate-500 flex items-center gap-1">
            <span className="text-govTeal-700 font-semibold">{summary.under_review} records</span>{" "}
            in pre-flight review
          </div>
        </div>

        {/* Card 2: Sanctioned Capacity */}
        <div className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs hover:border-slate-300 transition">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Intake Utilization
            </span>
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-slate-900 tracking-tight">
              {summary.intake_utilization_pct}%
            </span>
            <span className="text-xs font-medium text-slate-500">
              of {summary.total_approved_intake.toLocaleString()} seats
            </span>
          </div>
          <div className="mt-2 w-full bg-slate-100 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-govTeal-600 h-1.5 rounded-full"
              style={{ width: `${Math.min(100, summary.intake_utilization_pct)}%` }}
            />
          </div>
        </div>

        {/* Card 3: Cross-Institution Conflicts */}
        <Link
          href="/conflicts"
          className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs hover:border-amber-300 transition block group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Cross-Inst Conflicts
            </span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-700 flex items-center justify-center group-hover:scale-105 transition">
              <GitCompare className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-amber-700 tracking-tight">
              {summary.open_conflicts}
            </span>
            <span className="text-xs font-medium text-slate-500">open cases</span>
          </div>
          <div className="mt-2 text-[11px] text-amber-600 font-medium flex items-center gap-1">
            <span>Dual active enrolment investigations</span>
            <ArrowUpRight className="w-3 h-3" />
          </div>
        </Link>

        {/* Card 4: Anomaly Risk Alerts */}
        <Link
          href="/anomalies"
          className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs hover:border-rose-300 transition block group"
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
              Anomalies Flagged
            </span>
            <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-700 flex items-center justify-center group-hover:scale-105 transition">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-bold text-rose-700 tracking-tight">
              {summary.pending_anomalies}
            </span>
            <span className="text-xs font-medium text-slate-500">review required</span>
          </div>
          <div className="mt-2 text-[11px] text-rose-600 font-medium flex items-center gap-1">
            <span>Statistical & deadline surge signals</span>
            <ArrowUpRight className="w-3 h-3" />
          </div>
        </Link>
      </div>

      {/* Main Visuals Grid: Large Intake Chart + Category Pie */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Intake Utilization by Programme */}
        <div className="lg:col-span-2 bg-white p-4 sm:p-5 rounded-xl border border-slate-200/90 shadow-xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4">
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                Programme Capacity vs. Active Enrolment
              </h2>
              <p className="text-xs text-slate-500">
                Sanctioned Intake versus committed APAAR-verified students by programme (2026-27).
              </p>
            </div>
            <span className="text-xs font-mono font-medium text-slate-500 bg-slate-100 px-2 py-0.5 rounded self-start sm:self-auto">
              AICTE-APH-2026-V1
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={programme_utilization}
                margin={{ top: 10, right: 10, left: -20, bottom: 20 }}
              >
                <XAxis
                  dataKey="programme_code"
                  tick={{ fontSize: 11, fill: "#64748b" }}
                  interval={0}
                />
                <YAxis tick={{ fontSize: 11, fill: "#64748b" }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "none",
                    borderRadius: "8px",
                    color: "#fff",
                    fontSize: "12px",
                  }}
                />
                <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "10px" }} />
                <Bar
                  dataKey="approved_intake"
                  name="Sanctioned Intake"
                  fill="#94a3b8"
                  radius={[4, 4, 0, 0]}
                />
                <Bar
                  dataKey="enrolled"
                  name="Verified Enrolled"
                  fill="#0d9488"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Right 1 Col: Category Distribution */}
        <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-200/90 shadow-xs flex flex-col">
          <div className="mb-2">
            <h2 className="text-sm font-bold text-slate-900">Category Distribution</h2>
            <p className="text-xs text-slate-500">Affirmative action & quota breakdown.</p>
          </div>

          <div className="h-56 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={category_distribution}
                  dataKey="count"
                  nameKey="category"
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={75}
                  paddingAngle={3}
                >
                  {category_distribution.map((entry: any, index: number) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#0f172a",
                    border: "none",
                    borderRadius: "8px",
                    color: "#fff",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="grid grid-cols-2 gap-2 mt-auto pt-3 border-t border-slate-100 text-xs">
            {category_distribution.map((item: any, idx: number) => (
              <div key={item.category} className="flex items-center gap-2">
                <span
                  className="w-2.5 h-2.5 rounded-full shrink-0"
                  style={{ backgroundColor: CATEGORY_COLORS[idx % CATEGORY_COLORS.length] }}
                />
                <span className="text-slate-600 truncate">{item.category}:</span>
                <span className="font-semibold text-slate-900 ml-auto">{item.count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Bottom Row: Priority Action Queue & Live Audit Ledger Stream */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: High-Priority Regulatory Tasks */}
        <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-200/90 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
              <span>High-Priority Adjudication Queue</span>
            </h2>
            <Link
              href="/conflicts"
              className="text-xs text-govTeal-700 hover:text-govTeal-800 font-semibold flex items-center gap-1 shrink-0"
            >
              <span>View All</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-2.5">
            <div className="p-3 rounded-lg border border-amber-200 bg-amber-50/50 flex flex-col sm:flex-row sm:items-start justify-between gap-2">
              <div>
                <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                  <span className="px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 text-[10px] font-mono font-semibold">
                    CONF-2026-0042
                  </span>
                  <span>Cross-Institution Active Enrolment Collision</span>
                </div>
                <div className="text-xs text-slate-600 mt-1">
                  Student Kunal Singhania active at both <strong>COEP Pune</strong> and{" "}
                  <strong>DTU Delhi</strong> for academic session 2026-27.
                </div>
              </div>
              <Link
                href="/conflicts"
                className="px-2.5 py-1 bg-amber-600 hover:bg-amber-700 text-white rounded text-xs font-semibold whitespace-nowrap self-start sm:self-auto"
              >
                Adjudicate
              </Link>
            </div>

            <div className="p-3 rounded-lg border border-rose-200 bg-rose-50/50 flex flex-col sm:flex-row sm:items-start justify-between gap-2">
              <div>
                <div className="text-xs font-bold text-slate-900 flex items-center gap-2">
                  <span className="px-1.5 py-0.5 rounded bg-rose-100 text-rose-800 text-[10px] font-mono font-semibold">
                    ANOM-2026-0019
                  </span>
                  <span>Deadline Intake Concentration Surge</span>
                </div>
                <div className="text-xs text-slate-600 mt-1">
                  89% annual CSE intake uploaded in a single batch within 24 hours of portal closure
                  at <strong>R.V. College of Engineering</strong>.
                </div>
              </div>
              <Link
                href="/anomalies"
                className="px-2.5 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded text-xs font-semibold whitespace-nowrap self-start sm:self-auto"
              >
                Inspect
              </Link>
            </div>
          </div>
        </div>

        {/* Right: Live Cryptographic Audit Stream */}
        <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-200/90 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Activity className="w-4 h-4 text-govTeal-600 shrink-0" />
              <span>Cryptographic Audit Stream</span>
            </h2>
            <Link
              href="/audit"
              className="text-xs text-govTeal-700 hover:text-govTeal-800 font-semibold flex items-center gap-1 shrink-0"
            >
              <span>Verify</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-2">
            {recent_audits.map((a: any) => (
              <div
                key={a.sequence_no}
                className="flex flex-col sm:flex-row sm:items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs gap-1"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] bg-slate-200 text-slate-700 px-1.5 py-0.5 rounded font-semibold shrink-0">
                    #{a.sequence_no}
                  </span>
                  <span className="font-semibold text-slate-800 truncate">{a.action}</span>
                  <span className="text-slate-400">({a.entity_type})</span>
                </div>
                <div className="flex items-center gap-2 text-slate-500 text-[11px]">
                  <span className="truncate">{a.actor_email}</span>
                  <span className="text-slate-400 font-mono shrink-0">{a.created_at}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
