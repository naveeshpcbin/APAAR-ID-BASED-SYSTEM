"use client";

import React from "react";
import { User, LogOut, CheckCircle2, Menu } from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface TopBarProps {
  onToggleMobileMenu?: () => void;
}

export function TopBar({ onToggleMobileMenu }: TopBarProps) {
  const { user, logout } = useAuth();

  return (
    <header className="h-14 sm:h-16 bg-white border-b border-slate-200 px-3 sm:px-6 flex items-center justify-between select-none shrink-0">
      {/* Left: Mobile Hamburger & Academic Year Context */}
      <div className="flex items-center gap-2 sm:gap-4 min-w-0">
        {/* Mobile Hamburger Toggle Button */}
        <button
          id="mobile-nav-toggle-btn"
          type="button"
          aria-label="Open Navigation Menu"
          onClick={onToggleMobileMenu}
          className="p-2 -ml-1 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-lg md:hidden flex items-center justify-center cursor-pointer transition"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-1.5 sm:gap-2 text-xs truncate">
          <span className="text-slate-400 font-medium hidden xs:inline">Session:</span>
          <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[11px] sm:text-xs font-semibold bg-slate-100 text-slate-800 border border-slate-300">
            <span className="sm:hidden">2026-27</span>
            <span className="hidden sm:inline">2026-27 (Active Intake)</span>
          </span>
        </div>

        <div className="hidden md:flex items-center gap-2 text-xs border-l border-slate-200 pl-4">
          <span className="flex items-center gap-1.5 text-slate-600">
            <CheckCircle2 className="w-3.5 h-3.5 text-govTeal-600 shrink-0" />
            <span className="font-medium">Rule Engine:</span>
            <span className="font-mono text-slate-800">AICTE-APH-2026-V1</span>
          </span>
        </div>

        <div className="hidden lg:flex items-center border-l border-slate-200 pl-4">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 text-amber-900 border border-amber-300 shadow-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse shrink-0" />
            SIMULATION MODE (Synthetic APAAR Gateway)
          </span>
        </div>
      </div>

      {/* Right: Authoritative Scope & User Profile */}
      <div className="flex items-center gap-2 sm:gap-3 shrink-0">
        {/* Authoritative Scope Indicator */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 sm:px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 hidden md:inline">
            Active Scope:
          </span>
          {user?.role === "AICTE_ADMIN" || user?.role === "REGIONAL_OFFICER" ? (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold bg-blue-100 text-blue-900 border border-blue-300">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600 animate-pulse shrink-0" />
              <span className="hidden md:inline">Central Government Regulator (AICTE HQ)</span>
              <span className="md:hidden">AICTE HQ</span>
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-semibold bg-emerald-100 text-emerald-900 border border-emerald-300 max-w-[140px] md:max-w-none truncate">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse shrink-0" />
              <span className="truncate">{user?.institutionName || "College Portal"}</span>
            </span>
          )}
        </div>

        {/* User Card */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 pl-1.5 sm:pl-2 border-l border-slate-200">
          <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 shrink-0">
            <User className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
          </div>
          <div className="hidden sm:block text-left max-w-[130px] lg:max-w-[180px] truncate">
            <div className="text-xs font-semibold text-slate-900 leading-tight truncate">
              {user?.fullName || "Evaluating Officer"}
            </div>
            <div className="text-[10px] sm:text-[11px] text-slate-500 leading-tight truncate">
              {user?.email || "officer@pramaan.gov.in"}
            </div>
          </div>
          <button
            id="topbar-logout-btn"
            onClick={() => logout()}
            title="Sign out"
            aria-label="Sign out"
            className="p-2 sm:p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition cursor-pointer min-w-[36px] min-h-[36px] sm:min-w-[32px] sm:min-h-[32px] flex items-center justify-center"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
