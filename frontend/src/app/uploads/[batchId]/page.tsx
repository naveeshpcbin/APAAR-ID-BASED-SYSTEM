"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, CheckCircle2, AlertTriangle, XCircle, FileSpreadsheet } from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function BatchDetailPage() {
  const params = useParams();
  const router = useRouter();
  const batchId = params?.batchId;
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
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
    }
    load();
  }, [batchId]);

  if (loading) {
    return <div className="p-8 text-center text-xs text-slate-500">Loading batch details...</div>;
  }

  if (!data) {
    return <div className="p-8 text-center text-xs text-red-500">Batch not found.</div>;
  }

  const { batch, findings } = data;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3 pb-2 border-b border-slate-200">
        <Link
          href="/uploads"
          className="p-1.5 rounded-lg border border-slate-300 hover:bg-slate-100 text-slate-700"
        >
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Batch #{batch.id}: {batch.filename}
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Academic Session: {batch.academic_year} | Status:{" "}
            <span className="font-semibold text-govTeal-700">{batch.status}</span>
          </p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-xl border border-slate-200">
          <div className="text-xs text-slate-500">Total Rows</div>
          <div className="text-xl font-bold text-slate-900 mt-1">{batch.total_rows}</div>
        </div>
        <div className="p-4 bg-emerald-50 rounded-xl border border-emerald-200">
          <div className="text-xs text-emerald-700">Valid Records</div>
          <div className="text-xl font-bold text-emerald-800 mt-1">{batch.valid_rows}</div>
        </div>
        <div className="p-4 bg-amber-50 rounded-xl border border-amber-200">
          <div className="text-xs text-amber-700">Warnings / Collisions</div>
          <div className="text-xl font-bold text-amber-800 mt-1">{batch.warning_rows}</div>
        </div>
        <div className="p-4 bg-rose-50 rounded-xl border border-rose-200">
          <div className="text-xs text-rose-700">Errors</div>
          <div className="text-xl font-bold text-rose-800 mt-1">{batch.error_rows}</div>
        </div>
      </div>

      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-xs space-y-4">
        <h2 className="text-sm font-bold text-slate-900">Row Findings & Reconciliation Ledger</h2>

        <div className="border border-slate-200 rounded-lg overflow-hidden">
          <table className="w-full text-xs text-left">
            <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
              <tr>
                <th className="px-3 py-2.5">Row</th>
                <th className="px-3 py-2.5">Severity</th>
                <th className="px-3 py-2.5">Rule ID</th>
                <th className="px-3 py-2.5">Message</th>
                <th className="px-3 py-2.5">Recommended Action</th>
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
                  <td className="px-3 py-2 font-mono text-slate-700">{f.rule_id}</td>
                  <td className="px-3 py-2 text-slate-900">{f.message}</td>
                  <td className="px-3 py-2 text-slate-500">{f.recommended_action || "—"}</td>
                </tr>
              ))}
              {findings.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
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
