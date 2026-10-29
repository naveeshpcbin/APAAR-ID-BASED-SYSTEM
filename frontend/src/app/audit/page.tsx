"use client";

import React, { useState, useEffect } from "react";
import {
  History,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Search,
  Lock,
  ArrowRight,
  Filter,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function AuditPage() {
  const { user } = useAuth();
  const [events, setEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [isVerifying, setIsVerifying] = useState(false);
  const [chainResult, setChainResult] = useState<any | null>(null);

  const loadEvents = async () => {
    try {
      setLoading(true);
      const res = await apiRequest("/audit?limit=100");
      setEvents(res);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadEvents();
  }, [user]);

  const handleVerifyChain = async () => {
    setIsVerifying(true);
    try {
      const res = await apiRequest("/audit/verify-chain", { method: "POST" });
      setChainResult(res);
    } catch (err: any) {
      setChainResult({
        is_valid: false,
        message: err.message,
      });
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Tamper-Evident Hash Chain Audit Ledger
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Sequential cryptographic linking (SHA-256) of every regulatory action, admission commit, conflict adjudication, and receipt issuance.
          </p>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={isVerifying}
          className="px-4 py-2 bg-govNavy-900 hover:bg-govNavy-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-2 transition"
        >
          {isVerifying ? (
            <>
              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              <span>Verifying Cryptographic Chain...</span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-4 h-4 text-govTeal-400" />
              <span>Verify Hash Chain Integrity</span>
            </>
          )}
        </button>
      </div>

      {/* Verification Result Banner */}
      {chainResult && (
        <div
          className={`p-4 rounded-xl border text-xs flex items-start gap-3 ${
            chainResult.is_valid
              ? "bg-emerald-50 border-emerald-200 text-emerald-900"
              : "bg-rose-50 border-rose-200 text-rose-900"
          }`}
        >
          {chainResult.is_valid ? (
            <CheckCircle2 className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
          ) : (
            <XCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
          )}
          <div className="space-y-1">
            <div className="font-bold text-sm">
              {chainResult.is_valid
                ? "Cryptographic Hash Chain Verified (100% Unbroken Integrity)"
                : "Ledger Tampering Detected!"}
            </div>
            <div className="text-xs text-slate-600">{chainResult.message}</div>
            {chainResult.head_hash && (
              <div className="font-mono text-[11px] text-slate-500 truncate pt-1">
                Head Hash: {chainResult.head_hash}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Audit Events Table */}
      <div className="bg-white p-4 sm:p-6 rounded-xl border border-slate-200/90 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
          <h2 className="text-sm font-bold text-slate-900">Tamper-Evident Event Ledger</h2>
          <span className="text-xs text-slate-400 font-mono">
            {events.length} sequential cryptographically-linked entries
          </span>
        </div>

        <div className="border border-slate-200 rounded-lg overflow-x-auto">
          <table className="w-full min-w-[780px] text-xs text-left">
            <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
              <tr>
                <th className="px-3 py-2.5">Seq #</th>
                <th className="px-3 py-2.5">Action</th>
                <th className="px-3 py-2.5">Entity</th>
                <th className="px-3 py-2.5">Actor</th>
                <th className="px-3 py-2.5">Previous SHA-256 Hash</th>
                <th className="px-3 py-2.5">Current SHA-256 Hash</th>
                <th className="px-3 py-2.5">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
              {events.map((e) => (
                <tr key={e.id} className="hover:bg-slate-50">
                  <td className="px-3 py-2.5 font-bold text-slate-900 font-sans">
                    #{e.sequence_no}
                  </td>
                  <td className="px-3 py-2.5 font-sans font-semibold text-govTeal-700">
                    {e.action}
                  </td>
                  <td className="px-3 py-2.5 font-sans text-slate-700">
                    {e.entity_type} ({e.entity_id})
                  </td>
                  <td className="px-3 py-2.5 font-sans text-slate-600">
                    {e.actor_email} <span className="text-slate-400">({e.actor_role})</span>
                  </td>
                  <td className="px-3 py-2.5 text-slate-400 truncate max-w-[120px]" title={e.previous_hash}>
                    {e.previous_hash.slice(0, 16)}...
                  </td>
                  <td className="px-3 py-2.5 text-govTeal-800 font-bold truncate max-w-[120px]" title={e.current_hash}>
                    {e.current_hash.slice(0, 16)}...
                  </td>
                  <td className="px-3 py-2.5 text-slate-500 font-sans">
                    {new Date(e.created_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
              {events.length === 0 && !loading && (
                <tr>
                  <td colSpan={7} className="px-3 py-6 text-center text-slate-400 font-sans">
                    Audit ledger is at genesis state.
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
