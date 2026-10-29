"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ShieldCheck,
  Building2,
  ArrowRight,
  ShieldAlert,
  GraduationCap,
  Scale,
  CheckCircle2,
  Lock,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function PortalDirectoryPage() {
  const router = useRouter();
  const { user, logout, isLoading } = useAuth();

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-8 sm:py-12 px-4 sm:px-6 lg:px-8 relative overflow-hidden select-none">
      {/* Background Decorative Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-40 pointer-events-none" />

      {/* Header / Brand Title */}
      <div className="sm:mx-auto sm:w-full sm:max-w-2xl text-center relative z-10">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-teal-500 via-teal-600 to-slate-900 text-white flex items-center justify-center mx-auto mb-4 shadow-xl shadow-teal-950/60 border border-teal-500/30">
          <ShieldCheck className="w-9 h-9" />
        </div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white sm:text-4xl">
          PRAMAAN-AICTE
        </h1>
        <p className="mt-2 text-sm text-slate-300 max-w-xl mx-auto">
          Platform for Real-time APAAR-linked Monitoring, Auditing, and Academic Network
        </p>
        <div className="mt-3 inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-semibold bg-slate-900 text-teal-400 border border-slate-800 shadow-inner">
          <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse" />
          <span>SIH Problem Statement SIH26263 | Dual Portal System</span>
        </div>

        {/* Active Session Indicator (if already signed in) */}
        {!isLoading && user && (
          <div className="mt-6 mx-auto max-w-md p-3.5 rounded-xl bg-slate-900/95 border border-teal-500/40 shadow-lg text-left flex items-center justify-between gap-3">
            <div className="min-w-0">
              <div className="text-[10px] font-mono uppercase tracking-wider text-teal-400 font-bold">
                Active Session Detected
              </div>
              <div className="text-xs font-semibold text-white truncate">
                {user.fullName || user.email}
              </div>
              <div className="text-[10px] text-slate-400 truncate">
                {user.email} &bull; <span className="font-mono text-slate-300">{user.role}</span>
              </div>
            </div>
            <div className="flex items-center gap-2 shrink-0">
              <button
                onClick={() =>
                  router.push(
                    user.role === "AICTE_ADMIN" || user.role === "REGIONAL_OFFICER"
                      ? "/dashboard"
                      : "/uploads"
                  )
                }
                className="px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-teal-600 hover:bg-teal-500 text-white transition shadow-xs"
              >
                Continue &rarr;
              </button>
              <button
                onClick={() => logout()}
                className="px-2.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-rose-400 bg-slate-800 hover:bg-slate-800/80 transition"
              >
                Sign Out
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Two Separate Portal Entry Choices */}
      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-3xl relative z-10">
        <div className="text-center mb-6">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400">
            Select Your Authorized Portal Access
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Dedicated portals with distinct workflows, tenant permissions, and regulatory scopes
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Choice A: College & Institution Portal */}
          <Link
            id="college-portal-entry-btn"
            href="/login/college"
            className="group relative p-5 sm:p-8 bg-slate-900/90 hover:bg-slate-900 border-2 border-slate-800 hover:border-emerald-500/80 rounded-2xl transition-all duration-200 flex flex-col justify-between shadow-xl hover:shadow-2xl hover:shadow-emerald-950/40 text-left focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <div>
              <div className="flex items-center justify-between mb-5">
                <div className="w-12 h-12 rounded-xl bg-emerald-950/90 text-emerald-400 border border-emerald-700/50 flex items-center justify-center group-hover:scale-105 transition">
                  <Building2 className="w-6 h-6" />
                </div>
                <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                  INSTITUTION SCOPE
                </span>
              </div>

              <h3 className="text-xl font-bold text-white group-hover:text-emerald-300 transition flex items-center gap-2">
                <span>College Portal</span>
                <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition" />
              </h3>

              <p className="text-xs text-slate-400 mt-2.5 leading-relaxed">
                Dedicated workspace for AICTE-approved college nodal officers, university registrars, and admission deans.
              </p>

              <div className="mt-5 space-y-2 text-[11px] text-slate-400 border-t border-slate-800/80 pt-4">
                <div className="flex items-center gap-2 text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Upload CSV and Excel student batches</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Schema alias mapping & row preflight validation</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Explicit &ldquo;Commit & Submit to AICTE&rdquo; workflow</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span>Track review status, returned findings & corrections</span>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-slate-800 flex items-center justify-between">
              <span className="text-xs font-semibold text-emerald-400 group-hover:text-emerald-300 transition">
                Enter College Portal Sign In &rarr;
              </span>
              <span className="text-[10px] text-slate-500 font-mono">DTU, COEP, etc.</span>
            </div>
          </Link>

          {/* Choice B: AICTE Central Regulator Portal */}
          <Link
            id="central-portal-entry-btn"
            href="/login/central"
            className="group relative p-5 sm:p-8 bg-slate-900/90 hover:bg-slate-900 border-2 border-slate-800 hover:border-blue-500/80 rounded-2xl transition-all duration-200 flex flex-col justify-between shadow-xl hover:shadow-2xl hover:shadow-blue-950/40 text-left focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <div>
              <div className="flex items-center justify-between mb-5">
                <div className="w-12 h-12 rounded-xl bg-blue-950/90 text-blue-400 border border-blue-700/50 flex items-center justify-center group-hover:scale-105 transition">
                  <Scale className="w-6 h-6" />
                </div>
                <span className="text-[10px] font-mono font-bold uppercase px-2 py-0.5 rounded bg-blue-950 text-blue-400 border border-blue-800">
                  CENTRAL REGULATOR
                </span>
              </div>

              <h3 className="text-xl font-bold text-white group-hover:text-blue-300 transition flex items-center gap-2">
                <span>AICTE Central Portal</span>
                <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 group-hover:translate-x-1 transition" />
              </h3>

              <p className="text-xs text-slate-400 mt-2.5 leading-relaxed">
                Bureau of Approval and Regional Directorate workspace for adjudicating submissions and policy enforcement.
              </p>

              <div className="mt-5 space-y-2 text-[11px] text-slate-400 border-t border-slate-800/80 pt-4">
                <div className="flex items-center gap-2 text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>3-Way reconciliation analysis & intake verification</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>Adjudication: Approve, Return for Correction, Reject</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>Cross-institution conflict & anomaly investigation</span>
                </div>
                <div className="flex items-center gap-2 text-slate-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-blue-400 shrink-0" />
                  <span>Live editable synthetic reference data registry</span>
                </div>
              </div>
            </div>

            <div className="mt-8 pt-4 border-t border-slate-800 flex items-center justify-between">
              <span className="text-xs font-semibold text-blue-400 group-hover:text-blue-300 transition">
                Enter Central Reviewer Sign In &rarr;
              </span>
              <span className="text-[10px] text-slate-500 font-mono">HQ, WRO, SRO</span>
            </div>
          </Link>
        </div>

        {/* New College Registration Banner */}
        <div className="mt-8 p-4 rounded-2xl bg-slate-900/90 border border-emerald-500/30 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center justify-center shrink-0">
              <Building2 className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-bold text-white flex items-center gap-1.5">
                <span>New AICTE-Approved College?</span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 bg-emerald-950 text-emerald-400 rounded border border-emerald-800">
                  ANY COLLEGE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Register any recognized institution using your AICTE Permanent ID to generate or upload APAAR admission datasets.
              </p>
            </div>
          </div>
          <Link
            id="register-new-college-btn"
            href="/register"
            className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition flex items-center gap-1.5 shrink-0 shadow-md"
          >
            <span>Register New College &rarr;</span>
          </Link>
        </div>

        {/* Security & Access Notice */}
        <div className="mt-6 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
          <Lock className="w-3.5 h-3.5 text-slate-600" />
          <span>Role-based authorization is enforced by the authoritative backend API. Central privileges cannot be self-assigned.</span>
        </div>
      </div>
    </div>
  );
}
