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
  RefreshCw,
  GitCompare,
  Database,
  History,
  Info,
  Edit2,
  Save,
  X,
  HelpCircle,
  MessageSquare,
  Sparkles,
  ChevronDown,
  ChevronUp,
  FileDown,
  Download
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
  const [stagedRows, setStagedRows] = useState<any[]>([]);
  const [disputeQueries, setDisputeQueries] = useState<any[]>([]);
  const [loadingRows, setLoadingRows] = useState(true);

  // Review & Action state
  const [reviewNotes, setReviewNotes] = useState(
    "Adjudicated and verified against AICTE Approval Process Handbook (APH 2026-27) guidelines."
  );
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isRevalidating, setIsRevalidating] = useState(false);
  const [actionMessage, setActionMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // In-Browser Spreadsheet Inline Edit state
  const [editingRowId, setEditingRowId] = useState<number | null>(null);
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});
  const [isSavingRow, setIsSavingRow] = useState(false);
  const [expandedAdviceRowId, setExpandedAdviceRowId] = useState<number | null>(null);

  // Exemption / Message to AICTE Modal state
  const [isExemptionModalOpen, setIsExemptionModalOpen] = useState(false);
  const [exemptionRow, setExemptionRow] = useState<any | null>(null);
  const [exemptionCategory, setExemptionCategory] = useState("MISSING_APAAR_UIDAI_FAIL");
  const [exemptionSubject, setExemptionSubject] = useState("");
  const [exemptionMessage, setExemptionMessage] = useState("");
  const [isSubmittingExemption, setIsSubmittingExemption] = useState(false);

  // Central Exemption Resolution state
  const [resolvingQueryId, setResolvingQueryId] = useState<number | null>(null);
  const [resolutionReply, setResolutionReply] = useState(
    "Provisional admission exemption granted under AICTE Approval Process Handbook (APH 2026-27 Section 4.2). Institution must verify student credentials before end semester exams."
  );

  // AICTE Central Advisory / "Give an Idea" state
  const [advisories, setAdvisories] = useState<any[]>([]);
  const [isAdvisoryModalOpen, setIsAdvisoryModalOpen] = useState(false);
  const [advisoryTitle, setAdvisoryTitle] = useState("Remap Unapproved Programme BTECH-AI to Approved BTECH-CSE Cluster");
  const [advisoryDescription, setAdvisoryDescription] = useState(
    "Under AICTE Approval Process Handbook (APH 2026-27) Clause 4.2, emerging area specializations in Artificial Intelligence may be accommodated under the parent Computer Science & Engineering intake cluster. Institution is advised to remap students to BTECH-CSE to achieve regulatory compliance."
  );
  const [advisoryType, setAdvisoryType] = useState("PROGRAMME_REMAP_RECOMMENDATION");
  const [advisoryFromCode, setAdvisoryFromCode] = useState("BTECH-AI");
  const [advisoryToCode, setAdvisoryToCode] = useState("BTECH-CSE");
  const [isSubmittingAdvisory, setIsSubmittingAdvisory] = useState(false);
  const [isApplyingAdvisoryId, setIsApplyingAdvisoryId] = useState<number | null>(null);

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

  const handleDownloadBatch = (format: "xlsx" | "csv" = "xlsx") => {
    window.open(`http://127.0.0.1:8000/api/v1/uploads/${batchId}/download?format=${format}`, "_blank");
  };

  const loadStagedRowsAndQueries = async () => {
    if (!batchId) return;
    try {
      setLoadingRows(true);
      const [rowsRes, queriesRes, advisoriesRes] = await Promise.all([
        apiRequest(`/uploads/${batchId}/rows`),
        apiRequest(`/uploads/${batchId}/queries`),
        apiRequest(`/uploads/${batchId}/advisories`).catch(() => [])
      ]);
      setStagedRows(rowsRes.rows || []);
      setDisputeQueries(queriesRes || []);
      setAdvisories(advisoriesRes || []);
    } catch (err: any) {
      console.error("Failed to load staged rows, queries or advisories:", err);
    } finally {
      setLoadingRows(false);
    }
  };

  const handleCreateAdvisory = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmittingAdvisory(true);
    setActionMessage(null);
    try {
      const payload: any = {
        title: advisoryTitle,
        idea_description: advisoryDescription,
        advisory_type: advisoryType,
        recommended_action: {
          action: "REMAP_PROGRAMME",
          from_code: advisoryFromCode,
          to_code: advisoryToCode
        }
      };
      await apiRequest(`/uploads/${batchId}/advisories`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
      setActionMessage({
        type: "success",
        text: `Official AICTE Advisory / Guidance Idea successfully dispatched to institution!`
      });
      setIsAdvisoryModalOpen(false);
      await loadStagedRowsAndQueries();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to create advisory."
      });
    } finally {
      setIsSubmittingAdvisory(false);
    }
  };

  const handleApplyAdvisory = async (advisoryId: number) => {
    setIsApplyingAdvisoryId(advisoryId);
    setActionMessage(null);
    try {
      const res = await apiRequest(`/uploads/${batchId}/advisories/${advisoryId}/apply`, {
        method: "POST"
      });
      setActionMessage({
        type: "success",
        text: res.message || "AICTE Central Advisory applied! Batch re-evaluated."
      });
      await loadBatch();
      await loadStagedRowsAndQueries();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to apply advisory."
      });
    } finally {
      setIsApplyingAdvisoryId(null);
    }
  };

  useEffect(() => {
    loadBatch();
    loadStagedRowsAndQueries();
  }, [batchId]);

  // Central Regulator Decision
  const handleReviewDecision = async (decision: "APPROVED" | "RETURNED_FOR_CORRECTION" | "REJECTED") => {
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
      await loadStagedRowsAndQueries();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to submit review decision.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Institutional Commit & Submit
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
        text: `Batch #${batchId} committed and submitted to AICTE Central Review! Status: ${res.status}.`,
      });
      await loadBatch();
      await loadStagedRowsAndQueries();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to commit batch.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  // Trigger Revalidation
  const handleTriggerRevalidation = async () => {
    setIsRevalidating(true);
    setActionMessage(null);
    try {
      const res = await apiRequest(`/reference-data/revalidate/${batchId}`, {
        method: "POST"
      });
      setActionMessage({
        type: "success",
        text: `Dynamic revalidation run #${res.run_number} completed against live database reference state!`,
      });
      await loadBatch();
      await loadStagedRowsAndQueries();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to execute revalidation.",
      });
    } finally {
      setIsRevalidating(false);
    }
  };

  // Start Inline Editing a Row
  const handleStartEdit = (row: any) => {
    setEditingRowId(row.id);
    setEditedValues({
      apaar_id: row.apaar_id || "",
      student_name: row.student_name || "",
      programme_code: row.programme_code || "",
      category: row.category || "OPEN",
      gender: row.gender || "MALE",
      admission_quota: row.admission_quota || "STATE_GOVT",
      dob: row.dob || ""
    });
  };

  const handleCancelEdit = () => {
    setEditingRowId(null);
    setEditedValues({});
  };

  // Save Inline Row Edit & Trigger Real-Time Algorithm Re-Evaluation
  const handleSaveRow = async (rowId: number) => {
    setIsSavingRow(true);
    setActionMessage(null);
    try {
      const res = await apiRequest(`/uploads/${batchId}/rows/${rowId}`, {
        method: "PATCH",
        body: JSON.stringify(editedValues)
      });
      setActionMessage({
        type: "success",
        text: `Row #${res.staged_row.row_index} updated and re-validated by Python algorithms in real time! Status: ${res.staged_row.status}.`
      });
      setEditingRowId(null);
      setEditedValues({});
      await loadBatch();
      await loadStagedRowsAndQueries();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to update row."
      });
    } finally {
      setIsSavingRow(false);
    }
  };

  // Open Exemption / Dispute Dialog
  const handleOpenExemption = (row: any) => {
    setExemptionRow(row);
    setExemptionCategory("MISSING_APAAR_UIDAI_FAIL");
    setExemptionSubject(`APAAR Exemption Request for ${row.student_name || `Row #${row.row_index}`}`);
    setExemptionMessage(
      `Student ${row.student_name || "candidate"} currently lacks an APAAR ID due to technical UIDAI biometric synchronization delays at the state enrolment center. We request provisional admission exemption under AICTE Approval Process Handbook (APH 2026-27).`
    );
    setIsExemptionModalOpen(true);
  };

  // Submit Institutional Query / Exemption to AICTE Central
  const handleSubmitExemption = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!exemptionRow) return;
    setIsSubmittingExemption(true);
    try {
      await apiRequest(`/uploads/${batchId}/queries`, {
        method: "POST",
        body: JSON.stringify({
          row_id: exemptionRow.id,
          subject: exemptionSubject,
          category: exemptionCategory,
          student_identifier: exemptionRow.student_name || exemptionRow.apaar_id,
          message: exemptionMessage
        })
      });
      setActionMessage({
        type: "success",
        text: `Exemption request for ${exemptionRow.student_name || `Row #${exemptionRow.row_index}`} sent to AICTE Central Review! Status: EXEMPTION_REQUESTED.`
      });
      setIsExemptionModalOpen(false);
      setExemptionRow(null);
      await loadBatch();
      await loadStagedRowsAndQueries();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to submit exemption request."
      });
    } finally {
      setIsSubmittingExemption(false);
    }
  };

  // AICTE Central Regulator Resolves Exemption Query
  const handleResolveQuery = async (queryId: number, action: "APPROVE_EXEMPTION" | "REJECT_QUERY") => {
    try {
      const res = await apiRequest(`/uploads/${batchId}/queries/${queryId}/resolve`, {
        method: "PATCH",
        body: JSON.stringify({
          action,
          reply_message: resolutionReply
        })
      });
      setActionMessage({
        type: "success",
        text: `Query #${queryId} successfully resolved (${res.status})! Batch disposition refreshed.`
      });
      setResolvingQueryId(null);
      await loadBatch();
      await loadStagedRowsAndQueries();
    } catch (err: any) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to resolve query."
      });
    }
  };

  if (loading) {
    return (
      <div className="p-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
        <Clock className="w-5 h-5 animate-spin text-slate-400" />
        <span>Loading batch details & live database reconciliation ledger...</span>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="max-w-md mx-auto my-12 p-8 text-center bg-white border border-rose-200 rounded-2xl shadow-lg space-y-4">
        <div className="w-12 h-12 bg-rose-50 border border-rose-200 text-rose-600 rounded-xl flex items-center justify-center mx-auto">
          <ShieldCheck className="w-6 h-6 text-rose-600" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-900">Access Restricted: Institutional Isolation</h3>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            One institution&apos;s record does not exist in another institution. Batch #{batchId} belongs to another institution and cannot be accessed under your current institutional nodal login.
          </p>
        </div>
        <Link
          href="/uploads"
          className="inline-flex items-center justify-center px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition"
        >
          Return to My Institution&apos;s Batches
        </Link>
      </div>
    );
  }

  const { batch, findings, latest_validation_run, validation_runs_history } = data;

  // Strict Institutional Tenant Isolation: Prevent cross-institution access
  if (
    user?.role === "INSTITUTION_NODAL" &&
    user?.institutionId &&
    batch?.institution_id &&
    batch.institution_id !== user.institutionId
  ) {
    return (
      <div className="max-w-md mx-auto my-12 p-8 text-center bg-white border border-rose-200 rounded-2xl shadow-lg space-y-4">
        <div className="w-12 h-12 bg-rose-50 border border-rose-200 text-rose-600 rounded-xl flex items-center justify-center mx-auto">
          <ShieldCheck className="w-6 h-6 text-rose-600" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-slate-900">Access Restricted: Institutional Isolation</h3>
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            One institution&apos;s record does not exist in another institution. Batch #{batchId} belongs to another institution and cannot be accessed under your current institutional nodal login.
          </p>
        </div>
        <Link
          href="/uploads"
          className="inline-flex items-center justify-center px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition"
        >
          Return to My Institution&apos;s Batches
        </Link>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "APPROVED":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "COMMITTED":
      case "UNDER_REVIEW":
        return "bg-blue-100 text-blue-800 border-blue-300";
      case "RETURNED_FOR_CORRECTION":
      case "REJECTED_NEEDS_CORRECTION":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "NEEDS_CORRECTION":
        return "bg-rose-100 text-rose-800 border-rose-300";
      case "REJECTED":
        return "bg-rose-100 text-rose-800 border-rose-300";
      default:
        return "bg-slate-100 text-slate-700 border-slate-300";
    }
  };

  const getRowStatusBadge = (status: string) => {
    switch (status) {
      case "ELIGIBLE":
        return "bg-emerald-100 text-emerald-800 border-emerald-300";
      case "EXEMPTED":
        return "bg-teal-100 text-teal-800 border-teal-300 font-bold";
      case "EXEMPTION_REQUESTED":
        return "bg-purple-100 text-purple-800 border-purple-300";
      case "REQUIRES_REVIEW":
        return "bg-amber-100 text-amber-800 border-amber-300";
      case "BLOCKING_ERROR":
        return "bg-rose-100 text-rose-800 border-rose-300 font-bold";
      default:
        return "bg-slate-100 text-slate-700 border-slate-300";
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
              Institution: <span className="font-semibold text-slate-700">{batch.institution_name || `Inst #${batch.institution_id}`} ({batch.aicte_id})</span> |
              Academic Session: <span className="font-semibold text-slate-700">{batch.academic_year}</span>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            type="button"
            onClick={() => handleDownloadBatch("xlsx")}
            className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-lg border border-emerald-300 flex items-center gap-1.5 transition cursor-pointer"
            title="Download genuine OpenXML Excel spreadsheet (.xlsx)"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
            <span>Download Excel</span>
          </button>
          <button
            type="button"
            onClick={() => handleDownloadBatch("csv")}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 flex items-center gap-1.5 transition cursor-pointer"
            title="Download RFC-4180 CSV file (.csv)"
          >
            <FileDown className="w-3.5 h-3.5 text-slate-600" />
            <span>Download CSV</span>
          </button>
          {isAdmin && (
            <button
              onClick={handleTriggerRevalidation}
              disabled={isRevalidating}
              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg border border-slate-300 flex items-center gap-1.5 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isRevalidating ? "animate-spin" : ""}`} />
              <span>Re-run Validation</span>
            </button>
          )}
          <Link
            href="/admissions"
            className="px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white text-xs font-medium rounded-lg transition"
          >
            View Admissions Roll
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

      {/* Live Server File Artifacts Hub */}
      <div className="p-4 bg-gradient-to-r from-slate-900 to-govNavy-950 text-white rounded-xl shadow-sm border border-slate-700/60 space-y-2">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-mono font-bold rounded">
                SERVER FILE SYSTEM ARTIFACTS
              </span>
              <span className="text-xs font-semibold text-slate-200">
                Format: {batch.file_format || (batch.filename?.endsWith(".xlsx") ? "XLSX" : "CSV")}
              </span>
            </div>
            <div className="text-xs font-mono text-slate-300 break-all flex items-center gap-1.5">
              <span className="text-slate-400">Disk Path:</span>
              <span className="bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700 text-govTeal-300 select-all font-semibold">
                {batch.full_storage_path || batch.storage_path_xlsx || batch.storage_path_csv || "storage/uploads/..."}
              </span>
            </div>
            <p className="text-[11px] text-slate-400">
              Live inline edits below synchronize immediately with this file on disk. No re-run or external software required.
            </p>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => handleDownloadBatch("xlsx")}
              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-xs cursor-pointer"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>Download Excel (.xlsx)</span>
            </button>
            <button
              type="button"
              onClick={() => handleDownloadBatch("csv")}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
            >
              <FileDown className="w-3.5 h-3.5" />
              <span>Download CSV (.csv)</span>
            </button>
          </div>
        </div>
      </div>

      {/* RETURNED FOR CORRECTION / REVIEW REMARKS BANNER */}
      {batch.status === "RETURNED_FOR_CORRECTION" && (
        <div className="p-4 rounded-xl border border-amber-300 bg-amber-50/80 text-amber-900 text-xs space-y-2">
          <div className="flex items-center justify-between">
            <div className="font-bold uppercase tracking-wider flex items-center gap-1.5 text-amber-800">
              <RotateCcw className="w-4 h-4 text-amber-700" />
              <span>Returned to Institution for Correction by AICTE Central Regulator</span>
            </div>
            <span className="text-[10px] text-amber-700 font-mono">Action Required</span>
          </div>
          <div className="p-3 bg-white/80 rounded-lg border border-amber-200 italic font-medium">
            &quot;{batch.review_notes || "Adjudicated by AICTE central review committee. Please rectify highlighted student records."}&quot;
          </div>
          <p className="text-[11px] text-amber-800">
            <strong>How to proceed:</strong> You do <em>not</em> need to modify and re-upload the original Excel file. 
            Directly edit the incorrect cells in the <strong>Spreadsheet Grid</strong> below, view real-time algorithm advice, or submit an official AICTE exemption request for students without an APAAR ID.
          </p>
        </div>
      )}

      {/* THREE-WAY RECONCILIATION SUMMARY CARD */}
      {latest_validation_run && (
        <div className="bg-white p-6 rounded-xl border border-govTeal-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <GitCompare className="w-5 h-5 text-govTeal-600" />
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Three-Way Admission Reconciliation (Run #{latest_validation_run.run_number})
                </h2>
                <p className="text-xs text-slate-500">
                  Comparing Institutional Declaration (A), Submitted Student Records (B), and AICTE Sanctioned Approval Reference (C).
                </p>
              </div>
            </div>
            <span className="px-2.5 py-0.5 rounded bg-slate-100 text-slate-700 text-xs font-mono font-bold">
              Run #{latest_validation_run.run_number}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            {/* Input A */}
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-1">
              <div className="text-[10px] uppercase font-bold text-slate-500">Input A: Declaration</div>
              <div className="text-xl font-bold text-slate-900">
                {latest_validation_run.declared_intake} seats
              </div>
              <p className="text-[11px] text-slate-500">Declared enrolment from database registry</p>
            </div>

            {/* Input B */}
            <div className="p-4 bg-teal-50/50 rounded-xl border border-teal-200 space-y-1">
              <div className="text-[10px] uppercase font-bold text-teal-700">Input B: Submitted Roll</div>
              <div className="text-xl font-bold text-teal-900">
                {latest_validation_run.unique_records} unique records
              </div>
              <p className="text-[11px] text-teal-700">
                {latest_validation_run.total_rows} total rows ({latest_validation_run.duplicate_rows} duplicate rows filtered)
              </p>
            </div>

            {/* Input C & Discrepancy */}
            <div className="p-4 bg-blue-50/50 rounded-xl border border-blue-200 space-y-1">
              <div className="text-[10px] uppercase font-bold text-blue-700">Reconciliation Outcome</div>
              <div className={`text-xl font-bold font-mono ${latest_validation_run.declared_discrepancy !== 0 ? 'text-amber-800' : 'text-emerald-800'}`}>
                Discrepancy: {latest_validation_run.declared_discrepancy > 0 ? `+${latest_validation_run.declared_discrepancy}` : latest_validation_run.declared_discrepancy}
              </div>
              <p className="text-[11px] text-blue-700">
                {latest_validation_run.declared_discrepancy === 0 ? "100% reconciled with declared roll" : "Requires central review alignment"}
              </p>
            </div>
          </div>

          {/* Primary Row Disposition Tally */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs pt-1">
            <div className="p-3 bg-white rounded-lg border border-slate-200">
              <div className="text-slate-500 font-medium">Eligible to Proceed</div>
              <div className="text-lg font-bold text-emerald-800 mt-0.5">{latest_validation_run.eligible_to_proceed}</div>
            </div>
            <div className="p-3 bg-white rounded-lg border border-slate-200">
              <div className="text-slate-500 font-medium">Requiring Review</div>
              <div className="text-lg font-bold text-amber-800 mt-0.5">{latest_validation_run.requiring_review}</div>
            </div>
            <div className="p-3 bg-white rounded-lg border border-slate-200">
              <div className="text-slate-500 font-medium">Blocking Errors</div>
              <div className="text-lg font-bold text-rose-800 mt-0.5">{latest_validation_run.blocking_errors}</div>
            </div>
            <div className="p-3 bg-white rounded-lg border border-slate-200">
              <div className="text-slate-500 font-medium">Duplicate Rows</div>
              <div className="text-lg font-bold text-slate-800 mt-0.5">{latest_validation_run.duplicate_rows}</div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SECTION: AICTE CENTRAL ADVISORY & REGULATORY IDEAS ("GIVE AN IDEA")        */}
      {/* ========================================================================= */}
      <div className="bg-gradient-to-r from-amber-500/10 via-teal-500/10 to-indigo-500/10 p-5 rounded-xl border border-amber-500/30 shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-amber-500 text-white rounded-lg shadow-xs">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-slate-900">
                  AICTE Central Governance Advisories &amp; Remediation Ideas
                </h3>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300">
                  {advisories.length} Advisory Active
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-0.5">
                Central Government officers can provide regulatory ideas or policy dispensations. Colleges can apply recommendations with a single click.
              </p>
            </div>
          </div>

          {isAdmin && (
            <button
              onClick={() => setIsAdvisoryModalOpen(true)}
              className="px-3.5 py-1.5 bg-amber-600 hover:bg-amber-700 text-white text-xs font-bold rounded-lg shadow-xs flex items-center gap-1.5 transition"
            >
              <Sparkles className="w-4 h-4" />
              <span>+ Give an Idea / Issue Advisory</span>
            </button>
          )}
        </div>

        {advisories.length === 0 ? (
          <div className="p-4 bg-white/70 rounded-lg border border-slate-200 text-xs text-slate-500 flex items-center justify-between">
            <span>No regulatory advisories currently issued for this batch.</span>
            {isAdmin && (
              <span className="text-[11px] text-amber-700 font-semibold">
                Click &quot;+ Give an Idea&quot; above to advise institution on programme re-mapping or quota exceptions.
              </span>
            )}
          </div>
        ) : (
          <div className="space-y-2.5">
            {advisories.map((adv: any) => (
              <div
                key={adv.id}
                className="p-4 bg-white rounded-lg border border-slate-200 shadow-2xs flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">{adv.title}</span>
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                      adv.status === "APPLIED_BY_COLLEGE"
                        ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                        : "bg-amber-100 text-amber-800 border-amber-300"
                    }`}>
                      {adv.status === "APPLIED_BY_COLLEGE" ? "✓ APPLIED & RECONCILED" : "PENDING INSTITUTION ACTION"}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      by {adv.created_by_name} • {adv.created_at ? new Date(adv.created_at).toLocaleDateString() : ""}
                    </span>
                  </div>
                  <p className="text-xs text-slate-700 leading-relaxed">
                    {adv.idea_description}
                  </p>
                  {adv.recommended_action && adv.recommended_action.action === "REMAP_PROGRAMME" && (
                    <div className="text-[11px] text-teal-800 font-medium flex items-center gap-1.5 pt-0.5">
                      <span className="px-1.5 py-0.5 rounded bg-teal-50 border border-teal-200 font-mono font-bold">
                        {adv.recommended_action.from_code}
                      </span>
                      <span>→ Remap to approved cluster:</span>
                      <span className="px-1.5 py-0.5 rounded bg-teal-50 border border-teal-200 font-mono font-bold">
                        {adv.recommended_action.to_code}
                      </span>
                    </div>
                  )}
                </div>

                <div className="flex-shrink-0">
                  {adv.status === "ACTIVE" ? (
                    <button
                      onClick={() => handleApplyAdvisory(adv.id)}
                      disabled={isApplyingAdvisoryId === adv.id}
                      className="px-3.5 py-2 bg-govTeal-600 hover:bg-govTeal-700 text-white rounded-lg text-xs font-bold shadow-xs flex items-center gap-1.5 transition cursor-pointer"
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>{isApplyingAdvisoryId === adv.id ? "Applying..." : "Apply AICTE Advisory Recommendation"}</span>
                    </button>
                  ) : (
                    <span className="text-xs font-semibold text-emerald-700 flex items-center gap-1">
                      <CheckCircle2 className="w-4 h-4" /> Applied
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* SECTION: INTERACTIVE IN-BROWSER SPREADSHEET GRID & INLINE CORRECTION       */}
      {/* ========================================================================= */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 pb-4">
          <div className="flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-govTeal-600" />
            <div>
              <h2 className="text-sm font-bold text-slate-900">
                Interactive Staged Admission Spreadsheet ({stagedRows.length} Rows)
              </h2>
              <p className="text-xs text-slate-500">
                Edit cells inline directly on this portal. Deterministic Python algorithms re-verify all 3-way rules instantaneously.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-500 flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Error Highlighted
              <span className="w-2.5 h-2.5 rounded-full bg-amber-500 ml-2"></span> Requires Review
              <span className="w-2.5 h-2.5 rounded-full bg-teal-500 ml-2"></span> AICTE Exempted
            </span>
          </div>
        </div>

        {loadingRows ? (
          <div className="py-12 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
            <Clock className="w-5 h-5 animate-spin text-slate-400" />
            <span>Loading spreadsheet records...</span>
          </div>
        ) : (
          <div className="border border-slate-200 rounded-lg overflow-x-auto">
            <table className="w-full text-xs text-left border-collapse">
              <thead className="bg-slate-100 text-slate-700 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                <tr>
                  <th className="px-3 py-2.5 w-12 text-center">Row</th>
                  <th className="px-3 py-2.5 min-w-[150px]">Student Name</th>
                  <th className="px-3 py-2.5 min-w-[150px]">APAAR ID</th>
                  <th className="px-3 py-2.5 min-w-[110px]">Programme</th>
                  <th className="px-3 py-2.5 min-w-[90px]">Category</th>
                  <th className="px-3 py-2.5 min-w-[80px]">Gender</th>
                  <th className="px-3 py-2.5 min-w-[110px]">Quota</th>
                  <th className="px-3 py-2.5 min-w-[140px]">Reconciliation Status</th>
                  <th className="px-3 py-2.5 text-right min-w-[150px]">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {stagedRows.map((row: any) => {
                  const isEditing = editingRowId === row.id;
                  const hasErrors = row.status === "BLOCKING_ERROR";
                  const hasWarnings = row.status === "REQUIRES_REVIEW";
                  const isExempted = row.status === "EXEMPTED";
                  const isExemptionRequested = row.status === "EXEMPTION_REQUESTED";
                  const hasFindings = row.findings && row.findings.length > 0;
                  const isAdviceOpen = expandedAdviceRowId === row.id;

                  const rowBg = hasErrors
                    ? "bg-rose-50/70 hover:bg-rose-100/50"
                    : hasWarnings
                    ? "bg-amber-50/60 hover:bg-amber-100/40"
                    : isExempted
                    ? "bg-teal-50/60 hover:bg-teal-100/40"
                    : isExemptionRequested
                    ? "bg-purple-50/50 hover:bg-purple-100/40"
                    : "hover:bg-slate-50";

                  return (
                    <React.Fragment key={row.id}>
                      <tr className={`transition ${rowBg} ${isEditing ? "bg-blue-50/60 ring-1 ring-blue-300" : ""}`}>
                        {/* Row Index */}
                        <td className="px-3 py-2 text-center font-mono font-bold text-slate-500">
                          #{row.row_index}
                        </td>

                        {/* Student Name */}
                        <td className="px-3 py-2">
                          {isEditing ? (
                            <input
                              type="text"
                              value={editedValues.student_name}
                              onChange={(e) => setEditedValues({ ...editedValues, student_name: e.target.value })}
                              className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
                            />
                          ) : (
                            <div className="font-semibold text-slate-900">{row.student_name || "—"}</div>
                          )}
                        </td>

                        {/* APAAR ID */}
                        <td className="px-3 py-2 font-mono">
                          {isEditing ? (
                            <input
                              type="text"
                              value={editedValues.apaar_id}
                              onChange={(e) => setEditedValues({ ...editedValues, apaar_id: e.target.value })}
                              placeholder="12-digit numeric"
                              className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                            />
                          ) : (
                            <div>
                              <span className={`font-medium ${!row.apaar_id ? "text-rose-600 font-bold italic" : "text-slate-800"}`}>
                                {row.apaar_id || "Missing APAAR"}
                              </span>
                              {row.apaar_id && row.apaar_id.length !== 12 && (
                                <span className="ml-1 text-[10px] text-rose-600 font-bold">(Invalid Format)</span>
                              )}
                            </div>
                          )}
                        </td>

                        {/* Programme Code */}
                        <td className="px-3 py-2 font-mono">
                          {isEditing ? (
                            <input
                              type="text"
                              value={editedValues.programme_code}
                              onChange={(e) => setEditedValues({ ...editedValues, programme_code: e.target.value })}
                              className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 uppercase font-mono"
                            />
                          ) : (
                            <span className="font-bold text-slate-800">{row.programme_code || "—"}</span>
                          )}
                        </td>

                        {/* Category */}
                        <td className="px-3 py-2">
                          {isEditing ? (
                            <select
                              value={editedValues.category}
                              onChange={(e) => setEditedValues({ ...editedValues, category: e.target.value })}
                              className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
                            >
                              <option value="OPEN">OPEN</option>
                              <option value="OBC_NCL">OBC_NCL</option>
                              <option value="SC">SC</option>
                              <option value="ST">ST</option>
                              <option value="EWS">EWS</option>
                            </select>
                          ) : (
                            <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700">
                              {row.category}
                            </span>
                          )}
                        </td>

                        {/* Gender */}
                        <td className="px-3 py-2">
                          {isEditing ? (
                            <select
                              value={editedValues.gender}
                              onChange={(e) => setEditedValues({ ...editedValues, gender: e.target.value })}
                              className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
                            >
                              <option value="MALE">MALE</option>
                              <option value="FEMALE">FEMALE</option>
                              <option value="OTHER">OTHER</option>
                            </select>
                          ) : (
                            <span className="text-slate-600">{row.gender}</span>
                          )}
                        </td>

                        {/* Admission Quota */}
                        <td className="px-3 py-2">
                          {isEditing ? (
                            <select
                              value={editedValues.admission_quota}
                              onChange={(e) => setEditedValues({ ...editedValues, admission_quota: e.target.value })}
                              className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-medium"
                            >
                              <option value="STATE_GOVT">STATE_GOVT</option>
                              <option value="MANAGEMENT">MANAGEMENT</option>
                              <option value="AICTE_TFW">AICTE_TFW</option>
                              <option value="NRI">NRI</option>
                            </select>
                          ) : (
                            <span className="text-slate-600 font-medium">{row.admission_quota}</span>
                          )}
                        </td>

                        {/* Reconciliation Status & Diagnosis */}
                        <td className="px-3 py-2">
                          <div className="flex flex-col gap-1 items-start">
                            <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${getRowStatusBadge(row.status)}`}>
                              {row.status}
                            </span>
                            {hasFindings && (
                              <button
                                onClick={() => setExpandedAdviceRowId(isAdviceOpen ? null : row.id)}
                                className="text-[10px] text-govTeal-700 hover:text-govTeal-900 font-semibold flex items-center gap-0.5 transition"
                              >
                                {isAdviceOpen ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                                <span>Algorithm Advice ({row.findings.length})</span>
                              </button>
                            )}
                          </div>
                        </td>

                        {/* Actions */}
                        <td className="px-3 py-2 text-right">
                          <div className="flex items-center justify-end gap-1.5">
                            {isEditing ? (
                              <>
                                <button
                                  onClick={() => handleSaveRow(row.id)}
                                  disabled={isSavingRow}
                                  className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold flex items-center gap-1 transition shadow-xs"
                                >
                                  <Save className="w-3 h-3" />
                                  <span>{isSavingRow ? "Saving..." : "Save"}</span>
                                </button>
                                <button
                                  onClick={handleCancelEdit}
                                  disabled={isSavingRow}
                                  className="p-1 rounded text-slate-500 hover:bg-slate-200 transition"
                                  title="Cancel"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              </>
                            ) : (
                              <>
                                <button
                                  onClick={() => handleStartEdit(row)}
                                  className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-xs font-semibold flex items-center gap-1 transition"
                                  title="Edit cells inline"
                                >
                                  <Edit2 className="w-3 h-3" />
                                  <span>Edit</span>
                                </button>

                                {/* If student lacks APAAR ID, offer Exemption Request button */}
                                {(!row.apaar_id || hasErrors) && !isExempted && !isExemptionRequested && (
                                  <button
                                    onClick={() => handleOpenExemption(row)}
                                    className="px-2 py-1 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded text-xs font-semibold flex items-center gap-1 transition"
                                    title="Send Message / Exemption Request to AICTE Central"
                                  >
                                    <MessageSquare className="w-3 h-3" />
                                    <span>AICTE Exemption</span>
                                  </button>
                                )}
                              </>
                            )}
                          </div>
                        </td>
                      </tr>

                      {/* Expandable Algorithm Advice & Diagnosis Card */}
                      {isAdviceOpen && hasFindings && (
                        <tr className="bg-slate-50 border-y border-slate-200">
                          <td colSpan={9} className="p-4">
                            <div className="bg-white rounded-lg border border-slate-200 p-4 space-y-3 shadow-2xs">
                              <div className="flex items-center gap-2 text-xs font-bold text-slate-900 border-b border-slate-100 pb-2">
                                <Sparkles className="w-4 h-4 text-govTeal-600" />
                                <span>Reconciliation Algorithm Diagnostic Findings for Row #{row.row_index}</span>
                              </div>

                              <div className="space-y-2">
                                {row.findings.map((f: any) => (
                                  <div
                                    key={f.id}
                                    className={`p-3 rounded-lg border text-xs space-y-1 ${
                                      f.severity === "ERROR"
                                        ? "bg-rose-50/60 border-rose-200 text-rose-900"
                                        : f.severity === "WARNING"
                                        ? "bg-amber-50/60 border-amber-200 text-amber-900"
                                        : "bg-blue-50/60 border-blue-200 text-blue-900"
                                    }`}
                                  >
                                    <div className="flex items-center justify-between font-mono font-bold text-[11px]">
                                      <span>Rule: {f.rule_id} ({f.field_name})</span>
                                      <span className="uppercase text-[10px] px-1.5 py-0.2 rounded bg-white/80 border">
                                        {f.severity}
                                      </span>
                                    </div>
                                    <p className="font-medium text-slate-800">{f.message}</p>
                                    {f.recommended_action && (
                                      <div className="text-[11px] font-semibold text-govTeal-800 pt-1">
                                        👉 Action Required: {f.recommended_action}
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Re-Submit Corrected Batch Action for College */}
        {!isAdmin && (batch.status === "RETURNED_FOR_CORRECTION" || batch.status === "NEEDS_CORRECTION" || batch.status === "PREFLIGHT") && (
          <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-teal-50/60 p-4 rounded-xl border border-teal-200">
            <div>
              <div className="text-xs font-bold text-teal-900">Finished editing records?</div>
              <p className="text-[11px] text-teal-700">
                Submit this corrected admission roll back to AICTE Central Portal for formal sanctioning and approval.
              </p>
            </div>
            <button
              onClick={handleCommitBatch}
              disabled={isSubmitting}
              className="px-5 py-2.5 bg-govTeal-600 hover:bg-govTeal-700 text-white text-xs font-semibold rounded-lg flex items-center gap-2 shadow-xs transition whitespace-nowrap"
            >
              <Send className="w-4 h-4" />
              <span>Commit &amp; Re-submit Corrected Batch</span>
            </button>
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* SECTION: AICTE CENTRAL REGULATORY REVIEW CONTROLS (for Reviewers)          */}
      {/* ========================================================================= */}
      {isAdmin && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex items-center gap-2 border-b border-slate-200 pb-3">
            <ShieldCheck className="w-5 h-5 text-govNavy-900" />
            <div>
              <h2 className="text-sm font-bold text-slate-900">AICTE Central Regulatory Review &amp; Adjudication</h2>
              <p className="text-xs text-slate-500">
                Authorized regional regulatory officer decision controls. Decisions are committed to the tamper-evident SHA-256 audit ledger.
              </p>
            </div>
          </div>

          <div className="space-y-3">
            <label className="block text-xs font-semibold text-slate-700">
              Reviewer Adjudication Remarks &amp; Justification
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
                disabled={isSubmitting || (latest_validation_run && latest_validation_run.blocking_errors > 0)}
                className={`px-4 py-2 text-xs font-semibold rounded-lg flex items-center gap-1.5 transition ${
                  latest_validation_run && latest_validation_run.blocking_errors > 0
                    ? "bg-slate-200 text-slate-400 cursor-not-allowed"
                    : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs"
                }`}
                title={latest_validation_run && latest_validation_run.blocking_errors > 0 ? "Cannot approve while blocking errors exist" : "Sanction and admit students"}
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Approve Submission</span>
              </button>

              <button
                onClick={() => handleReviewDecision("RETURNED_FOR_CORRECTION")}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-amber-300 text-amber-800 hover:bg-amber-50 flex items-center gap-1.5 transition"
              >
                <RotateCcw className="w-4 h-4" />
                <span>Return to Institution for Correction</span>
              </button>

              <button
                onClick={() => handleReviewDecision("REJECTED")}
                disabled={isSubmitting}
                className="px-4 py-2 text-xs font-semibold rounded-lg border border-rose-300 text-rose-700 hover:bg-rose-50 flex items-center gap-1.5 transition"
              >
                <XCircle className="w-4 h-4" />
                <span>Reject Submission</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* SECTION: INSTITUTIONAL QUERIES & EXEMPTION APPEALS (Both College & Central)*/}
      {/* ========================================================================= */}
      {disputeQueries.length > 0 && (
        <div className="bg-white p-6 rounded-xl border border-purple-200 shadow-xs space-y-4">
          <div className="flex items-center justify-between border-b border-purple-100 pb-3">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-purple-700" />
              <div>
                <h2 className="text-sm font-bold text-slate-900">
                  Institutional Exemption Requests &amp; Communication ({disputeQueries.length})
                </h2>
                <p className="text-xs text-slate-500">
                  Official communications regarding students without APAAR IDs (UIDAI failures, iris mismatch, or admission exceptions).
                </p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            {disputeQueries.map((q: any) => (
              <div key={q.id} className="p-4 bg-purple-50/40 rounded-xl border border-purple-200 text-xs space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-purple-900">{q.subject}</span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-purple-100 text-purple-800 border border-purple-300">
                      {q.category}
                    </span>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                    q.status === "PROVISIONALLY_EXEMPTED"
                      ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                      : q.status === "RESOLVED_REJECTED"
                      ? "bg-rose-100 text-rose-800 border-rose-300"
                      : "bg-amber-100 text-amber-800 border-amber-300"
                  }`}>
                    {q.status}
                  </span>
                </div>

                <div className="text-slate-700 font-medium">{q.message}</div>
                <div className="text-[10px] text-slate-500">
                  Raised by: {q.raised_by_name || "Institution Nodal Officer"} at {q.created_at ? new Date(q.created_at).toLocaleString() : "Recently"}
                </div>

                {q.aicte_reply && (
                  <div className="mt-2 p-3 bg-white rounded-lg border border-purple-200 space-y-1">
                    <div className="text-[11px] font-bold text-govNavy-900 flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                      <span>AICTE Central Resolution ({q.resolved_by_name || "Bureau of Approval"})</span>
                    </div>
                    <p className="text-slate-800 italic">&quot;{q.aicte_reply}&quot;</p>
                  </div>
                )}

                {/* AICTE Admin Resolution Controls */}
                {isAdmin && q.status === "PENDING_REVIEW" && (
                  <div className="mt-3 pt-2 border-t border-purple-200 flex items-center gap-2">
                    <button
                      onClick={() => handleResolveQuery(q.id, "APPROVE_EXEMPTION")}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded text-xs font-semibold flex items-center gap-1 transition shadow-xs"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Grant Provisional Exemption (APH 2026-27)</span>
                    </button>
                    <button
                      onClick={() => handleResolveQuery(q.id, "REJECT_QUERY")}
                      className="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded text-xs font-semibold flex items-center gap-1 transition shadow-xs"
                    >
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Reject Exemption</span>
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Runs Multi-Run History */}
      {validation_runs_history && validation_runs_history.length > 0 && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-slate-500" />
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Validation Runs Historical Traceability ({validation_runs_history.length} Runs Recorded)
            </h3>
          </div>
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
                <tr>
                  <th className="px-3 py-2">Run Number</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Total Rows</th>
                  <th className="px-3 py-2">Unique Records</th>
                  <th className="px-3 py-2">Blocking Errors</th>
                  <th className="px-3 py-2">Discrepancy</th>
                  <th className="px-3 py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {validation_runs_history.map((r: any) => (
                  <tr key={r.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-mono font-bold text-slate-900">Run #{r.run_number}</td>
                    <td className="px-3 py-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-700">
                        {r.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-slate-700">{r.total_rows}</td>
                    <td className="px-3 py-2 text-slate-700 font-semibold">{r.unique_records}</td>
                    <td className="px-3 py-2 text-rose-700 font-bold">{r.blocking_errors}</td>
                    <td className="px-3 py-2 font-mono text-slate-700">{r.declared_discrepancy}</td>
                    <td className="px-3 py-2 font-mono text-slate-500">
                      {r.created_at ? new Date(r.created_at).toLocaleString() : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* MODAL: SUBMIT EXEMPTION / COMMUNICATION TO AICTE CENTRAL                  */}
      {/* ========================================================================= */}
      {isExemptionModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-purple-700" />
                <h3 className="text-sm font-bold text-slate-900">
                  Submit Institutional Exemption to AICTE Central
                </h3>
              </div>
              <button
                onClick={() => setIsExemptionModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleSubmitExemption} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Target Candidate / Row</label>
                <div className="p-2 bg-slate-50 border rounded-lg font-mono text-slate-800">
                  Row #{exemptionRow?.row_index}: {exemptionRow?.student_name || "Candidate"} (Prog: {exemptionRow?.programme_code})
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Exemption Reason Category</label>
                <select
                  value={exemptionCategory}
                  onChange={(e) => setExemptionCategory(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-purple-500"
                >
                  <option value="MISSING_APAAR_UIDAI_FAIL">UIDAI Biometric / Iris Recapture Delay (No APAAR yet)</option>
                  <option value="TECHNICAL_EXCEPTION">State Admission Portal Sync Discrepancy</option>
                  <option value="QUOTA_DISPUTE">Quota / Supernumerary Re-allocation Query</option>
                  <option value="OTHER">Other Institutional Technical Exception</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Subject</label>
                <input
                  type="text"
                  required
                  value={exemptionSubject}
                  onChange={(e) => setExemptionSubject(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-purple-500 font-medium"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Institutional Justification Message</label>
                <textarea
                  rows={4}
                  required
                  value={exemptionMessage}
                  onChange={(e) => setExemptionMessage(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-purple-500"
                  placeholder="Detail the circumstances, UIDAI acknowledgement number, or physical verification..."
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsExemptionModalOpen(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingExemption}
                  className="px-4 py-1.5 bg-purple-700 hover:bg-purple-800 text-white font-semibold rounded-lg shadow-xs transition"
                >
                  {isSubmittingExemption ? "Sending..." : "Submit to AICTE"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
      {/* ========================================================================= */}
      {/* MODAL: AICTE CENTRAL OFFICER ISSUES ADVISORY / GIVES AN IDEA              */}
      {/* ========================================================================= */}
      {isAdvisoryModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-xs p-4">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Issue Official AICTE Central Advisory / Regulatory Idea
                </h3>
              </div>
              <button
                onClick={() => setIsAdvisoryModalOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-slate-600 transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleCreateAdvisory} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Advisory Category / Nature</label>
                <select
                  value={advisoryType}
                  onChange={(e) => setAdvisoryType(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                >
                  <option value="PROGRAMME_REMAP_RECOMMENDATION">Programme Cluster Remap Recommendation (APH 2026-27 Cl. 4.2)</option>
                  <option value="QUOTA_REALLOCATION_IDEA">Supernumerary Quota Reallocation Idea (TFW / EWS)</option>
                  <option value="PROVISIONAL_UNDERTAKING">Form-8 Provisional Undertaking Approval</option>
                  <option value="GENERAL_ADVISORY">General Institutional Remediation Advisory</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Advisory Title</label>
                <input
                  type="text"
                  required
                  value={advisoryTitle}
                  onChange={(e) => setAdvisoryTitle(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500 font-semibold"
                />
              </div>

              {advisoryType === "PROGRAMME_REMAP_RECOMMENDATION" && (
                <div className="grid grid-cols-2 gap-3 p-3 bg-amber-50/60 border border-amber-200 rounded-lg">
                  <div>
                    <label className="block text-[11px] font-semibold text-amber-900 mb-1">Discrepant Programme Code</label>
                    <input
                      type="text"
                      required
                      value={advisoryFromCode}
                      onChange={(e) => setAdvisoryFromCode(e.target.value.toUpperCase())}
                      className="w-full p-1.5 border border-amber-300 rounded bg-white font-mono uppercase"
                    />
                  </div>
                  <div>
                    <label className="block text-[11px] font-semibold text-amber-900 mb-1">Recommended Approved Cluster</label>
                    <input
                      type="text"
                      required
                      value={advisoryToCode}
                      onChange={(e) => setAdvisoryToCode(e.target.value.toUpperCase())}
                      className="w-full p-1.5 border border-amber-300 rounded bg-white font-mono uppercase"
                    />
                  </div>
                </div>
              )}

              <div>
                <label className="block font-semibold text-slate-700 mb-1">AICTE Regulatory Idea &amp; Instructions</label>
                <textarea
                  rows={4}
                  required
                  value={advisoryDescription}
                  onChange={(e) => setAdvisoryDescription(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-amber-500"
                  placeholder="Detail the regulatory rationale and suggested path forward..."
                />
              </div>

              <div className="pt-2 flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setIsAdvisoryModalOpen(false)}
                  className="px-3 py-1.5 border border-slate-300 rounded-lg text-slate-700 hover:bg-slate-50 transition"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingAdvisory}
                  className="px-4 py-1.5 bg-amber-600 hover:bg-amber-700 text-white font-semibold rounded-lg shadow-xs transition"
                >
                  {isSubmittingAdvisory ? "Dispatching..." : "Dispatch Advisory to College"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
