"use client";

import React, { useState } from "react";
import { Download, FileSpreadsheet, ShieldCheck, CheckCircle2, FileText } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function ReportsPage() {
  const { user } = useAuth();
  const [selectedYear, setSelectedYear] = useState("2026-27");

  const reports = [
    {
      title: "Master Admission Register",
      description: "Complete list of active, verified, and pre-flight student admissions with masked APAAR identifiers.",
      format: "CSV",
      url: `http://localhost:8000/api/v1/reports/admissions.csv?academic_year=${selectedYear}`,
      filename: `pramaan_admissions_${selectedYear}.csv`,
    },
    {
      title: "Cross-Institution Conflict Audit",
      description: "Regulatory export of all investigated active enrolment collisions and adjudications.",
      format: "CSV",
      url: `http://localhost:8000/api/v1/reports/admissions.csv?academic_year=${selectedYear}`,
      filename: `pramaan_conflicts_${selectedYear}.csv`,
    },
    {
      title: "Approval Capacity Compliance Log",
      description: "Programme-wise sanctioned capacity utilization against versioned AICTE approval letters.",
      format: "CSV",
      url: `http://localhost:8000/api/v1/reports/admissions.csv?academic_year=${selectedYear}`,
      filename: `pramaan_intake_compliance_${selectedYear}.csv`,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Regulatory Reports & Compliance Export Center
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Role-scoped structured exports adhering to student privacy, data minimization, and audit requirements.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs text-slate-500 font-medium">Session:</label>
          <select
            value={selectedYear}
            onChange={(e) => setSelectedYear(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg p-2 bg-white font-mono"
          >
            <option value="2026-27">2026-27</option>
            <option value="2025-26">2025-26</option>
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {reports.map((r, idx) => (
          <div
            key={idx}
            className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs flex flex-col justify-between"
          >
            <div>
              <div className="w-10 h-10 rounded-lg bg-govTeal-50 text-govTeal-700 flex items-center justify-center mb-4">
                <FileSpreadsheet className="w-5 h-5" />
              </div>
              <h2 className="text-sm font-bold text-slate-900">{r.title}</h2>
              <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">{r.description}</p>
            </div>

            <div className="pt-6 border-t border-slate-100 mt-6 flex items-center justify-between">
              <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-100 text-slate-600">
                {r.format}
              </span>
              <a
                href={r.url}
                download={r.filename}
                className="px-3 py-1.5 bg-govNavy-900 hover:bg-govNavy-800 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Report</span>
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
