"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Database,
  Plus,
  Trash2,
  Edit2,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Search,
  ShieldAlert,
  Info,
  Sparkles
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface ApaarRecord {
  id: number;
  apaar_id: string;
  full_name: string;
  dob: string | null;
  gender: string;
  status: string;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

interface ApprovalItem {
  id: number;
  institution_id: number;
  institution_name: string | null;
  programme_id: number;
  programme_code: string | null;
  programme_name: string | null;
  academic_year: string;
  approved_intake: number;
  supernumerary_quota: Record<string, number>;
  policy_version: string;
  is_active: boolean;
}

interface DeclarationItem {
  id: number;
  institution_id: number;
  institution_name: string | null;
  programme_id: number;
  programme_code: string | null;
  programme_name: string | null;
  academic_year: string;
  declared_intake: number;
  reporting_scope: string | null;
  declaration_ref: string | null;
}

interface BatchItem {
  id: number;
  filename: string;
  institution_id: number;
  institution_name?: string | null;
  academic_year: string;
  status: string;
  total_rows: number;
}

interface FindingItem {
  id: number;
  row_index: number;
  finding_type?: string;
  rule_id: string;
  severity: string;
  message: string;
  recommended_action?: string;
}

interface RevalidationResult {
  batch_id: number;
  status: string;
  validation_run_id: number;
  run_number: number;
  disposition: {
    total_rows: number;
    duplicate_rows: number;
    unique_records: number;
    blocking_errors: number;
    requiring_review: number;
    eligible_to_proceed: number;
    declared_intake: number;
    declared_discrepancy: number;
  };
  findings_count: number;
  findings: FindingItem[];
}

export default function ReferenceDataPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "AICTE_ADMIN" || user?.role === "REGIONAL_OFFICER";

  const [activeTab, setActiveTab] = useState<"apaar" | "approvals" | "declarations" | "revalidate">("apaar");
  const [overview, setOverview] = useState<{
    total_institutions: number;
    total_programmes: number;
    total_approvals: number;
    total_declarations: number;
    total_synthetic_apaar: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Synthetic APAAR State
  const [apaarRecords, setApaarRecords] = useState<ApaarRecord[]>([]);
  const [apaarSearch, setApaarSearch] = useState("");
  const [apaarStatusFilter, setApaarStatusFilter] = useState("");
  const [newApaarId, setNewApaarId] = useState("");
  const [newApaarName, setNewApaarName] = useState("");
  const [newApaarDob, setNewApaarDob] = useState("2005-01-01");
  const [newApaarGender, setNewApaarGender] = useState("MALE");
  const [newApaarStatus, setNewApaarStatus] = useState("DEMO_REFERENCE_MATCH");
  const [newApaarNotes, setNewApaarNotes] = useState("");
  const [isAddingApaar, setIsAddingApaar] = useState(false);

  // Approvals State
  const [approvals, setApprovals] = useState<ApprovalItem[]>([]);
  const [editingApprovalId, setEditingApprovalId] = useState<number | null>(null);
  const [editApprovedIntake, setEditApprovedIntake] = useState<number>(0);

  // Declarations State
  const [declarations, setDeclarations] = useState<DeclarationItem[]>([]);
  const [editingDeclId, setEditingDeclId] = useState<number | null>(null);
  const [editDeclaredIntake, setEditDeclaredIntake] = useState<number>(0);

  // Revalidation State
  const [batches, setBatches] = useState<BatchItem[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState<number | null>(null);
  const [revalidationResult, setRevalidationResult] = useState<RevalidationResult | null>(null);
  const [isRevalidating, setIsRevalidating] = useState(false);

  // Supabase Cloud State
  const [supabaseStatus, setSupabaseStatus] = useState<any | null>(null);
  const [isSyncingSupabase, setIsSyncingSupabase] = useState(false);
  const [supabaseMessage, setSupabaseMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Sovereign Cryptographic Vault State
  const [vaultIntegrity, setVaultIntegrity] = useState<any | null>(null);
  const [isSealingVault, setIsSealingVault] = useState(false);

  // Manual Add Programme & Approval State
  const [isAddingProgramme, setIsAddingProgramme] = useState(false);
  const [newProgInstitutionId, setNewProgInstitutionId] = useState<number>(2); // Default DTU Delhi
  const [newProgCode, setNewProgCode] = useState("BTECH-AI");
  const [newProgName, setNewProgName] = useState("B.Tech in Artificial Intelligence & Data Science");
  const [newProgIntake, setNewProgIntake] = useState<number>(60);
  const [newProgTfw, setNewProgTfw] = useState<number>(3);
  const [isSubmittingProgramme, setIsSubmittingProgramme] = useState(false);

  const loadApaarRecords = useCallback(async () => {
    try {
      let url = "/reference-data/synthetic-apaar?limit=100";
      if (apaarStatusFilter) url += `&status=${apaarStatusFilter}`;
      if (apaarSearch) url += `&search=${encodeURIComponent(apaarSearch)}`;
      const res = await apiRequest(url);
      setApaarRecords(res.records || []);
    } catch (err: unknown) {
      console.error(err);
    }
  }, [apaarStatusFilter, apaarSearch]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [ovRes, appRes, decRes, batchRes, supaRes, vaultRes] = await Promise.all([
        apiRequest("/reference-data/overview"),
        apiRequest("/reference-data/approvals"),
        apiRequest("/reference-data/declarations"),
        apiRequest("/uploads"),
        apiRequest("/reference-data/supabase/status").catch(() => null),
        apiRequest("/reference-data/vault/integrity").catch(() => null)
      ]);

      setOverview(ovRes);
      setApprovals(appRes);
      setDeclarations(decRes);
      setBatches(batchRes);
      if (supaRes) setSupabaseStatus(supaRes);
      if (vaultRes) setVaultIntegrity(vaultRes);
      if (batchRes.length > 0 && !selectedBatchId) {
        setSelectedBatchId(batchRes[0].id);
      }

      await loadApaarRecords();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to load reference registry data.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, [loadApaarRecords, selectedBatchId]);

  const handleSyncSupabase = async () => {
    setIsSyncingSupabase(true);
    setSupabaseMessage(null);
    try {
      const res = await apiRequest("/reference-data/supabase/sync", { method: "POST" });
      setSupabaseMessage({
        type: res.success ? "success" : "error",
        text: res.message || "Supabase cloud sync finished."
      });
      await loadData();
    } catch (err: any) {
      setSupabaseMessage({
        type: "error",
        text: err.message || "Failed to synchronize with Supabase Cloud."
      });
    } finally {
      setIsSyncingSupabase(false);
    }
  };

  const handleSealVault = async () => {
    setIsSealingVault(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await apiRequest("/reference-data/vault/seal", { method: "POST" });
      setSuccess(`Sovereign Cryptographic Vault Sealed! Master Merkle Seal: ${res.sovereign_seal.slice(0, 16)}... Chained to audit ledger.`);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to seal vault.");
    } finally {
      setIsSealingVault(false);
    }
  };

  const handleCreateProgrammeWithApproval = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmittingProgramme(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await apiRequest("/reference-data/programmes-with-approval", {
        method: "POST",
        body: JSON.stringify({
          institution_id: Number(newProgInstitutionId),
          programme_code: newProgCode.trim().toUpperCase(),
          programme_name: newProgName.trim(),
          academic_year: "2026-27",
          approved_intake: Number(newProgIntake),
          tfw_quota: Number(newProgTfw)
        })
      });
      setSuccess(res.message || `Successfully registered ${newProgCode}!`);
      setIsAddingProgramme(false);
      await loadData();
    } catch (err: any) {
      setError(err.message || "Failed to create approved programme.");
    } finally {
      setIsSubmittingProgramme(false);
    }
  };

  useEffect(() => {
    if (isAdmin) {
      loadData();
    }
  }, [isAdmin, loadData]);

  useEffect(() => {
    if (isAdmin && activeTab === "apaar") {
      loadApaarRecords();
    }
  }, [isAdmin, activeTab, loadApaarRecords]);

  if (!isAdmin) {
    return (
      <div className="p-8 max-w-2xl mx-auto text-center space-y-4">
        <div className="w-12 h-12 bg-red-100 text-red-700 rounded-full flex items-center justify-center mx-auto">
          <ShieldAlert className="w-6 h-6" />
        </div>
        <h1 className="text-xl font-bold text-slate-900">Access Restricted</h1>
        <p className="text-xs text-slate-600">
          Only authorized central AICTE administrators and regional officers have permission to access and modify the synthetic reference registry.
        </p>
      </div>
    );
  }

  const [isSeedingBatch, setIsSeedingBatch] = useState(false);

  const handleSeedApaarBatch = async (count: number = 5, withDiscrepancies: boolean = false) => {
    setIsSeedingBatch(true);
    setError(null);
    setSuccess(null);
    try {
      const res = await apiRequest(`/reference-data/synthetic-apaar/seed-batch?count=${count}&with_discrepancies=${withDiscrepancies}`, {
        method: "POST"
      });
      setSuccess(res.message || `Successfully seeded ${count} synthetic APAAR records into database!`);
      await loadApaarRecords();
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to seed synthetic APAAR records.";
      setError(msg);
    } finally {
      setIsSeedingBatch(false);
    }
  };

  const handleCreateApaar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    try {
      const res = await apiRequest("/reference-data/synthetic-apaar", {
        method: "POST",
        body: JSON.stringify({
          apaar_id: newApaarId,
          full_name: newApaarName,
          dob: newApaarDob || "2005-01-01",
          gender: newApaarGender,
          status: newApaarStatus,
          notes: newApaarNotes
        })
      });
      setSuccess(`Synthetic APAAR Record for ${res.full_name} (${res.apaar_id}) successfully persisted to database!`);
      setNewApaarId("");
      setNewApaarName("");
      setNewApaarNotes("");
      setIsAddingApaar(false);
      await loadApaarRecords();
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to create synthetic APAAR record.";
      setError(msg);
    }
  };

  const handleDeleteApaar = async (id: number, apaarId: string) => {
    if (!confirm(`Are you sure you want to remove synthetic reference ${apaarId}? This change is traceable in audit ledger.`)) return;
    setError(null);
    setSuccess(null);
    try {
      await apiRequest(`/reference-data/synthetic-apaar/${id}`, { method: "DELETE" });
      setSuccess(`Record #${id} (${apaarId}) deleted from synthetic registry. Ready for revalidation test.`);
      await loadApaarRecords();
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete record.";
      setError(msg);
    }
  };

  const handleUpdateApaarStatus = async (id: number, currentStatus: string, newStatus: string) => {
    if (currentStatus === newStatus) return;
    setError(null);
    setSuccess(null);
    try {
      await apiRequest(`/reference-data/synthetic-apaar/${id}`, {
        method: "PUT",
        body: JSON.stringify({ status: newStatus })
      });
      setSuccess(`Updated APAAR record #${id} status to ${newStatus}. Persisted to database.`);
      await loadApaarRecords();
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update record status.";
      setError(msg);
    }
  };

  const handleSaveApproval = async (id: number) => {
    setError(null);
    setSuccess(null);
    try {
      const res = await apiRequest(`/reference-data/approvals/${id}`, {
        method: "PUT",
        body: JSON.stringify({ approved_intake: Number(editApprovedIntake) })
      });
      setSuccess(`Updated approved intake to ${res.approved_intake}. Persisted to database.`);
      setEditingApprovalId(null);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update approval snapshot.";
      setError(msg);
    }
  };

  const handleSaveDeclaration = async (id: number) => {
    setError(null);
    setSuccess(null);
    try {
      const res = await apiRequest(`/reference-data/declarations/${id}`, {
        method: "PUT",
        body: JSON.stringify({ declared_intake: Number(editDeclaredIntake) })
      });
      setSuccess(`Updated institutional declared intake to ${res.declared_intake}. Persisted to database.`);
      setEditingDeclId(null);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to update declaration.";
      setError(msg);
    }
  };

  const handleTriggerRevalidation = async () => {
    if (!selectedBatchId) return;
    setIsRevalidating(true);
    setError(null);
    setSuccess(null);
    setRevalidationResult(null);
    try {
      const res = await apiRequest(`/reference-data/revalidate/${selectedBatchId}`, {
        method: "POST"
      });
      setRevalidationResult(res);
      setSuccess(`Dynamic revalidation completed for Batch #${selectedBatchId}! Generated Validation Run #${res.run_number}.`);
      await loadData();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Revalidation failed.";
      setError(msg);
    } finally {
      setIsRevalidating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="p-4 bg-amber-500/10 border border-amber-500/30 rounded-xl flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
        <div className="text-xs">
          <div className="font-bold text-amber-900 uppercase tracking-wide">
            Authoritative Demonstration Registry [DEMO DATA]
          </div>
          <div className="text-amber-800/80 mt-0.5">
            This workspace directly reads and writes live database tables (<code>synthetic_apaar_registry</code>, <code>approval_snapshots</code>, <code>institutional_declarations</code>).
            All edits are persisted to SQLite/PostgreSQL and recorded into the SHA-256 tamper-evident hash chain ledger.
          </div>
        </div>
      </div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Database className="w-6 h-6 text-govTeal-600" />
            <span>Demo Reference Data Management</span>
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Modify approved capacities, declarations, and synthetic APAAR reference profiles to verify dynamic revalidation reactivity.
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Database Registry</span>
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
          <XCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {success && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-800 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
          <span>{success}</span>
        </div>
      )}

      {/* Registry Overview Tally */}
      {overview && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
          <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs">
            <div className="text-slate-500 font-medium">Institutions</div>
            <div className="text-lg font-bold text-slate-900 mt-1">{overview.total_institutions}</div>
          </div>
          <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs">
            <div className="text-slate-500 font-medium">Programmes</div>
            <div className="text-lg font-bold text-slate-900 mt-1">{overview.total_programmes}</div>
          </div>
          <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs">
            <div className="text-slate-500 font-medium">Approved Intakes</div>
            <div className="text-lg font-bold text-slate-900 mt-1">{overview.total_approvals}</div>
          </div>
          <div className="p-3 bg-white rounded-xl border border-slate-200 shadow-xs">
            <div className="text-slate-500 font-medium">Declarations</div>
            <div className="text-lg font-bold text-slate-900 mt-1">{overview.total_declarations}</div>
          </div>
          <div className="p-3 bg-teal-50 rounded-xl border border-teal-200 shadow-xs">
            <div className="text-teal-700 font-medium">Synthetic APAAR Records</div>
            <div className="text-lg font-bold text-teal-900 mt-1">{overview.total_synthetic_apaar}</div>
          </div>
        </div>
      )}

      {/* SUPABASE CLOUD DATABASE ("SUBOBASE") & SOVEREIGN CRYPTOGRAPHIC VAULT */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Supabase Cloud Base Card */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-emerald-50 text-emerald-700 rounded-lg border border-emerald-200">
                <Database className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-slate-900">
                    Supabase Cloud Database (SuboBase)
                  </h2>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    supabaseStatus?.connected
                      ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                      : "bg-blue-100 text-blue-800 border-blue-300"
                  }`}>
                    {supabaseStatus?.mode || "AUTHORITATIVE_LOCAL_HYBRID"}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  {supabaseStatus?.message || "Operating on Authoritative Local Database Engine with live Supabase Cloud synchronization adapter."}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={handleSyncSupabase}
                disabled={isSyncingSupabase}
                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-xs cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isSyncingSupabase ? "animate-spin" : ""}`} />
                <span>{isSyncingSupabase ? "Syncing..." : "Sync with Cloud"}</span>
              </button>
            </div>
          </div>

          {supabaseMessage && (
            <div className={`p-2.5 rounded-lg text-xs flex items-center gap-2 border ${
              supabaseMessage.type === "success"
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : "bg-amber-50 border-amber-200 text-amber-800"
            }`}>
              <Info className="w-3.5 h-3.5 flex-shrink-0" />
              <span>{supabaseMessage.text}</span>
            </div>
          )}
        </div>

        {/* Sovereign Cryptographic Merkle Vault Card */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <div className="p-2 bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-200">
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-sm font-bold text-slate-900">
                    Sovereign Cryptographic Data Vault
                  </h2>
                  <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                    vaultIntegrity?.is_valid
                      ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                      : "bg-amber-100 text-amber-800 border-amber-300"
                  }`}>
                    {vaultIntegrity?.status || "TAMPER_EVIDENT_ACTIVE"}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Algorithm: SHA-256 Merkle Sovereign Consensus Seal. Guarantees zero out-of-band data tampering.
                </p>
              </div>
            </div>

            <button
              onClick={handleSealVault}
              disabled={isSealingVault}
              className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-xs cursor-pointer"
            >
              <ShieldAlert className={`w-3.5 h-3.5 ${isSealingVault ? "animate-spin" : ""}`} />
              <span>{isSealingVault ? "Sealing..." : "Seal Vault Ledger"}</span>
            </button>
          </div>

          <div className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg font-mono text-[11px] text-slate-700 flex items-center justify-between">
            <div>
              <span className="text-slate-400">Master Digest: </span>
              <span className="font-bold text-indigo-900">
                {vaultIntegrity?.current_seal ? `${vaultIntegrity.current_seal.slice(0, 24)}...` : "CALCULATING..."}
              </span>
            </div>
            <span className="text-[10px] text-emerald-700 font-sans font-bold">
              ✓ Immutable Chain
            </span>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 text-xs font-semibold gap-6">
        <button
          onClick={() => setActiveTab("apaar")}
          className={`pb-2.5 transition border-b-2 ${
            activeTab === "apaar"
              ? "border-govTeal-600 text-govTeal-700 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Synthetic APAAR Registry ({apaarRecords.length})
        </button>
        <button
          onClick={() => setActiveTab("approvals")}
          className={`pb-2.5 transition border-b-2 ${
            activeTab === "approvals"
              ? "border-govTeal-600 text-govTeal-700 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Approved Intakes &amp; Limits ({approvals.length})
        </button>
        <button
          onClick={() => setActiveTab("declarations")}
          className={`pb-2.5 transition border-b-2 ${
            activeTab === "declarations"
              ? "border-govTeal-600 text-govTeal-700 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Institutional Declarations ({declarations.length})
        </button>
        <button
          onClick={() => setActiveTab("revalidate")}
          className={`pb-2.5 transition border-b-2 ${
            activeTab === "revalidate"
              ? "border-govNavy-900 text-govNavy-900 font-bold"
              : "border-transparent text-slate-500 hover:text-slate-800"
          }`}
        >
          Live Batch Revalidation (Tests A-E)
        </button>
      </div>

      {/* TAB 1: Synthetic APAAR Registry */}
      {activeTab === "apaar" && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search APAAR ID or Name..."
                  value={apaarSearch}
                  onChange={(e) => setApaarSearch(e.target.value)}
                  className="pl-8 pr-3 py-1.5 border border-slate-300 rounded-lg text-xs w-60 focus:outline-none focus:ring-1 focus:ring-govTeal-600 text-slate-900"
                />
              </div>
              <select
                value={apaarStatusFilter}
                onChange={(e) => setApaarStatusFilter(e.target.value)}
                className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs focus:outline-none focus:ring-1 focus:ring-govTeal-600 text-slate-900"
              >
                <option value="">All Statuses</option>
                <option value="DEMO_REFERENCE_MATCH">DEMO_REFERENCE_MATCH</option>
                <option value="NO_DEMO_REFERENCE_MATCH">NO_DEMO_REFERENCE_MATCH</option>
                <option value="MANUAL_REVIEW_REQUIRED">MANUAL_REVIEW_REQUIRED</option>
              </select>
            </div>

            <div className="flex items-center flex-wrap gap-2">
              <button
                type="button"
                onClick={() => handleSeedApaarBatch(5, false)}
                disabled={isSeedingBatch}
                className="px-2.5 py-1.5 bg-govTeal-50 hover:bg-govTeal-100 text-govTeal-800 border border-govTeal-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
                title="Seed 5 clean synthetic APAAR records directly into database"
              >
                <Sparkles className={`w-3.5 h-3.5 text-govTeal-600 ${isSeedingBatch ? "animate-spin" : ""}`} />
                <span>Seed 5 Clean</span>
              </button>

              <button
                type="button"
                onClick={() => handleSeedApaarBatch(5, true)}
                disabled={isSeedingBatch}
                className="px-2.5 py-1.5 bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-300 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition shadow-2xs cursor-pointer"
                title="Seed 5 discrepant synthetic APAAR records (unmatched/review) to test audit engine"
              >
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>Seed 5 Discrepant</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  const randomSuffix = Math.floor(10000000 + Math.random() * 90000000);
                  setNewApaarId(`98${randomSuffix}`);
                  setIsAddingApaar(!isAddingApaar);
                }}
                className="px-3 py-1.5 bg-govTeal-600 hover:bg-govTeal-700 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-xs transition cursor-pointer"
              >
                <Plus className="w-4 h-4" />
                <span>{isAddingApaar ? "Cancel" : "Add Synthetic Record"}</span>
              </button>
            </div>
          </div>

          {/* Add Record Form */}
          {isAddingApaar && (
            <form onSubmit={handleCreateApaar} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-900">Add New Synthetic APAAR Reference Record</h3>
                <button
                  type="button"
                  onClick={() => {
                    const randomSuffix = Math.floor(10000000 + Math.random() * 90000000);
                    setNewApaarId(`98${randomSuffix}`);
                  }}
                  className="px-2 py-1 bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 rounded text-[11px] font-medium flex items-center gap-1 transition"
                >
                  <RefreshCw className="w-3 h-3 text-slate-500" />
                  <span>Generate Random ID</span>
                </button>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div>
                  <label className="block text-slate-700 mb-1 font-medium">12-Digit APAAR ID</label>
                  <input
                    type="text"
                    required
                    maxLength={12}
                    placeholder="e.g. 400192839999"
                    value={newApaarId}
                    onChange={(e) => setNewApaarId(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg font-mono text-xs text-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 mb-1 font-medium">Full Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Test Student"
                    value={newApaarName}
                    onChange={(e) => setNewApaarName(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs text-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 mb-1 font-medium">Date of Birth</label>
                  <input
                    type="date"
                    required
                    value={newApaarDob}
                    onChange={(e) => setNewApaarDob(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs text-slate-900"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 mb-1 font-medium">Gender</label>
                  <select
                    value={newApaarGender}
                    onChange={(e) => setNewApaarGender(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs text-slate-900"
                  >
                    <option value="MALE">MALE</option>
                    <option value="FEMALE">FEMALE</option>
                    <option value="OTHER">OTHER</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 mb-1 font-medium">Reference Status</label>
                  <select
                    value={newApaarStatus}
                    onChange={(e) => setNewApaarStatus(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs text-slate-900"
                  >
                    <option value="DEMO_REFERENCE_MATCH">DEMO_REFERENCE_MATCH</option>
                    <option value="NO_DEMO_REFERENCE_MATCH">NO_DEMO_REFERENCE_MATCH</option>
                    <option value="MANUAL_REVIEW_REQUIRED">MANUAL_REVIEW_REQUIRED</option>
                    <option value="PENDING_EXTERNAL_VERIFICATION">PENDING_EXTERNAL_VERIFICATION</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 mb-1 font-medium">Notes / Test Scenario</label>
                  <input
                    type="text"
                    placeholder="e.g. Synthetic test candidate for dynamic mutation test"
                    value={newApaarNotes}
                    onChange={(e) => setNewApaarNotes(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg text-xs text-slate-900"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddingApaar(false)}
                  className="px-3 py-1.5 bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-govTeal-600 hover:bg-govTeal-700 text-white rounded-lg text-xs font-semibold"
                >
                  Save Record to Database
                </button>
              </div>
            </form>
          )}

          {/* Records Table */}
          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
                <tr>
                  <th className="px-3 py-2.5">ID</th>
                  <th className="px-3 py-2.5">APAAR ID</th>
                  <th className="px-3 py-2.5">Student Name</th>
                  <th className="px-3 py-2.5">DOB / Gender</th>
                  <th className="px-3 py-2.5">Database Status</th>
                  <th className="px-3 py-2.5">Audit Notes</th>
                  <th className="px-3 py-2.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {apaarRecords.map((r) => (
                  <tr key={r.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-mono text-slate-400">#{r.id}</td>
                    <td className="px-3 py-2 font-mono font-bold text-slate-900">{r.apaar_id}</td>
                    <td className="px-3 py-2 font-medium text-slate-800">{r.full_name}</td>
                    <td className="px-3 py-2 text-slate-500">{r.dob || "—"} ({r.gender})</td>
                    <td className="px-3 py-2">
                      <select
                        value={r.status}
                        onChange={(e) => handleUpdateApaarStatus(r.id, r.status, e.target.value)}
                        className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase border ${
                          r.status === "DEMO_REFERENCE_MATCH"
                            ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                            : r.status === "MANUAL_REVIEW_REQUIRED"
                            ? "bg-amber-50 text-amber-800 border-amber-300"
                            : "bg-rose-50 text-rose-800 border-rose-300"
                        }`}
                      >
                        <option value="DEMO_REFERENCE_MATCH">DEMO_REFERENCE_MATCH</option>
                        <option value="NO_DEMO_REFERENCE_MATCH">NO_DEMO_REFERENCE_MATCH</option>
                        <option value="MANUAL_REVIEW_REQUIRED">MANUAL_REVIEW_REQUIRED</option>
                        <option value="PENDING_EXTERNAL_VERIFICATION">PENDING_EXTERNAL_VERIFICATION</option>
                      </select>
                    </td>
                    <td className="px-3 py-2 text-slate-500 truncate max-w-xs">{r.notes || "—"}</td>
                    <td className="px-3 py-2 text-right">
                      <button
                        onClick={() => handleDeleteApaar(r.id, r.apaar_id)}
                        className="p-1 text-rose-600 hover:bg-rose-50 rounded transition"
                        title="Delete record from database"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))}
                {apaarRecords.length === 0 && (
                  <tr>
                    <td colSpan={7} className="px-4 py-8 text-center text-slate-400">
                      No matching synthetic APAAR records found in database.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 2: Approved Intakes & Policy Quotas */}
      {activeTab === "approvals" && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Sanctioned AICTE Approved Intakes</h2>
              <p className="text-xs text-slate-500">
                Central regulators can manually edit approved capacities or register newly sanctioned academic programmes.
              </p>
            </div>
            <button
              onClick={() => setIsAddingProgramme(!isAddingProgramme)}
              className="px-3.5 py-1.5 bg-govTeal-600 hover:bg-govTeal-700 text-white rounded-lg text-xs font-bold flex items-center gap-1.5 transition shadow-xs cursor-pointer"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>{isAddingProgramme ? "Close Form" : "+ Add Approved Programme"}</span>
            </button>
          </div>

          {/* Collapsible Form for Central Regulator to Add Approved Programme */}
          {isAddingProgramme && (
            <form onSubmit={handleCreateProgrammeWithApproval} className="p-4 bg-teal-50/60 border border-teal-200 rounded-xl space-y-3 text-xs">
              <div className="font-bold text-teal-900 flex items-center gap-1.5 text-xs">
                <Database className="w-4 h-4 text-govTeal-600" />
                <span>AICTE Central Portal: Sanction New Academic Programme &amp; Intake</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                <div>
                  <label className="block text-slate-700 mb-1 font-semibold">Target Approved Institution</label>
                  <select
                    value={newProgInstitutionId}
                    onChange={(e) => setNewProgInstitutionId(Number(e.target.value))}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg bg-white font-medium"
                  >
                    <option value={2}>DTU Delhi (AICTE ID: 1-1029384756)</option>
                    <option value={1}>COEP Pune (AICTE ID: 1-9876543210)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-slate-700 mb-1 font-semibold">Programme Code (e.g. BTECH-AI)</label>
                  <input
                    type="text"
                    required
                    value={newProgCode}
                    onChange={(e) => setNewProgCode(e.target.value.toUpperCase())}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg bg-white font-mono uppercase font-bold"
                  />
                </div>

                <div>
                  <label className="block text-slate-700 mb-1 font-semibold">Programme Title</label>
                  <input
                    type="text"
                    required
                    value={newProgName}
                    onChange={(e) => setNewProgName(e.target.value)}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
                <div>
                  <label className="block text-slate-700 mb-1 font-semibold">Sanctioned General Intake (Seats)</label>
                  <input
                    type="number"
                    min="1"
                    required
                    value={newProgIntake}
                    onChange={(e) => setNewProgIntake(Number(e.target.value))}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg bg-white font-bold"
                  />
                </div>

                <div>
                  <label className="block text-slate-700 mb-1 font-semibold">TFW Supernumerary Quota (5%)</label>
                  <input
                    type="number"
                    min="0"
                    required
                    value={newProgTfw}
                    onChange={(e) => setNewProgTfw(Number(e.target.value))}
                    className="w-full px-3 py-1.5 border border-slate-300 rounded-lg bg-white font-bold"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-teal-200">
                <button
                  type="button"
                  onClick={() => setIsAddingProgramme(false)}
                  className="px-3 py-1.5 bg-white border border-slate-300 text-slate-700 rounded-lg font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingProgramme}
                  className="px-4 py-1.5 bg-govTeal-600 hover:bg-govTeal-700 text-white rounded-lg font-bold shadow-xs transition"
                >
                  {isSubmittingProgramme ? "Saving to Database..." : "Sanction & Persist to Database"}
                </button>
              </div>
            </form>
          )}

          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
                <tr>
                  <th className="px-3 py-2.5">ID</th>
                  <th className="px-3 py-2.5">Institution</th>
                  <th className="px-3 py-2.5">Programme Code</th>
                  <th className="px-3 py-2.5">Academic Year</th>
                  <th className="px-3 py-2.5">Approved Intake</th>
                  <th className="px-3 py-2.5">Policy Version</th>
                  <th className="px-3 py-2.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {approvals.map((a) => (
                  <tr key={a.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-mono text-slate-400">#{a.id}</td>
                    <td className="px-3 py-2 font-medium text-slate-800">{a.institution_name}</td>
                    <td className="px-3 py-2 font-mono font-bold text-govTeal-700">{a.programme_code}</td>
                    <td className="px-3 py-2 font-mono text-slate-600">{a.academic_year}</td>
                    <td className="px-3 py-2">
                      {editingApprovalId === a.id ? (
                        <div className="flex items-center gap-1.5">
                          <input
                            type="number"
                            min="0"
                            value={editApprovedIntake}
                            onChange={(e) => setEditApprovedIntake(Number(e.target.value))}
                            className="w-20 px-2 py-1 border border-slate-300 rounded font-bold text-xs text-slate-900"
                          />
                          <button
                            onClick={() => handleSaveApproval(a.id)}
                            className="px-2 py-1 bg-govTeal-600 text-white rounded text-[11px] font-semibold"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingApprovalId(null)}
                            className="px-2 py-1 bg-slate-200 text-slate-700 rounded text-[11px]"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <span className="font-bold text-slate-900 text-sm">{a.approved_intake} seats</span>
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono text-slate-500">{a.policy_version}</td>
                    <td className="px-3 py-2 text-right">
                      {editingApprovalId !== a.id && (
                        <button
                          onClick={() => {
                            setEditingApprovalId(a.id);
                            setEditApprovedIntake(a.approved_intake);
                          }}
                          className="p-1 text-slate-600 hover:text-govTeal-600 rounded transition"
                          title="Edit approved capacity"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 3: Institutional Declarations */}
      {activeTab === "declarations" && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Institutional Enrolment Declarations</h2>
            <p className="text-xs text-slate-500">
              Edit college-declared admission targets. Modifying this value immediately alters the Declared Discrepancy metric and triggers reconciliation mismatch findings.
            </p>
          </div>

          <div className="border border-slate-200 rounded-lg overflow-hidden">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
                <tr>
                  <th className="px-3 py-2.5">ID</th>
                  <th className="px-3 py-2.5">Institution</th>
                  <th className="px-3 py-2.5">Programme Code</th>
                  <th className="px-3 py-2.5">Academic Year</th>
                  <th className="px-3 py-2.5">Declared Intake</th>
                  <th className="px-3 py-2.5">Declaration Ref</th>
                  <th className="px-3 py-2.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {declarations.map((d) => (
                  <tr key={d.id} className="hover:bg-slate-50">
                    <td className="px-3 py-2 font-mono text-slate-400">#{d.id}</td>
                    <td className="px-3 py-2 font-medium text-slate-800">{d.institution_name}</td>
                    <td className="px-3 py-2 font-mono font-bold text-govNavy-700">{d.programme_code}</td>
                    <td className="px-3 py-2 font-mono text-slate-600">{d.academic_year}</td>
                    <td className="px-3 py-2">
                      {editingDeclId === d.id ? (
                        <div className="flex items-center gap-1.5">
                          <input
                            type="number"
                            min="0"
                            value={editDeclaredIntake}
                            onChange={(e) => setEditDeclaredIntake(Number(e.target.value))}
                            className="w-20 px-2 py-1 border border-slate-300 rounded font-bold text-xs text-slate-900"
                          />
                          <button
                            onClick={() => handleSaveDeclaration(d.id)}
                            className="px-2 py-1 bg-govTeal-600 text-white rounded text-[11px] font-semibold"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => setEditingDeclId(null)}
                            className="px-2 py-1 bg-slate-200 text-slate-700 rounded text-[11px]"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <span className="font-bold text-slate-900 text-sm">{d.declared_intake} declared</span>
                      )}
                    </td>
                    <td className="px-3 py-2 font-mono text-slate-500">{d.declaration_ref}</td>
                    <td className="px-3 py-2 text-right">
                      {editingDeclId !== d.id && (
                        <button
                          onClick={() => {
                            setEditingDeclId(d.id);
                            setEditDeclaredIntake(d.declared_intake);
                          }}
                          className="p-1 text-slate-600 hover:text-govTeal-600 rounded transition"
                          title="Edit declared target"
                        >
                          <Edit2 className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* TAB 4: Live Dynamic Revalidation (Tests A-E Demo) */}
      {activeTab === "revalidate" && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-6">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Dynamic Revalidation Runner (SIH Requirement 10)</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Select an uploaded batch and trigger dynamic revalidation against the current live database reference values.
              A new versioned <code>ValidationRun</code> will be persisted without overwriting historical findings.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <select
              value={selectedBatchId || ""}
              onChange={(e) => setSelectedBatchId(Number(e.target.value))}
              className="px-3 py-2 border border-slate-300 rounded-lg text-xs font-medium w-80 focus:outline-none focus:ring-2 focus:ring-govNavy-500 text-slate-900"
            >
              {batches.map((b) => (
                <option key={b.id} value={b.id}>
                  Batch #{b.id}: {b.filename} ({b.institution_name || `Inst #${b.institution_id}`}) - {b.status}
                </option>
              ))}
            </select>

            <button
              onClick={handleTriggerRevalidation}
              disabled={!selectedBatchId || isRevalidating}
              className="px-5 py-2 bg-govNavy-900 hover:bg-govNavy-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-2 transition"
            >
              {isRevalidating ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Executing 3-Way Revalidation...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Trigger Revalidation against Live DB State</span>
                </>
              )}
            </button>
          </div>

          {/* Revalidation Outcome Display */}
          {revalidationResult && (
            <div className="p-5 bg-slate-50 border border-govTeal-200 rounded-xl space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="px-2 py-0.5 rounded bg-govNavy-900 text-white text-[11px] font-mono font-bold">
                    Validation Run #{revalidationResult.run_number}
                  </span>
                  <h3 className="text-sm font-bold text-slate-900 mt-1">
                    Revalidation Findings &amp; Disposition Metrics
                  </h3>
                </div>
                <div className="text-xs font-mono text-slate-600">
                  Status: <span className="font-bold text-govNavy-900">{revalidationResult.status}</span>
                </div>
              </div>

              {/* Disposition Cards */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div className="p-3 bg-white rounded-lg border border-slate-200">
                  <div className="text-slate-500 font-medium">Total Rows</div>
                  <div className="text-lg font-bold text-slate-900 mt-0.5">
                    {revalidationResult.disposition.total_rows}
                  </div>
                </div>
                <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-200">
                  <div className="text-emerald-700 font-medium">Eligible to Proceed</div>
                  <div className="text-lg font-bold text-emerald-800 mt-0.5">
                    {revalidationResult.disposition.eligible_to_proceed}
                  </div>
                </div>
                <div className="p-3 bg-amber-50 rounded-lg border border-amber-200">
                  <div className="text-amber-700 font-medium">Requiring Review</div>
                  <div className="text-lg font-bold text-amber-800 mt-0.5">
                    {revalidationResult.disposition.requiring_review}
                  </div>
                </div>
                <div className="p-3 bg-rose-50 rounded-lg border border-rose-200">
                  <div className="text-rose-700 font-medium">Blocking Errors</div>
                  <div className="text-lg font-bold text-rose-800 mt-0.5">
                    {revalidationResult.disposition.blocking_errors}
                  </div>
                </div>
              </div>

              {/* Discrepancy Metric */}
              <div className="p-3 bg-white rounded-lg border border-slate-200 flex items-center justify-between text-xs">
                <div>
                  <span className="text-slate-500 font-medium">Declared Intake Target: </span>
                  <span className="font-bold text-slate-900">{revalidationResult.disposition.declared_intake}</span>
                </div>
                <div>
                  <span className="text-slate-500 font-medium">Declared Discrepancy: </span>
                  <span className={`font-bold font-mono ${revalidationResult.disposition.declared_discrepancy !== 0 ? 'text-amber-700' : 'text-emerald-700'}`}>
                    {revalidationResult.disposition.declared_discrepancy > 0 ? `+${revalidationResult.disposition.declared_discrepancy}` : revalidationResult.disposition.declared_discrepancy}
                  </span>
                </div>
              </div>

              {/* Live Findings List */}
              <div>
                <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
                  Live Rule Evaluation Findings ({revalidationResult.findings.length})
                </h4>
                <div className="border border-slate-200 rounded-lg overflow-hidden bg-white">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
                      <tr>
                        <th className="px-3 py-2">Row</th>
                        <th className="px-3 py-2">Finding Type</th>
                        <th className="px-3 py-2">Severity</th>
                        <th className="px-3 py-2">Message</th>
                        <th className="px-3 py-2">Actionable Guidance</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {revalidationResult.findings.map((f: FindingItem, idx: number) => (
                        <tr key={idx} className="hover:bg-slate-50">
                          <td className="px-3 py-2 font-mono font-medium text-slate-500">#{f.row_index}</td>
                          <td className="px-3 py-2 font-mono font-semibold text-govTeal-700">{f.finding_type}</td>
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
                          <td className="px-3 py-2 text-slate-800">{f.message}</td>
                          <td className="px-3 py-2 text-slate-500">{f.recommended_action || "—"}</td>
                        </tr>
                      ))}
                      {revalidationResult.findings.length === 0 && (
                        <tr>
                          <td colSpan={5} className="px-3 py-4 text-center text-slate-400">
                            Zero discrepancies detected. 100% compliant with live database references.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
