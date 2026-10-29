"use client";

import React, { useState, useEffect } from "react";
import {
  GitCompare,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Building2,
  Calendar,
  User,
  ShieldCheck,
  RefreshCw,
  ArrowRight,
  ExternalLink,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function ConflictsPage() {
  const { user } = useAuth();
  const [conflicts, setConflicts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<any | null>(null);
  const [resolutionStatus, setResolutionStatus] = useState("RESOLVED_VALID");
  const [winningRecordId, setWinningRecordId] = useState<number | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadConflicts = async () => {
    try {
      setLoading(true);
      const res = await apiRequest("/conflicts");
      setConflicts(res);
      if (res.length > 0 && !selectedCase) {
        setSelectedCase(res[0]);
        setWinningRecordId(res[0].record_a_id);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConflicts();
  }, [user]);

  const handleResolve = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase) return;

    setIsSubmitting(true);
    setFeedback(null);
    try {
      await apiRequest(`/conflicts/${selectedCase.id}/resolve`, {
        method: "POST",
        body: JSON.stringify({
          resolution_status: resolutionStatus,
          winning_record_id: winningRecordId,
          resolution_notes: resolutionNotes || "Adjudicated based on regulatory verification.",
        }),
      });
      setFeedback(`Case ${selectedCase.case_number} successfully resolved as ${resolutionStatus}!`);
      await loadConflicts();
    } catch (err: any) {
      setFeedback(`Error: ${err.message}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Cross-Institution Conflict Investigation & Case Management
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Adjudicate overlapping active admissions, dual technical enrolment disputes, and legitimate transfer transitions.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-amber-100 text-amber-800 border border-amber-200">
            {conflicts.filter((c) => c.status === "OPEN").length} Open Cases Pending
          </span>
        </div>
      </div>

      {feedback && (
        <div className="p-4 bg-slate-900 text-white rounded-xl text-xs flex items-center justify-between">
          <span>{feedback}</span>
          <button onClick={() => setFeedback(null)} className="text-slate-400 hover:text-white">
            &times;
          </button>
        </div>
      )}

      {/* Main Grid: Left Cases List, Right Comparison Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cases List */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs space-y-3">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Conflict Cases
          </h2>

          <div className="space-y-2">
            {conflicts.map((c) => (
              <div
                key={c.id}
                onClick={() => {
                  setSelectedCase(c);
                  setWinningRecordId(c.record_a_id);
                }}
                className={`p-3 rounded-lg border text-xs cursor-pointer transition ${
                  selectedCase?.id === c.id
                    ? "bg-slate-900 text-white border-slate-900 shadow-xs"
                    : "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-800"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono font-bold">{c.case_number}</span>
                  <span
                    className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase ${
                      c.status === "OPEN"
                        ? "bg-amber-400 text-slate-950 font-bold"
                        : "bg-emerald-500 text-white"
                    }`}
                  >
                    {c.status}
                  </span>
                </div>
                <div className="font-semibold truncate">
                  Student: {c.student?.full_name || "Unknown"}
                </div>
                <div
                  className={`text-[11px] truncate mt-0.5 ${
                    selectedCase?.id === c.id ? "text-slate-300" : "text-slate-500"
                  }`}
                >
                  {c.record_a?.institution_name} vs. {c.record_b?.institution_name}
                </div>
              </div>
            ))}
            {conflicts.length === 0 && !loading && (
              <div className="p-4 text-center text-slate-400 text-xs">
                No active conflicts detected.
              </div>
            )}
          </div>
        </div>

        {/* Adjudication Workspace */}
        {selectedCase ? (
          <div className="lg:col-span-2 space-y-6">
            {/* Case Overview Card */}
            <div className="bg-white p-4 sm:p-5 rounded-xl border border-slate-200/90 shadow-xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">
                      Case #{selectedCase.case_number}
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 uppercase">
                      {selectedCase.conflict_type}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Flagged by Explainable Admission Reconciliation Engine
                  </p>
                </div>
                <div className="text-left sm:text-right text-xs">
                  <div className="text-slate-400">Student APAAR:</div>
                  <div className="font-mono font-bold text-slate-800">
                    {selectedCase.student?.apaar_masked}
                  </div>
                </div>
              </div>

              {/* Side-by-Side College Record Comparison */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Record A */}
                <div
                  className={`p-4 rounded-xl border transition ${
                    winningRecordId === selectedCase.record_a_id
                      ? "border-govTeal-500 bg-govTeal-50/30 ring-1 ring-govTeal-500"
                      : "border-slate-200 bg-slate-50/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-500 uppercase">
                      Claim A (Prior Enrolment)
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
                      Record #{selectedCase.record_a_id}
                    </span>
                  </div>
                  <div className="text-sm font-bold text-slate-900">
                    {selectedCase.record_a?.institution_name}
                  </div>
                  <div className="text-xs font-semibold text-govTeal-700 mt-0.5">
                    {selectedCase.record_a?.programme_name} ({selectedCase.record_a?.programme_code})
                  </div>

                  <div className="mt-3 space-y-1 text-xs text-slate-600">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Enrollment No:</span>
                      <span className="font-mono">{selectedCase.record_a?.enrollment_no}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Quota / Category:</span>
                      <span>
                        {selectedCase.record_a?.admission_quota} / {selectedCase.record_a?.category}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Admission Date:</span>
                      <span>{selectedCase.record_a?.admission_date}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Status:</span>
                      <span className="font-semibold text-emerald-700">
                        {selectedCase.record_a?.status}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setWinningRecordId(selectedCase.record_a_id)}
                    className={`mt-4 w-full py-1.5 rounded-lg text-xs font-semibold transition ${
                      winningRecordId === selectedCase.record_a_id
                        ? "bg-govTeal-600 text-white"
                        : "bg-white border border-slate-300 text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    {winningRecordId === selectedCase.record_a_id
                      ? "Selected as Valid Enrolment"
                      : "Select Record A as Valid"}
                  </button>
                </div>

                {/* Record B */}
                <div
                  className={`p-4 rounded-xl border transition ${
                    winningRecordId === selectedCase.record_b_id
                      ? "border-govTeal-500 bg-govTeal-50/30 ring-1 ring-govTeal-500"
                      : "border-slate-200 bg-slate-50/50"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold text-slate-500 uppercase">
                      Claim B (Concurrent Enrolment)
                    </span>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-200 text-slate-700">
                      Record #{selectedCase.record_b_id}
                    </span>
                  </div>
                  <div className="text-sm font-bold text-slate-900">
                    {selectedCase.record_b?.institution_name}
                  </div>
                  <div className="text-xs font-semibold text-govTeal-700 mt-0.5">
                    {selectedCase.record_b?.programme_name} ({selectedCase.record_b?.programme_code})
                  </div>

                  <div className="mt-3 space-y-1 text-xs text-slate-600">
                    <div className="flex justify-between">
                      <span className="text-slate-400">Enrollment No:</span>
                      <span className="font-mono">{selectedCase.record_b?.enrollment_no}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Quota / Category:</span>
                      <span>
                        {selectedCase.record_b?.admission_quota} / {selectedCase.record_b?.category}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Admission Date:</span>
                      <span>{selectedCase.record_b?.admission_date}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-slate-400">Status:</span>
                      <span className="font-semibold text-amber-700">
                        {selectedCase.record_b?.status}
                      </span>
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setWinningRecordId(selectedCase.record_b_id)}
                    className={`mt-4 w-full py-1.5 rounded-lg text-xs font-semibold transition ${
                      winningRecordId === selectedCase.record_b_id
                        ? "bg-govTeal-600 text-white"
                        : "bg-white border border-slate-300 text-slate-700 hover:bg-slate-100"
                    }`}
                  >
                    {winningRecordId === selectedCase.record_b_id
                      ? "Selected as Valid Enrolment"
                      : "Select Record B as Valid"}
                  </button>
                </div>
              </div>

              {/* Regulatory Action Decision Form */}
              <form onSubmit={handleResolve} className="pt-4 border-t border-slate-100 space-y-4">
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                  Adjudication Decision
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      Adjudication Verdict
                    </label>
                    <select
                      value={resolutionStatus}
                      onChange={(e) => setResolutionStatus(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-lg p-2 bg-white"
                    >
                      <option value="RESOLVED_VALID">Confirm Valid (Adjudicate Winning Seat)</option>
                      <option value="RESOLVED_CANCELLED">Cancel Duplicate Submission</option>
                      <option value="ESCALATED">Escalate to Regional Hearing Committee</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-medium text-slate-700 mb-1">
                      Regulatory Findings & Justification
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Migration certificate verified; previous seat cancelled."
                      value={resolutionNotes}
                      onChange={(e) => setResolutionNotes(e.target.value)}
                      className="w-full text-xs border border-slate-300 rounded-lg p-2 bg-white"
                    />
                  </div>
                </div>

                <div className="flex flex-col sm:flex-row justify-end gap-3 pt-2">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full sm:w-auto px-5 py-2 bg-govNavy-900 hover:bg-govNavy-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center justify-center gap-2 transition"
                  >
                    {isSubmitting ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Applying Adjudication...</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-4 h-4 text-govTeal-400" />
                        <span>Execute Adjudication & Append to Hash Chain</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>
          </div>
        ) : (
          <div className="lg:col-span-2 bg-white p-12 rounded-xl border border-slate-200 text-center text-slate-400 text-xs">
            Select a conflict case on the left to inspect side-by-side college claims.
          </div>
        )}
      </div>
    </div>
  );
}
