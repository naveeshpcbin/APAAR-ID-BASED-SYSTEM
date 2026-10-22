"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ShieldCheck,
  Send,
  RotateCcw,
  Clock,
  Building2,
  FileSpreadsheet,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function BatchDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { user } = useAuth();
  const batchId = params?.batchId;
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewNotes, setReviewNotes] = useState(
    "Adjudicated and verified against AICTE Approval Process Handbook (APH 2026-27) guidelines."
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const isAdmin = user?.role === "AICTE_ADMIN" || user?.role === "REGIONAL_OFFICER";

  const loadBatch = async () => {
    if (!batchId) return;
    try {
      setLoading(true);
      const res = await apiRequest(`/uploads/${batchId}`);
      setData(res);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadBatch();
  }, [batchId]);

  const handleReviewDecision = async (decision: "APPROVED" | "REJECTED_NEEDS_CORRECTION") => {
    setIsSubmitting(true);
    setActionMessage(null);
    try {
      const res = await apiRequest(`/uploads/${batchId}/review`, {
        method: "POST",
        body: JSON.stringify({
          decision,
          notes: reviewNotes,
        }),
      });
      setActionMessage({
        type: "success",
        text: `Batch #${batchId} status successfully updated to ${res.status}. Recorded in tamper-evident ledger.`,
      });
      await loadBatch();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to submit review decision.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCommitBatch = async () => {
    setIsSubmitting(true);
    setActionMessage(null);
    try {
      const res = await apiRequest(`/uploads/${batchId}/commit`, {
        method: "POST",
        body: JSON.stringify({ skip_errors: true }),
      });
      setActionMessage({
        type: "success",
        text: `Batch #${batchId} committed! Admitted ${res.committed_valid_records} valid records, ${res.quarantined_records} in review.`,
      });
      await loadBatch();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to commit batch.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
        <Clock className="w-5 h-5 animate-spin text-slate-400" />
        <span>Loading batch details & verification ledger...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8 text-center text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-xl">
        Batch #{batchId} not found or access restricted.
      </div>
    );
  }

  const { batch, findings } = data;

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "COMMITTED":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "REJECTED_NEEDS_CORRECTION":
      case "REJECTED":
        return "bg-rose-100 text-rose-800 border-rose-300";
      default:
        return "bg-amber-100 text-amber-800 border-amber-300";
    }
  };

  return (
    <div className="space-y-6">
      {/* Navigation & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <Link
            href="/uploads"
            className="p-1.5 rounded-lg border border-slate-300 hover:bg-slate-100 text-slate-700 transition"
          >
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-slate-900 tracking-tight">
                Batch #{batch.id}: {batch.filename}
              </h1>
              <span
                className={`text-[11px] font-bold uppercase px-2.5 py-0.5 rounded-full border ${getStatusBadge(
                  batch.status
                )}`}
              >
                {batch.status}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Academic Session: <span className="font-semibold text-slate-700">{batch.academic_year}</span> | Target
              Institution: <span className="font-semibold text-slate-700">#{batch.institution_id}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Link
            href="/admissions"
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-medium rounded-lg border border-slate-200 transition"
          >
            View Student Admissions
          </Link>
        </div>
      </div>

      {actionMessage && (
        <div
          className={`p-4 rounded-xl border text-xs flex items-center gap-2 ${
            actionMessage.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}
        >
          {actionMessage.type === "success" ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
          ) : (
            <XCircle className="w-4 h-4 text-rose-600 flex-shrink-0" />
          )}
          <span>{actionMessage.text}</span>
        </div>
      )}

      {/* Metrics Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs">
          <div className="text-xs text-slate-500 font-medium">Total Ingested Rows</div>
          <div className="text-2xl font-bold text-slate-900 mt-1">{batch.total_rows}</div>
        </div>
        <div className="p-4 bg-emerald-50/70 rounded-xl border border-emerald-200 shadow-xs">
          <div className="text-xs text-emerald-700 font-medium">Valid / Pass Records</div>
          <div className="text-2xl font-bold text-emerald-800 mt-1">{batch.valid_rows}</div>
        </div>
        <div className="p-4 bg-amber-50/70 rounded-xl border border-amber-200 shadow-xs">
          <div className="text-xs text-amber-700 font-medium">Warnings / In Review</div>
          <div className="text-2xl font-bold text-amber-800 mt-1">{batch.warning_rows}</div>
        </div>
        <div className="p-4 bg-rose-50/70 rounded-xl border border-rose-200 shadow-xs">
          <div className="text-xs text-rose-700 font-medium">Rejected Syntax Errors</div>
          <div className="text-2xl font-bold text-rose-800 mt-1">{batch.error_rows}</div>
        </div>
      </div>

      {/* AICTE Central Adjudication Section (for Reviewers) */}
      {isAdmin ? (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
            <ShieldCheck className="w-5 h-5 text-govNavy-900" />
            <div>
              <h2 className="text-sm font-bold text-slate-900">AICTE Central Regulatory Review & Adjudication</h2>
              <p className="text-xs text-slate-500">
                Authorized regional regulatory officer decision controls. Decisions are committed to the tamper-evident SHA-256 audit ledger.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <label className="block text-xs font-semibold text-slate-700">
              Reviewer Adjudication Notes & Justification
            </label>
            <textarea
              rows={2}
              value={reviewNotes}
              onChange={(e) => setReviewNotes(e.target.value)}
              className="w-full text-xs p-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-govNavy-500 focus:outline-none"
              placeholder="Enter official review remarks, seat compliance findings, or return justification..."
            />

            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={() => handleReviewDecision("APPROVED")}
                disabled={isSubmitting || batch.status === "APPROVED"}
                className={`px-4 py-2 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition ${
                  batch.status === "APPROVED"
                    ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                    : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs"
                }`}
              >
                <CheckCircle2 className="w-4 h-4" />
                {batch.status === "APPROVED" ? "Batch Already Approved" : "Approve Batch & Release Admissions"}
              </button>

              <button
                onClick={() => handleReviewDecision("REJECTED_NEEDS_CORRECTION")}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-rose-300 text-rose-700 hover:bg-rose-50 flex items-center gap-1.5 transition"
              >
                <RotateCcw className="w-4 h-4" />
                Return to Institution for Correction
              </button>
            </div>
          </div>
        </div>
      ) : (
        batch.status === "PREFLIGHT" && (
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
            <h2 className="text-sm font-bold text-slate-900">Institutional Commit & Ingestion</h2>
            <p className="text-xs text-slate-500">
              Pre-flight validation checks completed. Confirming ingestion will atomically commit verified rows and forward the batch to AICTE Central.
            </p>
            <button
              onClick={handleCommitBatch}
              disabled={isSubmitting}
              className="px-4 py-2 bg-govTeal-600 hover:bg-govTeal-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 transition"
            >
              <Send className="w-4 h-4" />
              Commit Batch & Send to AICTE
            </button>
          </div>
        )
      )}

      {/* Row Findings Table */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">
            Row-Level Findings & Validation Ledger ({findings.length})
          </h2>
          <span className="text-[11px] text-slate-400">Deterministic Rule Engine Evaluation</span>
        </div>

        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
              <tr>
                <th className="px-3 py-2.5">Row</th>
                <th className="px-3 py-2.5">Severity</th>
                <th className="px-3 py-2.5">Rule ID</th>
                <th className="px-3 py-2.5">Target Field</th>
                <th className="px-3 py-2.5">Diagnostic Finding</th>
                <th className="px-3 py-2.5">Actionable Guidance</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {findings.map((f: any) => (
                <tr key={f.id} className="hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono font-bold text-slate-600">#{f.row_index}</td>
                  <td className="px-3 py-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        f.severity === "ERROR"
                          ? "bg-rose-100 text-rose-800"
                          : f.severity === "WARNING"
                          ? "bg-amber-100 text-amber-800"
                          : "bg-blue-100 text-blue-800"
                      }`}
                    >
                      {f.severity}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono text-slate-700 font-medium">{f.rule_id}</td>
                  <td className="px-3 py-2 font-mono text-slate-500">{f.field_name || "—"}</td>
                  <td className="px-3 py-2 text-slate-900">{f.message}</td>
                  <td className="px-3 py-2 text-slate-500">{f.recommended_action || "—"}</td>
                </tr>
              ))}
              {findings.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                    No validation findings recorded. Clean submission.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
