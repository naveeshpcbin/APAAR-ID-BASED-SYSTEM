"use client";

import React from "react";
import { User, LogOut, CheckCircle2 } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export function TopBar() {
  const { user, logout } = useAuth();

  return (
    <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between select-none">
      {/* Left: Academic Year Context & Breadcrumb */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Academic Session:</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-300">
            2026-27 (Active Intake)
          </span>
        </div>

        <div className="hidden md:flex items-center gap-2 text-xs border-l border-slate-200 pl-4">
          <span className="flex items-center gap-1.5 text-slate-600">
            <CheckCircle2 className="w-3.5 h-3.5 text-govTeal-600" />
            <span className="font-medium">Rule Engine:</span>
            <span className="font-mono text-slate-800">AICTE-APH-2026-V1</span>
          </span>
        </div>

        <div className="hidden lg:flex items-center border-l border-slate-200 pl-4">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-900 border border-amber-300 shadow-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
            SIMULATION MODE (Synthetic APAAR Gateway)
          </span>
        </div>
      </div>

      {/* Right: Authoritative Scope & User Profile */}
      <div className="flex items-center gap-3">
        {/* Authoritative Scope Indicator (No mock role switching) */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
            Active Scope:
          </span>
          {user?.role === "AICTE_ADMIN" || user?.role === "REGIONAL_OFFICER" ? (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-900 border border-blue-300">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse" />
              Central Government Regulator (AICTE HQ)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-900 border border-emerald-300">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />
              {user?.institutionName || "College Portal Nodal"}
            </span>
          )}
        </div>

        {/* User Card */}
        <div className="flex items-center gap-2.5 pl-2 border-l border-slate-200">
          <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700">
            <User className="w-4 h-4" />
          </div>
          <div className="hidden sm:block text-left">
            <div className="text-xs font-semibold text-slate-900 leading-tight">
              {user?.fullName || "Evaluating Officer"}
            </div>
            <div className="text-[11px] text-slate-500 leading-tight">
              {user?.email || "officer@pramaan.gov.in"}
            </div>
          </div>
          <button
            id="topbar-logout-btn"
            onClick={() => logout()}
            title="Sign out"
            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
