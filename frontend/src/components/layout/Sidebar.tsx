"use client";

import React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
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
  Database,
  Lock,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

interface NavItem {
  name: string;
  href: string;
  icon: any;
  badge?: string;
  requiresCentral?: boolean;
}

interface NavGroup {
  title: string;
  items: NavItem[];
}

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useAuth();
  const isAdmin = user?.role === "AICTE_ADMIN" || user?.role === "REGIONAL_OFFICER";

  // Build navigation groups strictly based on tenant role
  const navGroups: NavGroup[] = isAdmin
    ? [
        {
          title: "Central Regulatory Scope",
          items: [
            {
              name: "National Dashboard",
              href: "/dashboard",
              icon: LayoutDashboard,
            },
            {
              name: "Submissions Review",
              href: "/uploads",
              icon: FileSpreadsheet,
            },
            {
              name: "Student Admissions",
              href: "/admissions",
              icon: GraduationCap,
            },
            {
              name: "Intake & Approvals",
              href: "/approvals",
              icon: Award,
            },
          ],
        },
        {
          title: "AICTE Central Intelligence",
          items: [
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
              name: "Institutions Directory",
              href: "/institutions",
              icon: Building2,
            },
            {
              name: "Reports & Exports",
              href: "/reports",
              icon: FileCheck2,
            },
            {
              name: "Reference Registry",
              href: "/reference-data",
              icon: Database,
              badge: "DEMO",
            },
          ],
        },
        {
          title: "Trust & Governance",
          items: [
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
              name: "System Settings",
              href: "/settings",
              icon: Settings,
            },
          ],
        },
      ]
    : [
        {
          title: "Institution Workspace",
          items: [
            {
              name: "My Submissions & Uploads",
              href: "/uploads",
              icon: FileSpreadsheet,
            },
            {
              name: "Student Admissions Roll",
              href: "/admissions",
              icon: GraduationCap,
            },
          ],
        },
        {
          title: "Verification Services",
          items: [
            {
              name: "QR Receipt Verification",
              href: "/verification",
              icon: QrCode,
            },
          ],
        },
        {
          title: "AICTE Central Regulator (Restricted)",
          items: [
            {
              name: "AICTE Central Website",
              href: "/dashboard",
              icon: Lock,
              badge: "AICTE HQ",
              requiresCentral: true,
            },
            {
              name: "Cross-Inst Conflicts",
              href: "/conflicts",
              icon: GitCompare,
              badge: "CENTRAL",
              requiresCentral: true,
            },
            {
              name: "Reference Registry",
              href: "/reference-data",
              icon: Database,
              badge: "CENTRAL",
              requiresCentral: true,
            },
            {
              name: "Tamper-Evident Audit",
              href: "/audit",
              icon: History,
              badge: "CENTRAL",
              requiresCentral: true,
            },
          ],
        },
      ];

  const handleNavClick = (e: React.MouseEvent, item: NavItem) => {
    if (!isAdmin && item.requiresCentral) {
      e.preventDefault();
      // Route directly to restricted central route to trigger interceptor
      router.push(item.href);
    }
  };

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
            {isAdmin ? "Central Regulatory HQ" : "College Nodal Portal"}
          </div>
        </div>
      </div>

      {/* Tenant / Role Context Badge */}
      <div className="mx-3 mt-3 p-2.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
        <div className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
          {isAdmin ? "Central Authority Scope" : "Assigned Institution Scope"}
        </div>
        <div className="text-slate-100 font-semibold truncate mt-0.5">
          {user?.institutionName || (isAdmin ? "AICTE National Headquarters" : "Affiliated College")}
        </div>
        <div className="text-[11px] text-govTeal-400 font-mono mt-0.5 flex items-center gap-1">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-govTeal-500 animate-pulse" />
          {user?.role || "GUEST"} {user?.aicteId ? `(${user.aicteId})` : ""}
        </div>
      </div>

      {/* Navigation Groups */}
      <nav className="flex-1 px-3 py-3 space-y-4 overflow-y-auto">
        {navGroups.map((group) => (
          <div key={group.title} className="space-y-1">
            <div className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-slate-500">
              {group.title}
            </div>
            {group.items.map((item) => {
              const isActive =
                !item.requiresCentral &&
                (pathname === item.href || pathname.startsWith(item.href + "/"));
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={(e) => handleNavClick(e, item)}
                  className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors ${
                    item.requiresCentral
                      ? "text-amber-400/90 hover:text-amber-300 hover:bg-amber-950/30 border border-amber-900/40"
                      : isActive
                      ? "bg-govTeal-600 text-white shadow-sm"
                      : "text-slate-400 hover:text-slate-100 hover:bg-slate-900/70"
                  }`}
                >
                  <div className="flex items-center gap-2.5 truncate">
                    <Icon
                      className={`w-4 h-4 ${
                        item.requiresCentral
                          ? "text-amber-400"
                          : isActive
                          ? "text-white"
                          : "text-slate-400"
                      }`}
                    />
                    <span className="truncate">{item.name}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={`text-[9px] font-bold px-1.5 py-0.5 rounded uppercase tracking-wide ${
                        item.requiresCentral
                          ? "bg-amber-950 text-amber-300 border border-amber-800"
                          : isActive
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
          </div>
        ))}
      </nav>

      {/* Regulatory Compliance Footer */}
      <div className="p-3 border-t border-slate-800/80 bg-slate-950/60 text-[10px] text-slate-400">
        <div className="flex justify-between items-center mb-1">
          <span>Tenant Separation</span>
          <span className="text-emerald-400 font-semibold font-mono">ENFORCED</span>
        </div>
        <div className="flex justify-between items-center">
          <span>Ed25519 Trust Layer</span>
          <span className="text-govTeal-400 font-semibold font-mono">ACTIVE</span>
        </div>
      </div>
    </aside>
  );
}
