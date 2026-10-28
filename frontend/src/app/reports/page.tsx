"use client";

import React, { useState, useEffect } from "react";
import { Download, FileSpreadsheet, ShieldCheck, CheckCircle2, AlertCircle, RefreshCw, BarChart3, Users, Award } from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { downloadFileWithAuth, apiRequest } from "@/lib/api";

export default function ReportsPage() {
  const { user } = useAuth();
  const [selectedYear, setSelectedYear] = useState("2026-27");
  const [downloadingIdx, setDownloadingIdx] = useState<number | null>(null);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [summaryData, setSummaryData] = useState<any | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);

  useEffect(() => {
    async function loadSummary() {
      try {
        setLoadingSummary(true);
        const data = await apiRequest(`/reports/summary?academic_year=${selectedYear}`);
        setSummaryData(data);
      } catch (err: any) {
        console.error("Failed to load reports summary:", err);
      } finally {
        setLoadingSummary(false);
      }
    }
    loadSummary();
  }, [user, selectedYear]);

  const reports = [
    {
      title: "Master Admission Register",
      description: "Complete list of active, verified student admissions with masked APAAR academic identifiers, category quotas, and nationality types.",
      format: "CSV",
      endpoint: `/reports/admissions.csv?academic_year=${selectedYear}`,
      filename: `pramaan_admissions_${selectedYear}.csv`,
      badge: "SIH-R1, R2, R10",
      icon: Users,
    },
    {
      title: "Cross-Institution Conflict Audit",
      description: "Authoritative regulatory audit of investigated multi-institution student enrolment collisions, flagged APAAR disputes, and resolution status.",
      format: "CSV",
      endpoint: `/reports/conflicts.csv`,
      filename: `pramaan_cross_institution_conflicts_${selectedYear}.csv`,
      badge: "SIH-R3, R5",
      icon: ShieldCheck,
    },
    {
      title: "Approval Capacity Compliance Log",
      description: "Programme-level sanctioned intake utilization against AICTE approval letter references, supernumerary quotas (TFW, EWS), and threshold compliance.",
      format: "CSV",
      endpoint: `/reports/compliance.csv?academic_year=${selectedYear}`,
      filename: `pramaan_intake_compliance_${selectedYear}.csv`,
      badge: "SIH-R2, R9",
      icon: Award,
    },
  ];

  const handleDownload = async (idx: number, endpoint: string, filename: string) => {
    try {
      setDownloadingIdx(idx);
      setMessage(null);
      await downloadFileWithAuth(endpoint, filename);
      setMessage({
        type: "success",
        text: `Successfully exported and downloaded ${filename}!`,
      });
    } catch (err: any) {
      setMessage({
        type: "error",
        text: err.message || "Failed to download regulatory report.",
      });
    } finally {
      setDownloadingIdx(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Regulatory Reports & Compliance Export Center
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Role-scoped structured exports adhering to student privacy, data minimization (DPDP Act 2023), and AICTE audit requirements.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-500 font-medium">Session:</label>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg p-2 bg-white font-mono shadow-xs focus:ring-1 focus:ring-govTeal-500"
          >
            <option value="2026-27">2026-27</option>
            <option value="2025-26">2025-26</option>
          </select>
        </div>
      </div>

      {/* Feedback Banner */}
      {message && (
        <div
          className={`p-3.5 rounded-xl text-xs flex items-center justify-between shadow-xs ${
            message.type === "success"
              ? "bg-emerald-50 text-emerald-800 border border-emerald-200"
              : "bg-rose-50 text-rose-800 border border-rose-200"
          }`}
        >
          <div className="flex items-center gap-2">
            {message.type === "success" ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            )}
            <span className="font-medium">{message.text}</span>
          </div>
          <button
            onClick={() => setMessage(null)}
            className="text-xs font-bold px-1.5 py-0.5 rounded hover:bg-black/5"
          >
            &times;
          </button>
        </div>
      )}

      {/* Summary KPI Strip */}
      {summaryData && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 p-4 bg-slate-900 text-white rounded-xl shadow-xs">
          <div>
            <div className="text-[10px] font-mono uppercase text-slate-400">Total Enrolment</div>
            <div className="text-lg font-bold text-white font-mono mt-0.5">{summaryData.total_admissions}</div>
          </div>
          <div>
            <div className="text-[10px] font-mono uppercase text-slate-400">Approved Sanctioned</div>
            <div className="text-lg font-bold text-govTeal-400 font-mono mt-0.5">{summaryData.total_approved_intake}</div>
          </div>
          <div>
            <div className="text-[10px] font-mono uppercase text-slate-400">Intake Utilization</div>
            <div className="text-lg font-bold text-emerald-400 font-mono mt-0.5">{summaryData.capacity_utilization_pct}%</div>
          </div>
          <div>
            <div className="text-[10px] font-mono uppercase text-slate-400">Active Conflicts</div>
            <div className="text-lg font-bold text-amber-400 font-mono mt-0.5">{summaryData.open_conflicts_pending}</div>
          </div>
        </div>
      )}

      {/* Report Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {reports.map((r, idx) => {
          const Icon = r.icon;
          const isDownloading = downloadingIdx === idx;
          return (
            <div
              key={idx}
              className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between hover:border-slate-300 transition"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg bg-teal-50 text-govTeal-700 flex items-center justify-center">
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
                    {r.badge}
                  </span>
                </div>
                <h2 className="text-sm font-bold text-slate-900">{r.title}</h2>
                <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{r.description}</p>
              </div>

              <div className="pt-6 border-t border-slate-100 mt-6 flex items-center justify-between">
                <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                  {r.format}
                </span>
                <button
                  type="button"
                  onClick={() => handleDownload(idx, r.endpoint, r.filename)}
                  disabled={isDownloading}
                  className="px-3 py-1.5 bg-govNavy-900 hover:bg-govNavy-800 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition disabled:opacity-50 cursor-pointer"
                >
                  {isDownloading ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Exporting...</span>
                    </>
                  ) : (
                    <>
                      <Download className="w-3.5 h-3.5" />
                      <span>Download Report</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
