"use client";

import React, { useState, useEffect } from "react";
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  Building2,
  Calendar,
  Search,
  Filter,
  Check,
  Flag,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function AnomaliesPage() {
  const { user } = useAuth();
  const [anomalies, setAnomalies] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCase, setSelectedCase] = useState<any | null>(null);
  const [reviewNotes, setReviewNotes] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);

  const loadAnomalies = async () => {
    try {
      setLoading(true);
      const res = await apiRequest("/anomalies");
      setAnomalies(res);
      if (res.length > 0 && !selectedCase) {
        setSelectedCase(res[0]);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnomalies();
  }, [user]);

  const handleUpdateStatus = async (newStatus: "INSPECTED_CLEARED" | "ESCALATED_AUDIT") => {
    if (!selectedCase) return;
    setIsUpdating(true);
    setFeedback(null);
    try {
      await apiRequest(`/anomalies/${selectedCase.id}/review`, {
        method: "POST",
        body: JSON.stringify({
          status: newStatus,
          review_notes: reviewNotes || `Case marked as ${newStatus} by regulatory officer.`,
        }),
      });
      setFeedback(`Anomaly ${selectedCase.case_number} successfully updated to ${newStatus}.`);
      await loadAnomalies();
    } catch (err: any) {
      setFeedback(`Error: ${err.message}`);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Explainable Regulatory Anomaly Detection Queue
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Transparent statistical signals, intake surges, reservation skew, and timeline clustering flags.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-2.5 py-1 rounded bg-rose-100 text-rose-800 border border-rose-200">
            {anomalies.filter((a) => a.status === "PENDING_REVIEW").length} Pending Investigations
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

      {/* Grid: Left Queue, Right Explanation Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Cases List */}
        <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs space-y-3">
          <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Flagged Cases
          </h2>

          <div className="space-y-2">
            {anomalies.map((a) => (
              <div
                key={a.id}
                onClick={() => setSelectedCase(a)}
                className={`p-3 rounded-lg border text-xs cursor-pointer transition ${
                  selectedCase?.id === a.id
                    ? "bg-slate-900 text-white border-slate-900 shadow-xs"
                    : "bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-800"
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono font-bold">{a.case_number}</span>
                  <span
                    className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                      a.risk_score >= 80
                        ? "bg-rose-500 text-white"
                        : a.risk_score >= 60
                        ? "bg-amber-500 text-slate-950 font-bold"
                        : "bg-blue-500 text-white"
                    }`}
                  >
                    Risk: {a.risk_score}
                  </span>
                </div>
                <div className="font-semibold truncate">{a.anomaly_type}</div>
                <div
                  className={`text-[11px] truncate mt-0.5 ${
                    selectedCase?.id === a.id ? "text-slate-300" : "text-slate-500"
                  }`}
                >
                  {a.institution_name}
                </div>
              </div>
            ))}
            {anomalies.length === 0 && !loading && (
              <div className="p-4 text-center text-slate-400 text-xs">
                No active anomalies detected.
              </div>
            )}
          </div>
        </div>

        {/* Detailed Explanation Panel */}
        {selectedCase ? (
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white p-4 sm:p-6 rounded-xl border border-slate-200/90 shadow-xs space-y-5">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">
                      {selectedCase.case_number}
                    </span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-rose-100 text-rose-800 uppercase">
                      {selectedCase.anomaly_type}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-0.5">
                    Institution: <strong>{selectedCase.institution_name}</strong> | Academic Session:{" "}
                    {selectedCase.academic_year}
                  </div>
                </div>

                <div className="text-left sm:text-right">
                  <div className="text-xs text-slate-400">Calculated Risk Score:</div>
                  <div className="text-2xl font-bold text-rose-700 tracking-tight">
                    {selectedCase.risk_score}
                    <span className="text-xs text-slate-400">/100</span>
                  </div>
                </div>
              </div>

              {/* The 6 Core Regulatory Answers */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-xs font-bold text-slate-500 uppercase mb-1">
                    1. Detected Statistical Pattern
                  </div>
                  <div className="text-xs font-semibold text-slate-900">
                    {selectedCase.anomaly_type.replace(/_/g, " ")}
                  </div>
                  <div className="text-xs text-slate-600 mt-1">
                    Anomalous deviation in upload timing, quota proportion, or capacity threshold.
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
                  <div className="text-xs font-bold text-slate-500 uppercase mb-1">
                    2. Supporting Metrics & Signals
                  </div>
                  <pre className="text-[11px] font-mono bg-white p-2 rounded border border-slate-200 text-slate-800 overflow-x-auto">
                    {JSON.stringify(selectedCase.signals_json, null, 2)}
                  </pre>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 md:col-span-2">
                  <div className="text-xs font-bold text-slate-500 uppercase mb-1">
                    3. Regulatory Officer Explanation & Rationale
                  </div>
                  <div className="text-xs text-slate-800 leading-relaxed bg-white p-3 rounded-lg border border-slate-200">
                    {selectedCase.explanation}
                  </div>
                </div>
              </div>

              {/* Status and Action Panel */}
              <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="text-xs text-slate-400">Current Status:</div>
                  <span
                    className={`inline-block mt-0.5 px-2 py-0.5 rounded text-xs font-bold uppercase ${
                      selectedCase.status === "PENDING_REVIEW"
                        ? "bg-amber-100 text-amber-800"
                        : selectedCase.status === "INSPECTED_CLEARED"
                        ? "bg-emerald-100 text-emerald-800"
                        : "bg-rose-100 text-rose-800"
                    }`}
                  >
                    {selectedCase.status}
                  </span>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={() => handleUpdateStatus("INSPECTED_CLEARED")}
                    disabled={isUpdating}
                    className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition"
                  >
                    <Check className="w-3.5 h-3.5" />
                    <span>Clear as Compliant</span>
                  </button>

                  <button
                    onClick={() => handleUpdateStatus("ESCALATED_AUDIT")}
                    disabled={isUpdating}
                    className="px-3.5 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition"
                  >
                    <Flag className="w-3.5 h-3.5" />
                    <span>Escalate to Formal Audit</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="lg:col-span-2 bg-white p-12 rounded-xl border border-slate-200 text-center text-slate-400 text-xs">
            Select an anomaly case on the left to inspect its explainable signals.
          </div>
        )}
      </div>
    </div>
  );
}
