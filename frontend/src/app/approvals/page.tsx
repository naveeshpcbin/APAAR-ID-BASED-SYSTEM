"use client";

import React, { useState, useEffect } from "react";
import { Award, ShieldCheck, CheckCircle2, AlertCircle, RefreshCw, Calculator } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function ApprovalsPage() {
  const { user } = useAuth();
  const [approvals, setApprovals] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // Capacity simulator state
  const [simProgrammeId, setSimProgrammeId] = useState<number | null>(null);
  const [simIncomingCount, setSimIncomingCount] = useState(25);
  const [simResult, setSimResult] = useState<any | null>(null);
  const [isSimulating, setIsSimulating] = useState(false);

  useEffect(() => {
    async function loadApprovals() {
      try {
        setLoading(true);
        const res = await apiRequest("/approvals?academic_year=2026-27");
        setApprovals(res);
        if (res.length > 0) {
          setSimProgrammeId(res[0].programme_id);
        }
      } catch (err: any) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadApprovals();
  }, [user]);

  const handleSimulate = async () => {
    if (!simProgrammeId) return;
    setIsSimulating(true);
    try {
      const res = await apiRequest(
        `/approvals/capacity/evaluate?institution_id=${user?.institutionId || 1}&programme_id=${simProgrammeId}&academic_year=2026-27&incoming_count=${simIncomingCount}`
      );
      setSimResult(res);
    } catch (err: any) {
      alert(`Simulation failed: ${err.message}`);
    } finally {
      setIsSimulating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Sanctioned Approvals & Versioned Policy Snapshots
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Programme-wise sanctioned capacity, supernumerary quotas (TFW, EWS), and approval letters for academic session 2026-27.
          </p>
        </div>
        <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
          AICTE Approval Process Handbook 2026
        </span>
      </div>

      {/* Grid: Approvals List & Live Capacity Simulator */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Approvals Table */}
        <div className="lg:col-span-2 bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs space-y-4">
          <h2 className="text-sm font-bold text-slate-900">Active Programme Approvals</h2>

          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
                <tr>
                  <th className="px-4 py-2.5">Programme Code</th>
                  <th className="px-4 py-2.5">Academic Session</th>
                  <th className="px-4 py-2.5">Approved Intake</th>
                  <th className="px-4 py-2.5">Supernumerary Quotas</th>
                  <th className="px-4 py-2.5">Approval Letter Ref</th>
                  <th className="px-4 py-2.5">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {approvals.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50">
                    <td className="px-4 py-2.5 font-bold text-slate-900 font-mono">
                      {a.programme_code}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">{a.academic_year}</td>
                    <td className="px-4 py-2.5 font-bold text-govTeal-700">{a.approved_intake} seats</td>
                    <td className="px-4 py-2.5 font-mono text-slate-600">
                      TFW: {a.supernumerary_quota?.TFW || 0} | EWS: {a.supernumerary_quota?.EWS || 0}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-slate-500 text-[11px]">
                      {a.approval_letter_ref}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                        ACTIVE
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Live Capacity Evaluation Simulator */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-govTeal-600" />
            <h2 className="text-sm font-bold text-slate-900">Intake Capacity Simulator</h2>
          </div>
          <p className="text-xs text-slate-500">
            Simulate incoming batch admissions against versioned intake ceilings to detect overages before submission.
          </p>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-700 font-medium mb-1">Target Programme</label>
              <select
                value={simProgrammeId || ""}
                onChange={(e) => setSimProgrammeId(Number(e.target.value))}
                className="w-full border border-slate-300 rounded-lg p-2 bg-white"
              >
                {approvals.map((a) => (
                  <option key={a.id} value={a.programme_id}>
                    {a.programme_code} (Intake: {a.approved_intake})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-slate-700 font-medium mb-1">
                Proposed Batch Intake (Students)
              </label>
              <input
                type="number"
                value={simIncomingCount}
                onChange={(e) => setSimIncomingCount(Number(e.target.value))}
                className="w-full border border-slate-300 rounded-lg p-2 font-mono"
              />
            </div>

            <button
              onClick={handleSimulate}
              disabled={isSimulating}
              className="w-full py-2 bg-govNavy-900 hover:bg-govNavy-800 text-white rounded-lg font-semibold flex items-center justify-center gap-2 transition"
            >
              {isSimulating ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : "Run Compliance Check"}
            </button>
          </div>

          {/* Simulation Output */}
          {simResult && (
            <div
              className={`p-4 rounded-xl border space-y-2 text-xs ${
                simResult.is_compliant
                  ? "bg-emerald-50/50 border-emerald-200"
                  : "bg-rose-50/50 border-rose-200"
              }`}
            >
              <div className="flex items-center gap-2">
                {simResult.is_compliant ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-rose-600" />
                )}
                <span
                  className={`font-bold ${
                    simResult.is_compliant ? "text-emerald-900" : "text-rose-900"
                  }`}
                >
                  {simResult.is_compliant ? "Intake Capacity Compliant" : "Intake Ceiling Exceeded!"}
                </span>
              </div>
              <div className="text-slate-700 leading-relaxed">{simResult.explanation}</div>
              <div className="pt-2 border-t border-slate-200 grid grid-cols-2 gap-2 font-mono text-[11px] text-slate-600">
                <div>Enrolled: {simResult.current_active}</div>
                <div>Approved: {simResult.approved_intake}</div>
                <div>Projected: {simResult.projected_total}</div>
                <div>Overage: {simResult.overage} seats</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
