"use client";

import React from "react";
import { User, LogOut, Shield, ChevronDown, CheckCircle2 } from "lucide-react";
import { useAuth, DEMO_CREDENTIALS } from "@/lib/auth-context";

export function TopBar() {
  const { user, logout, switchDemoUser } = useAuth();

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
      </div>

      {/* Right: Demo Persona Switcher & User Profile */}
      <div className="flex items-center gap-3">
        {/* Quick Role Switcher for SIH Evaluators */}
        <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 p-1 rounded-lg text-xs">
          <span className="text-[11px] font-semibold text-slate-500 px-1.5">
            Role Switcher:
          </span>
          <button
            onClick={() => switchDemoUser("admin")}
            className={`px-2 py-1 rounded text-xs font-medium transition ${
              user?.role === "AICTE_ADMIN"
                ? "bg-govNavy-900 text-white shadow-xs"
                : "text-slate-600 hover:bg-slate-200/60"
            }`}
          >
            AICTE Central
          </button>
          <button
            onClick={() => switchDemoUser("dtu")}
            className={`px-2 py-1 rounded text-xs font-medium transition ${
              user?.email === DEMO_CREDENTIALS.dtu.email
                ? "bg-govNavy-900 text-white shadow-xs"
                : "text-slate-600 hover:bg-slate-200/60"
            }`}
          >
            DTU Delhi
          </button>
          <button
            onClick={() => switchDemoUser("coep")}
            className={`px-2 py-1 rounded text-xs font-medium transition ${
              user?.email === DEMO_CREDENTIALS.coep.email
                ? "bg-govNavy-900 text-white shadow-xs"
                : "text-slate-600 hover:bg-slate-200/60"
            }`}
          >
            COEP Pune
          </button>
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
            onClick={logout}
            title="Sign out"
            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
