"use client";

import React, { useState, useEffect } from "react";
import { Building2, Search, MapPin, Mail, CheckCircle2 } from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function InstitutionsPage() {
  const { user } = useAuth();
  const [institutions, setInstitutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    async function loadInstitutions() {
      try {
        setLoading(true);
        const res = await apiRequest(`/institutions?search=${encodeURIComponent(searchTerm)}`);
        setInstitutions(res);
      } catch (err: any) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadInstitutions();
  }, [user, searchTerm]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            AICTE Approved Technical Institutions Directory
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Nationwide institutional records, AICTE approval IDs, state jurisdictions, and active programmes.
          </p>
        </div>
        <div className="relative w-72">
          <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
          <input
            type="text"
            placeholder="Search institution name or AICTE ID..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {institutions.map((inst) => (
          <div
            key={inst.id}
            className="bg-white p-5 rounded-xl border border-slate-200/90 shadow-xs space-y-3"
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700">
                  AICTE ID: {inst.aicte_id}
                </span>
                <h2 className="text-sm font-bold text-slate-900 mt-1">{inst.name}</h2>
              </div>
              <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                {inst.status}
              </span>
            </div>

            <div className="space-y-1.5 text-xs text-slate-600">
              <div className="flex items-center gap-1.5">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                <span>
                  {inst.district}, {inst.state}
                </span>
              </div>
              <div className="flex items-center gap-1.5">
                <Building2 className="w-3.5 h-3.5 text-slate-400" />
                <span>Type: {inst.institution_type}</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-slate-400" />
                <span className="font-mono text-[11px]">{inst.contact_email || "N/A"}</span>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500 font-medium">Offered Programmes:</span>
              <span className="font-semibold text-govTeal-700 font-mono">
                {inst.programmes?.length || 0} Registered
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
