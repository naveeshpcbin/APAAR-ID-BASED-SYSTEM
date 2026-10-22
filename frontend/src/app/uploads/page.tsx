"use client";

import React, { useState, useEffect } from "react";
import {
  UploadCloud,
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ArrowRight,
  RefreshCw,
  FileText,
  Download,
  Info,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function UploadsPage() {
  const { user } = useAuth();
  const [file, setFile] = useState<File | null>(null);
  const [batches, setBatches] = useState<any[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const [isCommitting, setIsCommitting] = useState(false);
  const [preflightData, setPreflightData] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadBatches = async () => {
    try {
      const res = await apiRequest("/uploads");
      setBatches(res);
    } catch (e: any) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadBatches();
  }, [user]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setSuccessMessage(null);
    }
  };

  const handlePreflightUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError("Please select a CSV or Excel file to upload.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setPreflightData(null);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("institution_id", String(user?.institutionId || 1));
    formData.append("academic_year", "2026-27");

    try {
      const res = await apiRequest("/uploads/preflight", {
        method: "POST",
        body: formData,
      });
      setPreflightData(res);
      await loadBatches();
    } catch (err: any) {
      setError(err.message || "Failed to process upload.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleCommitBatch = async (batchId: number) => {
    setIsCommitting(true);
    setError(null);
    try {
      const res = await apiRequest(`/uploads/${batchId}/commit`, {
        method: "POST",
        body: JSON.stringify({ skip_errors: true }),
      });
      setSuccessMessage(
        `Batch #${batchId} committed successfully! ${res.committed_valid_records} valid records admitted, ${res.quarantined_records} quarantined for review.`
      );
      setPreflightData(null);
      setFile(null);
      await loadBatches();
    } catch (err: any) {
      setError(err.message || "Failed to commit batch.");
    } finally {
      setIsCommitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Institutional Smart Uploader & Pre-flight Workspace
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Automated schema mapping, APAAR identity checks, intake compliance, and row-level reconciliation.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-600 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
          Target Institution ID: #{user?.institutionId || 1} ({user?.institutionName || "DTU Delhi"})
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs flex items-center gap-2">
          <XCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Uploader Card */}
      <div className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs">
        <h2 className="text-sm font-bold text-slate-900 mb-1">Upload Student Admission Dataset</h2>
        <p className="text-xs text-slate-500 mb-4">
          Select or drag your institutional spreadsheet (.csv, .xlsx, .xls) containing APAAR numbers, student details, and programme codes.
        </p>

        <form onSubmit={handlePreflightUpload} className="space-y-4">
          <div className="border-2 border-dashed border-slate-300 hover:border-govTeal-500 rounded-xl p-8 text-center bg-slate-50/50 transition cursor-pointer">
            <input
              type="file"
              id="file-upload"
              accept=".csv, .xlsx, .xls"
              onChange={handleFileChange}
              className="hidden"
            />
            <label htmlFor="file-upload" className="cursor-pointer block">
              <UploadCloud className="w-10 h-10 text-slate-400 mx-auto mb-2" />
              <div className="text-sm font-semibold text-slate-700">
                {file ? file.name : "Click to browse or drop file here"}
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Supports CSV, Excel (XLSX, XLS) up to 10MB
              </p>
            </label>
          </div>

          <div className="flex items-center justify-between">
            <div className="text-xs text-slate-500 flex items-center gap-1.5">
              <Info className="w-4 h-4 text-govTeal-600" />
              <span>Deterministic mock APAAR validation active. Zero PII transmitted externally.</span>
            </div>
            <button
              type="submit"
              disabled={!file || isUploading}
              className="px-4 py-2 bg-govTeal-600 hover:bg-govTeal-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-2 transition"
            >
              {isUploading ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing Pre-flight...</span>
                </>
              ) : (
                <>
                  <span>Run Pre-flight Validation</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Pre-flight Results Workspace */}
      {preflightData && (
        <div className="bg-white p-6 rounded-xl border border-govTeal-200 shadow-md space-y-6">
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-govTeal-100 text-govTeal-800 text-xs font-mono font-bold">
                  Batch #{preflightData.batch_id}
                </span>
                <h3 className="text-sm font-bold text-slate-900">
                  Pre-flight Validation & Schema Reconciliation
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                File: {preflightData.filename} | Academic Session: {preflightData.academic_year}
              </p>
            </div>

            <button
              onClick={() => handleCommitBatch(preflightData.batch_id)}
              disabled={isCommitting}
              className="px-4 py-2 bg-govNavy-900 hover:bg-govNavy-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-sm flex items-center gap-2 transition"
            >
              {isCommitting ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Committing Batch...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3.5 h-3.5 text-govTeal-400" />
                  <span>Commit Clean Records</span>
                </>
              )}
            </button>
          </div>

          {/* Validation Tally */}
          <div className="grid grid-cols-4 gap-4">
            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
              <div className="text-xs text-slate-500 font-semibold">Total Rows</div>
              <div className="text-xl font-bold text-slate-900 mt-1">{preflightData.total_rows}</div>
            </div>
            <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
              <div className="text-xs text-emerald-700 font-semibold">Valid & Verified</div>
              <div className="text-xl font-bold text-emerald-800 mt-1">{preflightData.valid_rows}</div>
            </div>
            <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
              <div className="text-xs text-amber-700 font-semibold">Warnings / Review</div>
              <div className="text-xl font-bold text-amber-800 mt-1">{preflightData.warning_rows}</div>
            </div>
            <div className="p-3 bg-rose-50 rounded-lg border border-rose-200">
              <div className="text-xs text-rose-700 font-semibold">Hard Errors</div>
              <div className="text-xl font-bold text-rose-800 mt-1">{preflightData.error_rows}</div>
            </div>
          </div>

          {/* Column Mappings Table */}
          <div>
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Detected Schema Column Mappings
            </h4>
            <div className="flex flex-wrap gap-2 text-xs">
              {Object.entries(preflightData.mappings || {}).map(([incoming, canonical]) => (
                <div
                  key={incoming}
                  className="px-2.5 py-1 rounded bg-slate-100 border border-slate-200 flex items-center gap-1.5"
                >
                  <span className="font-mono text-slate-500">{incoming}</span>
                  <span className="text-slate-400">&rarr;</span>
                  <span className="font-semibold text-govTeal-700">{String(canonical)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Findings Table */}
          {preflightData.findings_preview && preflightData.findings_preview.length > 0 ? (
            <div>
              <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
                Row-Level Findings & Actionable Guidance
              </h4>
              <div className="border border-slate-200 rounded-lg overflow-hidden">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
                    <tr>
                      <th className="px-3 py-2">Row</th>
                      <th className="px-3 py-2">Severity</th>
                      <th className="px-3 py-2">Rule ID</th>
                      <th className="px-3 py-2">Finding Message</th>
                      <th className="px-3 py-2">Recommended Next Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {preflightData.findings_preview.map((f: any, idx: number) => (
                      <tr key={idx} className="hover:bg-slate-50">
                        <td className="px-3 py-2 font-mono font-medium text-slate-500">#{f.row_index}</td>
                        <td className="px-3 py-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                              f.severity === "ERROR"
                                ? "bg-red-100 text-red-800"
                                : f.severity === "WARNING"
                                ? "bg-amber-100 text-amber-800"
                                : "bg-blue-100 text-blue-800"
                            }`}
                          >
                            {f.severity}
                          </span>
                        </td>
                        <td className="px-3 py-2 font-mono text-slate-700 font-medium">{f.rule_id}</td>
                        <td className="px-3 py-2 text-slate-800">{f.message}</td>
                        <td className="px-3 py-2 text-slate-600">{f.recommended_action || "—"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-emerald-50 text-emerald-800 rounded-lg text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>All rows passed strict syntactic schema and APAAR identity verification. Ready for atomic commit.</span>
            </div>
          )}
        </div>
      )}

      {/* Batch Upload History */}
      <div className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs">
        <h2 className="text-sm font-bold text-slate-900 mb-1">Ingestion Batch History</h2>
        <p className="text-xs text-slate-500 mb-4">Historical upload batches, status, and reconciliation outcomes.</p>

        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
              <tr>
                <th className="px-3 py-2.5">Batch ID</th>
                <th className="px-3 py-2.5">Filename</th>
                <th className="px-3 py-2.5">Academic Year</th>
                <th className="px-3 py-2.5">Total Rows</th>
                <th className="px-3 py-2.5">Valid</th>
                <th className="px-3 py-2.5">Warnings</th>
                <th className="px-3 py-2.5">Errors</th>
                <th className="px-3 py-2.5">Status</th>
                <th className="px-3 py-2.5">Submitted At</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {batches.map((b) => (
                <tr key={b.id} className="hover:bg-slate-50">
                  <td className="px-3 py-2 font-mono font-bold text-slate-900">#{b.id}</td>
                  <td className="px-3 py-2 font-medium text-slate-800">{b.filename}</td>
                  <td className="px-3 py-2 font-mono text-slate-600">{b.academic_year}</td>
                  <td className="px-3 py-2 font-semibold text-slate-900">{b.total_rows}</td>
                  <td className="px-3 py-2 text-emerald-600 font-semibold">{b.valid_rows}</td>
                  <td className="px-3 py-2 text-amber-600 font-semibold">{b.warning_rows}</td>
                  <td className="px-3 py-2 text-rose-600 font-semibold">{b.error_rows}</td>
                  <td className="px-3 py-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        b.status === "COMMITTED"
                          ? "bg-emerald-100 text-emerald-800"
                          : "bg-blue-100 text-blue-800"
                      }`}
                    >
                      {b.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-500 font-mono">
                    {new Date(b.created_at).toLocaleString()}
                  </td>
                </tr>
              ))}
              {batches.length === 0 && (
                <tr>
                  <td colSpan={9} className="px-3 py-6 text-center text-slate-400">
                    No upload batches recorded for this institution yet.
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
