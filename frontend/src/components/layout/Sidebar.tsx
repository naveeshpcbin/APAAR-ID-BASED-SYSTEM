"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Building2,
  FileSpreadsheet,
  AlertTriangle,
  GitCompare,
  FileCheck2,
  History,
  QrCode,
  GraduationCap,
  Settings,
  ShieldCheck,
  Award,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface NavItem {
  name: string;
  href: string;
  icon: any;
  roles?: string[];
  badge?: string;
}

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const isAdmin = user?.role === "AICTE_ADMIN" || user?.role === "REGIONAL_OFFICER";

  const navigation: NavItem[] = [
    {
      name: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
    },
    {
      name: "Smart Uploader",
      href: "/uploads",
      icon: FileSpreadsheet,
    },
    {
      name: "Student Admissions",
      href: "/admissions",
      icon: GraduationCap,
    },
    {
      name: "Cross-Inst Conflicts",
      href: "/conflicts",
      icon: GitCompare,
      badge: "Active",
    },
    {
      name: "Explainable Anomalies",
      href: "/anomalies",
      icon: AlertTriangle,
    },
    {
      name: "Sanctioned Approvals",
      href: "/approvals",
      icon: Award,
    },
    {
      name: "Institutions Directory",
      href: "/institutions",
      icon: Building2,
    },
    {
      name: "QR Receipt Verification",
      href: "/verification",
      icon: QrCode,
    },
    {
      name: "Tamper-Evident Audit",
      href: "/audit",
      icon: History,
      badge: "SHA-256",
    },
    {
      name: "Reports & Exports",
      href: "/reports",
      icon: FileCheck2,
    },
    {
      name: "System Settings",
      href: "/settings",
      icon: Settings,
    },
  ];

  return (
    <aside className="w-64 bg-govNavy-950 text-slate-300 flex flex-col flex-shrink-0 border-r border-slate-800 select-none">
      {/* Brand Header */}
      <div className="h-16 flex items-center px-5 border-b border-slate-800/80 gap-3">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-govTeal-500 to-govTeal-700 flex items-center justify-center text-white font-bold shadow-md shadow-govTeal-900/40">
          <ShieldCheck className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="text-white font-bold tracking-tight text-sm flex items-center gap-1.5">
            PRAMAAN-AICTE
            <span className="text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded bg-govTeal-600/30 text-govTeal-400 border border-govTeal-500/30">
              SIH &apos;26
            </span>
          </div>
          <div className="text-[11px] text-slate-400 truncate max-w-[150px]">
            Regulatory Monitoring Network
          </div>
        </div>
      </div>

      {/* Role / Context Badge */}
      <div className="mx-3 mt-3 p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
        <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
          Active Workspace
        </div>
        <div className="text-slate-100 font-semibold truncate mt-0.5">
          {user?.institutionName || "AICTE National Headquarters"}
        </div>
        <div className="text-[11px] text-govTeal-400 font-mono mt-0.5 flex items-center gap-1">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-govTeal-500 animate-pulse" />
          {user?.role || "GUEST"} {user?.aicteId ? `(${user.aicteId})` : ""}
        </div>
      </div>

      {/* Nav List */}
      <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
        {navigation.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          const Icon = item.icon;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                isActive
                  ? "bg-govTeal-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-100 hover:bg-slate-900/70"
              }`}
            >
              <div className="flex items-center gap-2.5 truncate">
                <Icon className={`w-4 h-4 ${isActive ? "text-white" : "text-slate-400"}`} />
                <span className="truncate">{item.name}</span>
              </div>
              {item.badge && (
                <span
                  className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide ${
                    isActive
                      ? "bg-white/20 text-white"
                      : "bg-slate-800 text-govTeal-400 border border-slate-700"
                  }`}
                >
                  {item.badge}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Regulatory Compliance Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/60 text-[10px] text-slate-400">
        <div className="flex justify-between items-center mb-1">
          <span>APAAR Mock Gateway</span>
          <span className="text-govTeal-400 font-semibold">ONLINE</span>
        </div>
        <div className="flex justify-between items-center">
          <span>Ed25519 Trust Layer</span>
          <span className="text-govTeal-400 font-semibold">ACTIVE</span>
        </div>
      </div>
    </aside>
  );
}
