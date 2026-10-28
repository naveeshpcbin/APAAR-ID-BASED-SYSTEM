"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
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
  Edit2,
  Save,
  X,
  Sparkles,
  Code,
  Check,
  ChevronDown,
  ChevronUp,
  Plus,
  Trash2,
  Play,
  FileDown,
} from "lucide-react";
import { apiRequest, API_BASE } from "@/lib/api";
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

  // Ingestion Mode: "GENERATE_ON_WEB" vs "UPLOAD_FILE"
  const [ingestionMode, setIngestionMode] = useState<"GENERATE_ON_WEB" | "UPLOAD_FILE">("GENERATE_ON_WEB");
  const [generatorRows, setGeneratorRows] = useState<any[]>([]);
  const [builderFormat, setBuilderFormat] = useState<"xlsx" | "csv">("xlsx");
  const [downloadedFilePath, setDownloadedFilePath] = useState<string | null>(null);

  // In-Browser Spreadsheet & Live Correction State
  const [stagedRows, setStagedRows] = useState<any[]>([]);
  const [approvedProgrammes, setApprovedProgrammes] = useState<any[]>([]);
  const [loadingRows, setLoadingRows] = useState(false);
  const [editingRowId, setEditingRowId] = useState<number | null>(null);
  const [editedValues, setEditedValues] = useState<Record<string, any>>({});
  const [isSavingRow, setIsSavingRow] = useState(false);
  const [isQuickFixing, setIsQuickFixing] = useState(false);

  // Raw CSV Editor Modal State
  const [rawCsvModalOpen, setRawCsvModalOpen] = useState(false);
  const [rawCsvText, setRawCsvText] = useState("");
  const [isSavingRawCsv, setIsSavingRawCsv] = useState(false);

  const loadBatches = async () => {
    try {
      const res = await apiRequest("/uploads");
      setBatches(res);
    } catch (e: any) {
      console.error(e);
    }
  };

  const loadApprovedProgrammes = async () => {
    try {
      const instId = user?.institutionId || 2;
      const progs = await apiRequest(`/institutions/${instId}/programmes`);
      setApprovedProgrammes(progs || []);
    } catch (e: any) {
      console.error("Failed to load approved programmes:", e);
    }
  };

  const loadStagedRows = async (batchId: number) => {
    try {
      setLoadingRows(true);
      const res = await apiRequest(`/uploads/${batchId}/rows`);
      setStagedRows(res.rows || []);
    } catch (err: any) {
      console.error("Failed to load staged rows:", err);
    } finally {
      setLoadingRows(false);
    }
  };

  useEffect(() => {
    loadBatches();
    loadApprovedProgrammes();
  }, [user]);

  // Web In-Browser Dataset Generator Handlers
  const handleAutoGenerateStudents = async (count: number = 5, withDiscrepancies: boolean = false) => {
    try {
      setError(null);
      const res = await apiRequest("/uploads/generate-dataset", {
        method: "POST",
        body: JSON.stringify({
          institution_id: user?.institutionId || 2,
          count: count,
          include_discrepancies: withDiscrepancies,
          academic_year: "2026-27",
        }),
      });
      setGeneratorRows(res.rows || []);
      setSuccessMessage(
        `Generated ${res.count} student admission records directly on the website for ${
          user?.institutionName || "your institution"
        }! ${
          withDiscrepancies
            ? "Includes sample regulatory discrepancies to demonstrate real-time AICTE audit detection."
            : "Fully compliant with approved programmes and sanctioned intake."
        }`
      );
    } catch (err: any) {
      setError(err.message || "Failed to generate student dataset.");
    }
  };

  const handleAddBlankRow = () => {
    const defaultProg = approvedProgrammes[0]?.programme_code || "BTECH-CSE";
    const randomSuffix = Math.floor(10000000 + Math.random() * 90000000);
    const newRow = {
      apaar_id: `98${randomSuffix}12`,
      student_name: "",
      dob: "2005-01-15",
      gender: "MALE",
      programme_code: defaultProg,
      category: "OPEN",
      admission_quota: "STATE_GOVT",
      is_supernumerary: false,
      nationality_type: "DOMESTIC",
    };
    setGeneratorRows((prev) => [...prev, newRow]);
  };

  const handleUpdateGeneratorRow = (index: number, field: string, value: any) => {
    setGeneratorRows((prev) => {
      const next = [...prev];
      next[index] = { ...next[index], [field]: value };
      return next;
    });
  };

  const handleRemoveGeneratorRow = (index: number) => {
    setGeneratorRows((prev) => prev.filter((_, i) => i !== index));
  };

  const compileRowsToCsv = (rows: any[]) => {
    const header = "apaar_id,student_name,dob,gender,programme_code,category,admission_quota,is_supernumerary,nationality_type\n";
    const body = rows
      .map(
        (r) =>
          `${(r.apaar_id || "").trim()},${(r.student_name || "").trim()},${(r.dob || "").trim()},${
            (r.gender || "MALE").trim()
          },${(r.programme_code || "").trim()},${(r.category || "OPEN").trim()},${(
            r.admission_quota || "STATE_GOVT"
          ).trim()},${r.is_supernumerary ? "true" : "false"},${(r.nationality_type || "DOMESTIC").trim()}`
      )
      .join("\n");
    return header + body;
  };

  const handlePreflightFromGeneratedData = async () => {
    if (generatorRows.length === 0) {
      setError("Please generate or add at least one student record before running pre-flight validation.");
      return;
    }

    setIsUploading(true);
    setError(null);
    setPreflightData(null);
    setStagedRows([]);

    try {
      let uploadFile: File;
      const timestamp = Date.now();
      const token = typeof window !== "undefined" ? localStorage.getItem("pramaan_token") : null;

      if (builderFormat === "xlsx") {
        // Request genuine OpenXML XLSX binary from backend export engine
        const filename = `web_generated_${timestamp}.xlsx`;
        const resp = await fetch(`${API_BASE}/uploads/export-dataset`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
          },
          body: JSON.stringify({
            rows: generatorRows,
            format: "xlsx",
            filename: filename,
          }),
        });
        if (!resp.ok) {
          throw new Error("Failed to compile Excel dataset for preflight validation.");
        }
        const blob = await resp.blob();
        uploadFile = new File([blob], filename, {
          type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        });
      } else {
        // Compile RFC-4180 CSV
        const csvText = compileRowsToCsv(generatorRows);
        const blob = new Blob([csvText], { type: "text/csv;charset=utf-8;" });
        uploadFile = new File([blob], `web_generated_${timestamp}.csv`, { type: "text/csv" });
      }

      const formData = new FormData();
      formData.append("file", uploadFile);
      formData.append("institution_id", String(user?.institutionId || 2));
      formData.append("academic_year", "2026-27");

      const res = await apiRequest("/uploads/preflight", {
        method: "POST",
        body: formData,
      });
      setPreflightData(res);
      await loadStagedRows(res.batch_id);
      await loadBatches();
      const detectedPath = res.full_storage_path || res.storage_path_xlsx || res.storage_path_csv;
      setDownloadedFilePath(detectedPath);
      setSuccessMessage(
        `Pre-flight compilation complete for ${generatorRows.length} ${
          builderFormat === "xlsx" ? "Excel (.xlsx)" : "CSV (.csv)"
        } student records! Disk path: ${detectedPath}. Review findings below.`
      );
    } catch (err: any) {
      setError(err.message || "Failed to process generated dataset.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownloadGeneratedCsv = async () => {
    if (generatorRows.length === 0) {
      setError("No student records available to download.");
      return;
    }
    try {
      const filename = `student_admissions_${user?.aicteId || user?.institutionId || "college"}_${Date.now()}.csv`;
      const token = typeof window !== "undefined" ? localStorage.getItem("pramaan_token") : null;
      const resp = await fetch(`${API_BASE}/uploads/export-dataset`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          rows: generatorRows,
          format: "csv",
          filename: filename,
        }),
      });

      if (!resp.ok) {
        throw new Error(`Export failed with HTTP ${resp.status}`);
      }

      const storagePath = resp.headers.get("X-Storage-Path");
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      if (storagePath) {
        setDownloadedFilePath(storagePath);
        setSuccessMessage(`RFC-4180 CSV file downloaded successfully! System storage path: ${storagePath}`);
      } else {
        setSuccessMessage("Generated CSV file downloaded successfully!");
      }
    } catch (err: any) {
      setError(err.message || "Failed to download CSV file.");
    }
  };

  const handleDownloadGeneratedExcel = async () => {
    if (generatorRows.length === 0) {
      setError("No student records available to download.");
      return;
    }
    try {
      const filename = `student_admissions_${user?.aicteId || user?.institutionId || "college"}_${Date.now()}.xlsx`;
      const token = typeof window !== "undefined" ? localStorage.getItem("pramaan_token") : null;
      const resp = await fetch(`${API_BASE}/uploads/export-dataset`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          rows: generatorRows,
          format: "xlsx",
          filename: filename,
        }),
      });

      if (!resp.ok) {
        throw new Error(`Export failed with HTTP ${resp.status}`);
      }

      const storagePath = resp.headers.get("X-Storage-Path");
      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      if (storagePath) {
        setDownloadedFilePath(storagePath);
        setSuccessMessage(`Genuine OpenXML Excel (.xlsx) file downloaded successfully! Backing system disk path: ${storagePath}`);
      } else {
        setSuccessMessage("Genuine Excel spreadsheet downloaded successfully!");
      }
    } catch (err: any) {
      setError(err.message || "Failed to download Excel spreadsheet.");
    }
  };

  // Automatically initialize with 5 compliant students if table is empty
  useEffect(() => {
    if (user && generatorRows.length === 0) {
      handleAutoGenerateStudents(5, false);
    }
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
    setStagedRows([]);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("institution_id", String(user?.institutionId || 2));
    formData.append("academic_year", "2026-27");

    try {
      const res = await apiRequest("/uploads/preflight", {
        method: "POST",
        body: formData,
      });
      setPreflightData(res);
      await loadStagedRows(res.batch_id);
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
      setStagedRows([]);
      setFile(null);
      await loadBatches();
    } catch (err: any) {
      setError(err.message || "Failed to commit batch.");
    } finally {
      setIsCommitting(false);
    }
  };

  // Inspect existing batch from history directly into the web spreadsheet
  const handleInspectExistingBatch = async (batch: any) => {
    setError(null);
    setSuccessMessage(null);
    try {
      const batchDetail = await apiRequest(`/uploads/${batch.id}`);
      setPreflightData({
        batch_id: batch.id,
        filename: batch.filename,
        academic_year: batch.academic_year,
        total_rows: batch.total_rows,
        valid_rows: batch.valid_rows,
        warning_rows: batch.warning_rows,
        error_rows: batch.error_rows,
        mappings: batchDetail.batch.mapping_config || {},
        findings_preview: batchDetail.findings || [],
        storage_path_xlsx: batchDetail.batch.storage_path_xlsx,
        storage_path_csv: batchDetail.batch.storage_path_csv,
        full_storage_path: batchDetail.batch.full_storage_path,
        file_format: batchDetail.batch.file_format || (batch.filename?.endsWith(".xlsx") ? "XLSX" : "CSV"),
      });
      setDownloadedFilePath(batchDetail.batch.full_storage_path || batchDetail.batch.storage_path_xlsx || batchDetail.batch.storage_path_csv);
      await loadStagedRows(batch.id);
    } catch (err: any) {
      setError(err.message || "Failed to load batch spreadsheet.");
    }
  };

  // Inline Row Edit handlers
  const handleStartEdit = (row: any) => {
    setEditingRowId(row.id);
    setEditedValues({
      apaar_id: row.apaar_id || "",
      student_name: row.student_name || "",
      programme_code: row.programme_code || (approvedProgrammes[0]?.programme_code || "BTECH-CSE"),
      category: row.category || "OPEN",
      gender: row.gender || "MALE",
      admission_quota: row.admission_quota || "STATE_GOVT",
      dob: row.dob || "",
    });
  };

  const handleCancelEdit = () => {
    setEditingRowId(null);
    setEditedValues({});
  };

  const handleSaveRow = async (batchId: number, rowId: number) => {
    setIsSavingRow(true);
    setError(null);
    try {
      const res = await apiRequest(`/uploads/${batchId}/rows/${rowId}`, {
        method: "PATCH",
        body: JSON.stringify(editedValues),
      });
      setSuccessMessage(
        `Row #${res.staged_row.row_index} updated directly in database & backing file! Instant Python reconciliation: status is now ${res.staged_row.status}.`
      );
      setEditingRowId(null);
      setEditedValues({});

      // Refresh rows and preflight state
      await loadStagedRows(batchId);
      const batchDetail = await apiRequest(`/uploads/${batchId}`);
      setPreflightData((prev: any) => ({
        ...prev,
        valid_rows: batchDetail.batch.valid_rows,
        warning_rows: batchDetail.batch.warning_rows,
        error_rows: batchDetail.batch.error_rows,
        findings_preview: batchDetail.findings,
      }));
      await loadBatches();
    } catch (err: any) {
      setError(err.message || "Failed to save row update.");
    } finally {
      setIsSavingRow(false);
    }
  };

  // Quick-fix a single row's unknown programme
  const handleQuickFixRowProgramme = async (batchId: number, rowIndex: number, targetProg: string) => {
    const row = stagedRows.find((r) => r.row_index === rowIndex);
    if (!row) return;
    setIsSavingRow(true);
    setError(null);
    try {
      await apiRequest(`/uploads/${batchId}/rows/${row.id}`, {
        method: "PATCH",
        body: JSON.stringify({ programme_code: targetProg }),
      });
      setSuccessMessage(
        `Row #${rowIndex} programme code updated to approved offering '${targetProg}'. Re-validated by reconciliation engine!`
      );
      await loadStagedRows(batchId);
      const batchDetail = await apiRequest(`/uploads/${batchId}`);
      setPreflightData((prev: any) => ({
        ...prev,
        valid_rows: batchDetail.batch.valid_rows,
        warning_rows: batchDetail.batch.warning_rows,
        error_rows: batchDetail.batch.error_rows,
        findings_preview: batchDetail.findings,
      }));
      await loadBatches();
    } catch (err: any) {
      setError(err.message || "Failed to apply quick fix.");
    } finally {
      setIsSavingRow(false);
    }
  };

  // One-click batch fix all unknown programmes
  const handleQuickFixAllProgrammes = async (batchId: number) => {
    setIsQuickFixing(true);
    setError(null);
    try {
      const primaryProg = approvedProgrammes[0]?.programme_code || "BTECH-CSE";
      const res = await apiRequest(`/uploads/${batchId}/quick-fix`, {
        method: "POST",
        body: JSON.stringify({
          target_rule: "RULE_UNKNOWN_PROGRAMME",
          replacement_value: primaryProg,
        }),
      });
      setSuccessMessage(res.message);
      await loadStagedRows(batchId);
      const batchDetail = await apiRequest(`/uploads/${batchId}`);
      setPreflightData((prev: any) => ({
        ...prev,
        valid_rows: batchDetail.batch.valid_rows,
        warning_rows: batchDetail.batch.warning_rows,
        error_rows: batchDetail.batch.error_rows,
        findings_preview: batchDetail.findings,
      }));
      await loadBatches();
    } catch (err: any) {
      setError(err.message || "Failed to auto-fix programme discrepancies.");
    } finally {
      setIsQuickFixing(false);
    }
  };

  // Open Raw CSV Web Editor
  const handleOpenRawCsvEditor = () => {
    if (stagedRows.length === 0) return;
    const header = "apaar_id,student_name,dob,gender,programme_code,category,admission_quota\n";
    const body = stagedRows
      .map(
        (r) =>
          `${r.apaar_id || ""},${r.student_name || ""},${r.dob || ""},${r.gender || "MALE"},${
            r.programme_code || ""
          },${r.category || "OPEN"},${r.admission_quota || "STATE_GOVT"}`
      )
      .join("\n");
    setRawCsvText(header + body);
    setRawCsvModalOpen(true);
  };

  // Save Raw CSV from Web Editor
  const handleSaveRawCsv = async (batchId: number) => {
    setIsSavingRawCsv(true);
    setError(null);
    try {
      const res = await apiRequest(`/uploads/${batchId}/raw`, {
        method: "PUT",
        body: JSON.stringify({ csv_content: rawCsvText }),
      });
      setSuccessMessage(res.message);
      setRawCsvModalOpen(false);
      await loadStagedRows(batchId);
      const batchDetail = await apiRequest(`/uploads/${batchId}`);
      setPreflightData((prev: any) => ({
        ...prev,
        valid_rows: batchDetail.batch.valid_rows,
        warning_rows: batchDetail.batch.warning_rows,
        error_rows: batchDetail.batch.error_rows,
        findings_preview: batchDetail.findings,
      }));
      await loadBatches();
    } catch (err: any) {
      setError(err.message || "Failed to update raw CSV.");
    } finally {
      setIsSavingRawCsv(false);
    }
  };

  // Download Batch in Selected Format (Excel .xlsx or CSV .csv)
  const handleDownloadBatch = (batchId: number, format: "xlsx" | "csv" = "xlsx") => {
    window.open(`http://127.0.0.1:8000/api/v1/uploads/${batchId}/download?format=${format}`, "_blank");
  };

  const handleDownloadCsv = (batchId: number) => {
    handleDownloadBatch(batchId, "csv");
  };

  const primaryApprovedProg = approvedProgrammes[0]?.programme_code || "BTECH-CSE";
  const hasUnknownProgrammeErrors =
    preflightData?.findings_preview?.some((f: any) => f.rule_id === "RULE_UNKNOWN_PROGRAMME") || false;

  return (
    <div className="space-y-6">
      {/* Page Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Institutional Smart Uploader &amp; Live Spreadsheet Workspace
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Automated schema mapping, in-browser spreadsheet editing, APAAR checks, and real-time reconciliation.
          </p>
        </div>
        <div className="text-xs font-mono text-slate-600 bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
          Target Institution ID: #{user?.institutionId || 1} ({user?.institutionName || "DTU Delhi"})
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-xs flex items-center gap-2">
          <XCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Ingestion Mode Selector Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200">
        <button
          type="button"
          onClick={() => setIngestionMode("GENERATE_ON_WEB")}
          className={`pb-3 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition ${
            ingestionMode === "GENERATE_ON_WEB"
              ? "border-govTeal-600 text-govTeal-800 bg-govTeal-50/60 rounded-t-lg"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <Sparkles className="w-4 h-4 text-govTeal-600" />
          <span>✨ Generate &amp; Build Dataset on Web (Interactive Grid)</span>
          <span className="px-1.5 py-0.5 text-[10px] bg-govTeal-100 text-govTeal-800 rounded font-bold uppercase tracking-wider">
            Web Feature
          </span>
        </button>
        <button
          type="button"
          onClick={() => setIngestionMode("UPLOAD_FILE")}
          className={`pb-3 px-4 text-xs font-semibold flex items-center gap-2 border-b-2 transition ${
            ingestionMode === "UPLOAD_FILE"
              ? "border-govTeal-600 text-govTeal-800 bg-govTeal-50/60 rounded-t-lg"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          <UploadCloud className="w-4 h-4 text-slate-500" />
          <span>📁 Upload External Spreadsheet File (.csv, .xlsx)</span>
        </button>
      </div>

      {/* MODE 1: In-Browser Dataset Generator & Interactive Table Builder */}
      {ingestionMode === "GENERATE_ON_WEB" && (
        <div className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-sm font-bold text-slate-900">
                  In-Browser Student Admission Dataset Builder &amp; Generator
                </h2>
                <span className="px-2 py-0.5 bg-govTeal-100 text-govTeal-800 text-[11px] font-semibold rounded">
                  No External Excel Needed
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Generate synthetic batches matching {user?.institutionName || "your college"}&apos;s approved intake, manually add/edit student rows directly on the web, export to CSV/Excel, and compile straight to regulatory pre-flight validation.
              </p>
            </div>

            {/* Quick Generator Toolbar */}
            <div className="flex items-center flex-wrap gap-2">
              <button
                id="btn-quick-5"
                type="button"
                onClick={() => handleAutoGenerateStudents(5, false)}
                className="px-2.5 py-1.5 bg-govTeal-50 hover:bg-govTeal-100 text-govTeal-700 border border-govTeal-300 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                title="Generate 5 clean compliant records"
              >
                <Sparkles className="w-3.5 h-3.5 text-govTeal-600" />
                <span>Quick 5</span>
              </button>
              <button
                id="btn-quick-10"
                type="button"
                onClick={() => handleAutoGenerateStudents(10, false)}
                className="px-2.5 py-1.5 bg-govTeal-50 hover:bg-govTeal-100 text-govTeal-700 border border-govTeal-300 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                title="Generate 10 clean compliant records"
              >
                <Sparkles className="w-3.5 h-3.5 text-govTeal-600" />
                <span>Quick 10</span>
              </button>
              <button
                id="btn-test-discrepancies"
                type="button"
                onClick={() => handleAutoGenerateStudents(10, true)}
                className="px-2.5 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                title="Generate records with discrepancies to test audit rules"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Test Discrepancies (10)</span>
              </button>
              <button
                id="btn-add-row"
                type="button"
                onClick={handleAddBlankRow}
                className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 border border-slate-300 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Add Row</span>
              </button>

              <div className="h-5 w-[1px] bg-slate-300 mx-1 hidden sm:block" />

              {/* Target Format Selector Pill */}
              <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg border border-slate-200">
                <button
                  type="button"
                  onClick={() => setBuilderFormat("xlsx")}
                  className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                    builderFormat === "xlsx"
                      ? "bg-white text-emerald-800 shadow-2xs font-bold"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                  title="Target OpenXML Excel spreadsheet (.xlsx)"
                >
                  <span className="flex items-center gap-1">
                    <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Excel (.xlsx)</span>
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setBuilderFormat("csv")}
                  className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                    builderFormat === "csv"
                      ? "bg-white text-govTeal-800 shadow-2xs font-bold"
                      : "text-slate-500 hover:text-slate-800"
                  }`}
                  title="Target RFC-4180 CSV file (.csv)"
                >
                  <span className="flex items-center gap-1">
                    <FileDown className="w-3.5 h-3.5 text-govTeal-600" />
                    <span>CSV (.csv)</span>
                  </span>
                </button>
              </div>

              <button
                id="btn-download-excel"
                type="button"
                onClick={handleDownloadGeneratedExcel}
                disabled={generatorRows.length === 0}
                className="px-2.5 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 disabled:opacity-50 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                title="Download genuine styled Excel spreadsheet (.xlsx)"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                <span>Download Excel</span>
              </button>

              <button
                id="btn-download-csv"
                type="button"
                onClick={handleDownloadGeneratedCsv}
                disabled={generatorRows.length === 0}
                className="px-2.5 py-1.5 bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 disabled:opacity-50 rounded-lg text-xs font-medium flex items-center gap-1.5 transition cursor-pointer"
                title="Download RFC-4180 CSV file (.csv)"
              >
                <FileDown className="w-3.5 h-3.5 text-slate-600" />
                <span>Download CSV</span>
              </button>
            </div>
          </div>

          {/* Downloaded System File Path Banner */}
          {downloadedFilePath && (
            <div className="p-3 bg-emerald-50 border border-emerald-300 rounded-xl text-emerald-950 text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 shadow-2xs">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-4 h-4 text-emerald-600 shrink-0" />
                <div>
                  <span className="font-bold">System Storage File Path:</span>{" "}
                  <span className="font-mono text-[11px] bg-white px-2 py-0.5 rounded border border-emerald-200 text-emerald-800 select-all">
                    {downloadedFilePath}
                  </span>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setDownloadedFilePath(null)}
                className="text-emerald-700 hover:text-emerald-900 text-xs font-semibold self-end sm:self-auto"
              >
                Dismiss
              </button>
            </div>
          )}

          {/* Interactive Editable Table Grid */}
          <div className="border border-slate-200 rounded-xl overflow-hidden shadow-xs">
            <div className="max-h-[380px] overflow-x-auto overflow-y-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 sticky top-0 border-b border-slate-200 text-slate-700 font-semibold z-10">
                  <tr>
                    <th className="py-2.5 px-3 w-12 text-center">#</th>
                    <th className="py-2.5 px-3 min-w-[145px]">APAAR ID (12-Digit)</th>
                    <th className="py-2.5 px-3 min-w-[170px]">Student Full Name</th>
                    <th className="py-2.5 px-3 min-w-[115px]">Date of Birth</th>
                    <th className="py-2.5 px-3 min-w-[95px]">Gender</th>
                    <th className="py-2.5 px-3 min-w-[150px]">Approved Programme</th>
                    <th className="py-2.5 px-3 min-w-[105px]">Category</th>
                    <th className="py-2.5 px-3 min-w-[120px]">Quota</th>
                    <th className="py-2.5 px-3 min-w-[115px]">Supernumerary</th>
                    <th className="py-2.5 px-3 min-w-[130px]">Nationality / FN</th>
                    <th className="py-2.5 px-2 w-12 text-center">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 bg-white">
                  {generatorRows.length === 0 ? (
                    <tr>
                      <td colSpan={11} className="py-12 text-center text-slate-400">
                        <FileSpreadsheet className="w-8 h-8 mx-auto mb-2 opacity-50" />
                        <p className="font-medium text-slate-600">No student records staged yet</p>
                        <p className="text-[11px] text-slate-400 mt-1">
                          Click &quot;Quick 5&quot; or &quot;Add Row&quot; above to build your admission batch right here on the website.
                        </p>
                      </td>
                    </tr>
                  ) : (
                    generatorRows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/80 transition">
                        <td className="py-2 px-3 text-center text-slate-400 font-mono text-[11px]">
                          {idx + 1}
                        </td>
                        <td className="py-1.5 px-2">
                          <input
                            type="text"
                            maxLength={12}
                            value={row.apaar_id || ""}
                            onChange={(e) => handleUpdateGeneratorRow(idx, "apaar_id", e.target.value)}
                            placeholder="12 digit APAAR"
                            className="w-full px-2 py-1 text-xs font-mono border border-slate-200 rounded focus:border-govTeal-500 focus:outline-none"
                          />
                        </td>
                        <td className="py-1.5 px-2">
                          <input
                            type="text"
                            value={row.student_name || ""}
                            onChange={(e) => handleUpdateGeneratorRow(idx, "student_name", e.target.value)}
                            placeholder="Student Name"
                            className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:border-govTeal-500 focus:outline-none"
                          />
                        </td>
                        <td className="py-1.5 px-2">
                          <input
                            type="date"
                            value={row.dob || ""}
                            onChange={(e) => handleUpdateGeneratorRow(idx, "dob", e.target.value)}
                            className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:border-govTeal-500 focus:outline-none"
                          />
                        </td>
                        <td className="py-1.5 px-2">
                          <select
                            value={row.gender || "MALE"}
                            onChange={(e) => handleUpdateGeneratorRow(idx, "gender", e.target.value)}
                            className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:border-govTeal-500 focus:outline-none bg-white"
                          >
                            <option value="MALE">MALE</option>
                            <option value="FEMALE">FEMALE</option>
                            <option value="TRANSGENDER">TRANSGENDER</option>
                          </select>
                        </td>
                        <td className="py-1.5 px-2">
                          <select
                            value={row.programme_code || ""}
                            onChange={(e) => handleUpdateGeneratorRow(idx, "programme_code", e.target.value)}
                            className="w-full px-2 py-1 text-xs font-semibold text-slate-800 border border-slate-200 rounded focus:border-govTeal-500 focus:outline-none bg-white"
                          >
                            {approvedProgrammes.length > 0 ? (
                              approvedProgrammes.map((p) => (
                                <option key={p.id || p.programme_code} value={p.programme_code}>
                                  {p.programme_code} ({p.name || "Approved"})
                                </option>
                              ))
                            ) : (
                              <>
                                <option value="BTECH-CSE">BTECH-CSE (Computer Science)</option>
                                <option value="BTECH-ECE">BTECH-ECE (Electronics)</option>
                                <option value="BTECH-MECH">BTECH-MECH (Mechanical)</option>
                              </>
                            )}
                            <option value="INVALID-PROG">INVALID-PROG (Test Discrepancy)</option>
                          </select>
                        </td>
                        <td className="py-1.5 px-2">
                          <select
                            value={row.category || "OPEN"}
                            onChange={(e) => handleUpdateGeneratorRow(idx, "category", e.target.value)}
                            className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:border-govTeal-500 focus:outline-none bg-white"
                          >
                            <option value="OPEN">OPEN</option>
                            <option value="OBC_NCL">OBC_NCL</option>
                            <option value="SC">SC</option>
                            <option value="ST">ST</option>
                            <option value="EWS">EWS</option>
                          </select>
                        </td>
                        <td className="py-1.5 px-2">
                          <select
                            value={row.admission_quota || "STATE_GOVT"}
                            onChange={(e) => handleUpdateGeneratorRow(idx, "admission_quota", e.target.value)}
                            className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:border-govTeal-500 focus:outline-none bg-white"
                          >
                            <option value="STATE_GOVT">STATE_GOVT</option>
                            <option value="ALL_INDIA">ALL_INDIA</option>
                            <option value="MANAGEMENT">MANAGEMENT</option>
                            <option value="TFW">TFW (Tuition Fee Waiver)</option>
                          </select>
                        </td>
                        <td className="py-1.5 px-2">
                          <select
                            value={row.is_supernumerary ? "true" : "false"}
                            onChange={(e) => handleUpdateGeneratorRow(idx, "is_supernumerary", e.target.value === "true")}
                            className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:border-govTeal-500 focus:outline-none bg-white font-medium"
                          >
                            <option value="false">Sanctioned</option>
                            <option value="true">Supernumerary</option>
                          </select>
                        </td>
                        <td className="py-1.5 px-2">
                          <select
                            value={row.nationality_type || "DOMESTIC"}
                            onChange={(e) => handleUpdateGeneratorRow(idx, "nationality_type", e.target.value)}
                            className="w-full px-2 py-1 text-xs border border-slate-200 rounded focus:border-govTeal-500 focus:outline-none bg-white font-medium"
                          >
                            <option value="DOMESTIC">Indian / Domestic</option>
                            <option value="NRI">NRI Status</option>
                            <option value="OCI">OCI Status</option>
                            <option value="FOREIGN_NATIONAL">FN Status</option>
                          </select>
                        </td>
                        <td className="py-1.5 px-2 text-center">
                          <button
                            type="button"
                            onClick={() => handleRemoveGeneratorRow(idx)}
                            className="p-1 text-slate-400 hover:text-red-600 rounded transition cursor-pointer"
                            title="Delete Row"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Grid Footer with Stats & Preflight Action */}
            <div className="bg-slate-50 p-3 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-semibold text-slate-700">
                  Total Students: <span className="font-mono text-govTeal-700">{generatorRows.length}</span>
                </span>
                <span className="text-xs text-slate-400">|</span>
                <span className="text-xs text-slate-600 font-medium">
                  Target Pre-flight Format: <strong className="text-slate-900">{builderFormat === "xlsx" ? "Excel (.xlsx)" : "CSV (.csv)"}</strong>
                </span>
                {generatorRows.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setGeneratorRows([])}
                    className="text-[11px] text-slate-500 hover:text-red-600 underline"
                  >
                    Clear All
                  </button>
                )}
              </div>

              <button
                id="btn-compile-preflight"
                type="button"
                onClick={handlePreflightFromGeneratedData}
                disabled={generatorRows.length === 0 || isUploading}
                className="px-5 py-2.5 bg-gradient-to-r from-govTeal-600 to-govTeal-700 hover:from-govTeal-700 hover:to-govTeal-800 disabled:opacity-50 text-white rounded-lg text-xs font-bold shadow-sm flex items-center justify-center gap-2 transition cursor-pointer"
              >
                {isUploading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Compiling &amp; Validating Dataset...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5 fill-current" />
                    <span>Compile &amp; Pre-flight as {builderFormat === "xlsx" ? "Excel (.xlsx)" : "CSV (.csv)"}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* MODE 2: External File Drag-and-Drop Uploader */}
      {ingestionMode === "UPLOAD_FILE" && (
        <div className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs">
          <h2 className="text-sm font-bold text-slate-900 mb-1">Upload External Spreadsheet File</h2>
          <p className="text-xs text-slate-500 mb-4">
            Select or drag an existing institutional spreadsheet (.csv, .xlsx, .xls) containing APAAR numbers, student details, and programme codes.
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
                  {file ? file.name : "Click to browse or drop CSV/Excel file here"}
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Supports CSV, Excel (XLSX, XLS). You can modify errors directly on this website without reopening Excel.
                </p>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div className="text-xs text-slate-500 flex items-center gap-1.5">
                <Info className="w-4 h-4 text-govTeal-600" />
                <span>In-browser spreadsheet live correction active. No need to re-open external files.</span>
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
      )}

      {/* ========================================================================= */}
      {/* PRE-FLIGHT RESULTS & LIVE SPREADSHEET WORKSPACE                            */}
      {/* ========================================================================= */}
      {preflightData && (
        <div className="bg-white p-6 rounded-xl border border-govTeal-300 shadow-md space-y-6">
          {/* Header & Quick Action Buttons */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                <span className="px-2 py-0.5 rounded bg-govTeal-100 text-govTeal-800 text-xs font-mono font-bold">
                  Batch #{preflightData.batch_id}
                </span>
                <h3 className="text-sm font-bold text-slate-900">
                  Pre-flight Validation &amp; Live Spreadsheet Workspace
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                File: <span className="font-medium text-slate-700">{preflightData.filename}</span> | Academic Session: {preflightData.academic_year}
              </p>
            </div>

            <div className="flex items-center flex-wrap gap-2">
              {/* One-Click Auto-Fix Button (if unknown programme errors detected) */}
              {hasUnknownProgrammeErrors && (
                <button
                  onClick={() => handleQuickFixAllProgrammes(preflightData.batch_id)}
                  disabled={isQuickFixing}
                  className="px-3 py-1.5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition"
                  title="Automatically map unapproved programme codes to institution's approved offering"
                >
                  <Sparkles className={`w-3.5 h-3.5 ${isQuickFixing ? "animate-spin" : ""}`} />
                  <span>{isQuickFixing ? "Fixing..." : `Auto-Fix to ${primaryApprovedProg}`}</span>
                </button>
              )}

              {/* Edit Raw CSV Web Button */}
              <button
                onClick={handleOpenRawCsvEditor}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-300 flex items-center gap-1.5 transition"
                title="Edit raw CSV text directly in browser"
              >
                <Code className="w-3.5 h-3.5" />
                <span>Edit Raw CSV</span>
              </button>

              {/* Download Excel Button */}
              <button
                onClick={() => handleDownloadBatch(preflightData.batch_id, "xlsx")}
                className="px-3 py-1.5 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded-lg text-xs font-semibold border border-emerald-300 flex items-center gap-1.5 transition cursor-pointer"
                title="Download genuine OpenXML Excel spreadsheet (.xlsx)"
              >
                <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
                <span>Download Excel (.xlsx)</span>
              </button>

              {/* Download Corrected CSV Button */}
              <button
                onClick={() => handleDownloadBatch(preflightData.batch_id, "csv")}
                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold border border-slate-300 flex items-center gap-1.5 transition cursor-pointer"
                title="Download RFC-4180 CSV file (.csv)"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download CSV</span>
              </button>

              {/* Commit & Submit to AICTE Button */}
              {preflightData.status === "APPROVED" || preflightData.status === "SUBMITTED" ? (
                <div className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-300 flex items-center gap-1.5 shadow-xs">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Submitted to AICTE ({preflightData.status})</span>
                </div>
              ) : (
                <button
                  onClick={() => handleCommitBatch(preflightData.batch_id)}
                  disabled={isCommitting}
                  className={`px-4 py-1.5 rounded-lg text-xs font-semibold shadow-sm flex items-center gap-2 transition ${
                    preflightData.error_rows === 0
                      ? "bg-emerald-600 hover:bg-emerald-700 text-white ring-2 ring-emerald-400 cursor-pointer"
                      : "bg-govNavy-900 hover:bg-govNavy-800 text-white cursor-pointer"
                  }`}
                >
                  {isCommitting ? (
                    <>
                      <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                      <span>Committing Batch...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5 text-govTeal-400" />
                      <span>
                        {preflightData.error_rows === 0
                          ? "0 Errors — Commit & Submit to AICTE"
                          : "Commit & Submit to AICTE"}
                      </span>
                    </>
                  )}
                </button>
              )}
            </div>
          </div>

          {/* Live File Storage & Disk Artifacts Hub */}
          <div className="p-4 bg-gradient-to-r from-slate-900 to-govNavy-950 text-white rounded-xl shadow-sm border border-slate-700/60 space-y-3">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-0.5 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-mono font-bold rounded">
                    ACTIVE DISK STORAGE ARTIFACTS
                  </span>
                  <span className="text-xs font-semibold text-slate-200">
                    Ingestion Format: {preflightData.file_format || (preflightData.filename?.endsWith(".xlsx") ? "XLSX" : "CSV")}
                  </span>
                </div>
                <div className="text-xs font-mono text-slate-300 break-all flex items-center gap-1.5">
                  <span className="text-slate-400">Disk Path:</span>
                  <span className="bg-slate-800/80 px-2 py-0.5 rounded border border-slate-700 text-govTeal-300 select-all">
                    {preflightData.full_storage_path || preflightData.storage_path_xlsx || preflightData.storage_path_csv || "storage/uploads/..."}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400">
                  Real-time disk synchronization: cell modifications and batch fixes update both genuine OpenXML (.xlsx) and RFC-4180 (.csv) on the server.
                </p>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  onClick={() => handleDownloadBatch(preflightData.batch_id, "xlsx")}
                  className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-xs cursor-pointer"
                  title="Download genuine styled Excel spreadsheet (.xlsx)"
                >
                  <FileSpreadsheet className="w-3.5 h-3.5" />
                  <span>Download Excel (.xlsx)</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleDownloadBatch(preflightData.batch_id, "csv")}
                  className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
                  title="Download RFC-4180 CSV file (.csv)"
                >
                  <FileDown className="w-3.5 h-3.5" />
                  <span>Download CSV (.csv)</span>
                </button>
              </div>
            </div>
          </div>

          {/* Validation Tally Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200 shadow-2xs">
              <div className="text-xs text-slate-500 font-semibold">Total Rows</div>
              <div className="text-2xl font-extrabold text-slate-900 mt-1">{preflightData.total_rows}</div>
            </div>
            <div className="p-3.5 bg-emerald-50 rounded-xl border border-emerald-200 shadow-2xs">
              <div className="text-xs text-emerald-700 font-semibold">Valid &amp; Verified</div>
              <div className="text-2xl font-extrabold text-emerald-800 mt-1">{preflightData.valid_rows}</div>
            </div>
            <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200 shadow-2xs">
              <div className="text-xs text-amber-700 font-semibold">Warnings / Review</div>
              <div className="text-2xl font-extrabold text-amber-800 mt-1">{preflightData.warning_rows}</div>
            </div>
            <div className={`p-3.5 rounded-xl border shadow-2xs ${
              preflightData.error_rows > 0 ? "bg-rose-50 border-rose-300 ring-1 ring-rose-200" : "bg-emerald-50 border-emerald-200"
            }`}>
              <div className={`text-xs font-semibold ${preflightData.error_rows > 0 ? "text-rose-700" : "text-emerald-700"}`}>
                Hard Errors
              </div>
              <div className={`text-2xl font-extrabold mt-1 ${preflightData.error_rows > 0 ? "text-rose-800" : "text-emerald-800"}`}>
                {preflightData.error_rows}
              </div>
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
                  className="px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 flex items-center gap-1.5"
                >
                  <span className="font-mono text-slate-500">{incoming}</span>
                  <span className="text-slate-400">&rarr;</span>
                  <span className="font-semibold text-govTeal-700">{String(canonical)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Row-Level Findings Table with Direct In-Row Quick Fix Buttons */}
          {preflightData.findings_preview && preflightData.findings_preview.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Row-Level Findings &amp; Actionable Guidance
                </h4>
                {hasUnknownProgrammeErrors && (
                  <span className="text-[11px] text-purple-700 font-semibold flex items-center gap-1">
                    <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                    <span>Single-click quick-fixes available below</span>
                  </span>
                )}
              </div>

              <div className="border border-slate-200 rounded-lg overflow-x-auto shadow-2xs">
                <table className="w-full text-xs text-left">
                  <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px] tracking-wider">
                    <tr>
                      <th className="px-3 py-2.5 w-12 text-center">Row</th>
                      <th className="px-3 py-2.5 w-20">Severity</th>
                      <th className="px-3 py-2.5 min-w-[140px]">Rule ID</th>
                      <th className="px-3 py-2.5 min-w-[220px]">Finding Message</th>
                      <th className="px-3 py-2.5 min-w-[200px]">Recommended Next Action</th>
                      <th className="px-3 py-2.5 text-right min-w-[120px]">Quick Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {preflightData.findings_preview.map((f: any, idx: number) => {
                      const isUnknownProg = f.rule_id === "RULE_UNKNOWN_PROGRAMME";
                      return (
                        <tr key={idx} className={`hover:bg-slate-50 transition ${f.severity === "ERROR" ? "bg-rose-50/40" : ""}`}>
                          <td className="px-3 py-2 font-mono font-bold text-slate-600 text-center">#{f.row_index}</td>
                          <td className="px-3 py-2">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                                f.severity === "ERROR"
                                  ? "bg-rose-100 text-rose-800 border border-rose-300"
                                  : f.severity === "WARNING"
                                  ? "bg-amber-100 text-amber-800 border border-amber-300"
                                  : "bg-blue-100 text-blue-800 border border-blue-300"
                              }`}
                            >
                              {f.severity}
                            </span>
                          </td>
                          <td className="px-3 py-2 font-mono text-slate-700 font-semibold">{f.rule_id}</td>
                          <td className="px-3 py-2 text-slate-800 font-medium">{f.message}</td>
                          <td className="px-3 py-2 text-slate-600">{f.recommended_action || "—"}</td>
                          <td className="px-3 py-2 text-right">
                            {isUnknownProg ? (
                              <button
                                onClick={() => handleQuickFixRowProgramme(preflightData.batch_id, f.row_index, primaryApprovedProg)}
                                disabled={isSavingRow}
                                className="px-2 py-1 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded text-[11px] font-semibold flex items-center gap-1 shadow-2xs ml-auto transition"
                                title={`Change programme to approved offering '${primaryApprovedProg}'`}
                              >
                                <Sparkles className="w-3 h-3" />
                                <span>Fix to {primaryApprovedProg}</span>
                              </button>
                            ) : (
                              <button
                                onClick={() => {
                                  const r = stagedRows.find((sr) => sr.row_index === f.row_index);
                                  if (r) handleStartEdit(r);
                                }}
                                className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium flex items-center gap-1 ml-auto transition"
                              >
                                <Edit2 className="w-3 h-3" />
                                <span>Edit Cell</span>
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Quick link to Full Adjudication & AICTE Central Advisories */}
          <div className="p-3 bg-gradient-to-r from-amber-500/10 via-teal-500/10 to-indigo-500/10 border border-amber-500/30 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <div className="flex items-center gap-2 text-slate-800">
              <Sparkles className="w-4 h-4 text-amber-600 flex-shrink-0" />
              <span>
                <strong>AICTE Central Governance &amp; Advisory Workspace:</strong> Central government officers can provide policy dispensations and remediation ideas for this batch.
              </span>
            </div>
            <Link
              href={`/uploads/${preflightData.batch_id}`}
              className="px-3 py-1 bg-amber-600 hover:bg-amber-700 text-white font-bold rounded-lg transition flex items-center gap-1 flex-shrink-0 self-start sm:self-auto"
            >
              <span>View AICTE Advisories</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          {/* ========================================================================= */}
          {/* SECTION: INTERACTIVE IN-BROWSER SPREADSHEET (FRONT OF PAGE)                */}
          {/* ========================================================================= */}
          <div className="pt-2 border-t border-slate-200">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
              <div className="flex items-center gap-2">
                <FileSpreadsheet className="w-5 h-5 text-govTeal-600" />
                <div>
                  <h4 className="text-sm font-bold text-slate-900">
                    Live In-Browser Staged Spreadsheet ({stagedRows.length} Rows)
                  </h4>
                  <p className="text-xs text-slate-500">
                    Modify cell values directly right here. Deterministic Python algorithms re-verify all 3-way rules instantaneously.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-[11px] text-slate-500 flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Discrepancy Cell
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 ml-2"></span> Needs Review
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 ml-2"></span> Verified
                </span>
              </div>
            </div>

            {loadingRows ? (
              <div className="py-8 text-center text-xs text-slate-500 flex flex-col items-center gap-2">
                <RefreshCw className="w-5 h-5 animate-spin text-slate-400" />
                <span>Loading staged records...</span>
              </div>
            ) : (
              <div className="border border-slate-200 rounded-lg overflow-x-auto shadow-2xs">
                <table className="w-full text-xs text-left border-collapse">
                  <thead className="bg-slate-100 text-slate-700 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="px-3 py-2.5 w-12 text-center">Row</th>
                      <th className="px-3 py-2.5 min-w-[150px]">Student Name</th>
                      <th className="px-3 py-2.5 min-w-[150px]">APAAR ID</th>
                      <th className="px-3 py-2.5 min-w-[140px]">Programme Code</th>
                      <th className="px-3 py-2.5 min-w-[90px]">Category</th>
                      <th className="px-3 py-2.5 min-w-[80px]">Gender</th>
                      <th className="px-3 py-2.5 min-w-[110px]">Quota</th>
                      <th className="px-3 py-2.5 min-w-[130px]">Status</th>
                      <th className="px-3 py-2.5 text-right min-w-[150px]">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-200">
                    {stagedRows.map((row: any) => {
                      const isEditing = editingRowId === row.id;
                      const hasErrors = row.status === "BLOCKING_ERROR";
                      const hasWarnings = row.status === "REQUIRES_REVIEW";

                      // Check if programme code is invalid/unapproved
                      const isProgrammeError = row.findings?.some((f: any) => f.rule_id === "RULE_UNKNOWN_PROGRAMME");

                      const rowBg = hasErrors
                        ? "bg-rose-50/70 hover:bg-rose-100/50"
                        : hasWarnings
                        ? "bg-amber-50/60 hover:bg-amber-100/40"
                        : "hover:bg-slate-50";

                      return (
                        <tr key={row.id} className={`transition ${rowBg} ${isEditing ? "bg-blue-50/70 ring-1 ring-blue-400" : ""}`}>
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
                                placeholder="12 numeric digits"
                                className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                              />
                            ) : (
                              <div className="font-medium text-slate-800">
                                {row.apaar_id || <span className="text-rose-600 font-bold italic">Missing APAAR</span>}
                              </div>
                            )}
                          </td>

                          {/* Programme Code (with highlighting on invalid offerings) */}
                          <td className="px-3 py-2 font-mono">
                            {isEditing ? (
                              <select
                                value={editedValues.programme_code}
                                onChange={(e) => setEditedValues({ ...editedValues, programme_code: e.target.value })}
                                className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none focus:ring-1 focus:ring-blue-500 uppercase font-mono font-bold text-slate-900"
                              >
                                {approvedProgrammes.map((p) => (
                                  <option key={p.id} value={p.programme_code}>
                                    {p.programme_code} ({p.programme_name})
                                  </option>
                                ))}
                                {/* If current invalid code not in list, keep as selectable option */}
                                {!approvedProgrammes.some((p) => p.programme_code === editedValues.programme_code) && (
                                  <option value={editedValues.programme_code}>
                                    {editedValues.programme_code} [Unapproved]
                                  </option>
                                )}
                              </select>
                            ) : (
                              <div>
                                <span className={`font-bold ${isProgrammeError ? "text-rose-700 bg-rose-100 px-1.5 py-0.5 rounded border border-rose-300" : "text-slate-800"}`}>
                                  {row.programme_code || "—"}
                                </span>
                                {isProgrammeError && (
                                  <span className="block text-[10px] text-rose-600 font-medium mt-0.5">
                                    Not Approved &bull; Use {primaryApprovedProg}
                                  </span>
                                )}
                              </div>
                            )}
                          </td>

                          {/* Category */}
                          <td className="px-3 py-2">
                            {isEditing ? (
                              <select
                                value={editedValues.category}
                                onChange={(e) => setEditedValues({ ...editedValues, category: e.target.value })}
                                className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none font-medium"
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
                                className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none font-medium"
                              >
                                <option value="MALE">MALE</option>
                                <option value="FEMALE">FEMALE</option>
                                <option value="OTHER">OTHER</option>
                              </select>
                            ) : (
                              <span className="text-slate-600">{row.gender}</span>
                            )}
                          </td>

                          {/* Quota */}
                          <td className="px-3 py-2">
                            {isEditing ? (
                              <select
                                value={editedValues.admission_quota}
                                onChange={(e) => setEditedValues({ ...editedValues, admission_quota: e.target.value })}
                                className="w-full text-xs p-1.5 rounded border border-blue-400 bg-white focus:outline-none font-medium"
                              >
                                <option value="STATE_GOVT">STATE_GOVT</option>
                                <option value="MANAGEMENT">MANAGEMENT</option>
                                <option value="AICTE_TFW">AICTE_TFW</option>
                                <option value="NRI">NRI</option>
                                <option value="TFW">TFW</option>
                              </select>
                            ) : (
                              <span className="text-slate-600 font-medium">{row.admission_quota}</span>
                            )}
                          </td>

                          {/* Status */}
                          <td className="px-3 py-2">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
                                row.status === "BLOCKING_ERROR"
                                  ? "bg-rose-100 text-rose-800 border-rose-300"
                                  : row.status === "REQUIRES_REVIEW"
                                  ? "bg-amber-100 text-amber-800 border-amber-300"
                                  : "bg-emerald-100 text-emerald-800 border-emerald-300"
                              }`}
                            >
                              {row.status}
                            </span>
                          </td>

                          {/* Actions */}
                          <td className="px-3 py-2 text-right">
                            <div className="flex items-center justify-end gap-1.5">
                              {isEditing ? (
                                <>
                                  <button
                                    onClick={() => handleSaveRow(preflightData.batch_id, row.id)}
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

                                  {isProgrammeError && (
                                    <button
                                      onClick={() => handleQuickFixRowProgramme(preflightData.batch_id, row.row_index, primaryApprovedProg)}
                                      disabled={isSavingRow}
                                      className="px-2 py-1 bg-purple-50 hover:bg-purple-100 text-purple-700 border border-purple-200 rounded text-xs font-semibold flex items-center gap-1 transition"
                                      title={`Auto-correct to ${primaryApprovedProg}`}
                                    >
                                      <Sparkles className="w-3 h-3" />
                                      <span>Fix to {primaryApprovedProg}</span>
                                    </button>
                                  )}
                                </>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================================= */}
      {/* RAW CSV LIVE TEXT EDITOR MODAL                                            */}
      {/* ========================================================================= */}
      {rawCsvModalOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/80 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full border border-slate-200 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-200 pb-3">
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5 text-govTeal-600" />
                <h3 className="text-sm font-bold text-slate-900">
                  Live CSV Text Editor (Batch #{preflightData?.batch_id})
                </h3>
              </div>
              <button
                onClick={() => setRawCsvModalOpen(false)}
                className="p-1 rounded text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <p className="text-xs text-slate-500">
              Directly edit the raw comma-separated values in your browser. Saving updates both the backing storage file and the database, followed by immediate Python re-reconciliation.
            </p>

            <textarea
              value={rawCsvText}
              onChange={(e) => setRawCsvText(e.target.value)}
              rows={12}
              className="w-full text-xs font-mono p-3 bg-slate-900 text-emerald-400 rounded-lg border border-slate-700 focus:outline-none focus:ring-2 focus:ring-govTeal-500"
              spellCheck={false}
            />

            <div className="flex items-center justify-between pt-2 border-t border-slate-200">
              <div className="text-[11px] text-slate-500 font-mono">
                {rawCsvText.split("\n").filter((l) => l.trim().length > 0).length - 1} data records detected
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setRawCsvModalOpen(false)}
                  className="px-3 py-1.5 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveRawCsv(preflightData.batch_id)}
                  disabled={isSavingRawCsv}
                  className="px-4 py-1.5 bg-govTeal-600 hover:bg-govTeal-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition"
                >
                  <Save className={`w-3.5 h-3.5 ${isSavingRawCsv ? "animate-spin" : ""}`} />
                  <span>{isSavingRawCsv ? "Re-validating..." : "Save Raw CSV & Re-validate"}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Batch Upload History */}
      <div className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs">
        <h2 className="text-sm font-bold text-slate-900 mb-1">Ingestion Batch History</h2>
        <p className="text-xs text-slate-500 mb-4">Historical upload batches, status, and reconciliation outcomes.</p>

        <div className="border border-slate-200 rounded-lg overflow-x-auto shadow-2xs">
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
                <th className="px-3 py-2.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {batches.map((b) => (
                <tr key={b.id} className="hover:bg-slate-50 transition">
                  <td className="px-3 py-2 font-mono font-bold text-slate-900">#{b.id}</td>
                  <td className="px-3 py-2">
                    <div className="font-medium text-slate-800 flex items-center gap-1.5">
                      <span>{b.filename}</span>
                      <span className={`px-1.5 py-0.2 rounded text-[9px] font-mono font-bold uppercase ${
                        (b.file_format === "XLSX" || b.filename?.endsWith(".xlsx"))
                          ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                          : "bg-slate-100 text-slate-700 border border-slate-300"
                      }`}>
                        {b.file_format || (b.filename?.endsWith(".xlsx") ? "XLSX" : "CSV")}
                      </span>
                    </div>
                    {(b.full_storage_path || b.storage_path_xlsx || b.storage_path_csv) && (
                      <div className="text-[10px] font-mono text-slate-400 truncate max-w-[220px]" title={b.full_storage_path || b.storage_path_xlsx || b.storage_path_csv}>
                        {b.full_storage_path || b.storage_path_xlsx || b.storage_path_csv}
                      </div>
                    )}
                  </td>
                  <td className="px-3 py-2 font-mono text-slate-600">{b.academic_year}</td>
                  <td className="px-3 py-2 font-semibold text-slate-900">{b.total_rows}</td>
                  <td className="px-3 py-2 text-emerald-600 font-semibold">{b.valid_rows}</td>
                  <td className="px-3 py-2 text-amber-600 font-semibold">{b.warning_rows}</td>
                  <td className="px-3 py-2 text-rose-600 font-semibold">{b.error_rows}</td>
                  <td className="px-3 py-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        b.status === "APPROVED"
                          ? "bg-emerald-100 text-emerald-800"
                          : b.status === "COMMITTED"
                          ? "bg-blue-100 text-blue-800"
                          : b.status === "REJECTED_NEEDS_CORRECTION" || b.status === "RETURNED_FOR_CORRECTION"
                          ? "bg-rose-100 text-rose-800"
                          : "bg-amber-100 text-amber-800"
                      }`}
                    >
                      {b.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-slate-500 font-mono">
                    {new Date(b.created_at).toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <div className="flex items-center justify-end gap-1.5 flex-wrap">
                      <button
                        onClick={() => handleInspectExistingBatch(b)}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-govTeal-700 hover:text-govTeal-900 hover:underline cursor-pointer"
                        title="Open interactive spreadsheet directly on this page"
                      >
                        <FileSpreadsheet className="w-3 h-3" />
                        <span>Open Sheet</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDownloadBatch(b.id, "xlsx")}
                        className="inline-flex items-center gap-0.5 text-[10px] font-semibold text-emerald-700 hover:text-emerald-900 bg-emerald-50 hover:bg-emerald-100 px-1.5 py-0.5 rounded border border-emerald-200 transition cursor-pointer"
                        title="Download genuine OpenXML Excel spreadsheet (.xlsx)"
                      >
                        <FileSpreadsheet className="w-3 h-3 text-emerald-600" />
                        <span>Excel</span>
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDownloadBatch(b.id, "csv")}
                        className="inline-flex items-center gap-0.5 text-[10px] font-semibold text-slate-700 hover:text-slate-900 bg-slate-100 hover:bg-slate-200 px-1.5 py-0.5 rounded border border-slate-300 transition cursor-pointer"
                        title="Download RFC-4180 CSV file (.csv)"
                      >
                        <FileDown className="w-3 h-3 text-slate-600" />
                        <span>CSV</span>
                      </button>
                      <Link
                        href={`/uploads/${b.id}`}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-govNavy-700 hover:text-govNavy-950 hover:underline"
                      >
                        Details &rarr;
                      </Link>
                    </div>
                  </td>
                </tr>
              ))}
              {batches.length === 0 && (
                <tr>
                  <td colSpan={10} className="px-3 py-6 text-center text-slate-400">
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
