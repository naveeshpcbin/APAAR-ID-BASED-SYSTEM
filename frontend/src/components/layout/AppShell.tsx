"use client";

import React, { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/lib/auth-context";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { ShieldAlert, ArrowRight, LogOut, Lock, Building2 } from "lucide-react";
import Link from "next/link";

// Routes restricted strictly to Central AICTE Government Authorities (HQ / Regional)
const CENTRAL_ONLY_ROUTES = [
  "/dashboard",
  "/conflicts",
  "/anomalies",
  "/institutions",
  "/approvals",
  "/reference-data",
  "/audit",
  "/reports",
  "/settings",
];

function AppShellContent({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout, isLoading } = useAuth();
  const [countdown, setCountdown] = useState<number>(5);
  const [showCentralPrompt, setShowCentralPrompt] = useState(false);

  const isPublicPage =
    pathname.startsWith("/login") ||
    pathname.startsWith("/register") ||
    pathname.startsWith("/verification/receipt/");

  // Identify if college user is attempting to access central government regulatory routes
  const isCollegeUser = user?.role === "INSTITUTION_NODAL";
  const isRestrictedCentralRoute =
    isCollegeUser &&
    CENTRAL_ONLY_ROUTES.some((route) => pathname === route || pathname.startsWith(route + "/"));

  // Check unauthenticated state
  useEffect(() => {
    if (!isLoading && !user && !isPublicPage) {
      router.replace("/login");
    }
  }, [isLoading, user, isPublicPage, router]);

  const handleProceedToCentral = React.useCallback(() => {
    logout("/login/central");
  }, [logout]);

  // Handle countdown and auto-logout when college user lands on an AICTE Central page
  useEffect(() => {
    if (isRestrictedCentralRoute) {
      setShowCentralPrompt(true);
      setCountdown(5);

      const timer = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            clearInterval(timer);
            handleProceedToCentral();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearInterval(timer);
    } else {
      setShowCentralPrompt(false);
    }
  }, [isRestrictedCentralRoute, pathname, handleProceedToCentral]);

  // Public pages (Login, Receipt verification) have no sidebar/topbar
  if (isPublicPage) {
    return <main className="min-h-screen bg-slate-900">{children}</main>;
  }

  // Loading session state
  if (isLoading) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-900 text-white">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-3 border-teal-500 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-xs font-medium text-slate-400 tracking-wide uppercase">
            Verifying PRAMAAN-AICTE Session...
          </p>
        </div>
      </div>
    );
  }

  // Unauthorized guard fallback while redirecting
  if (!user) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-950 p-4">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center space-y-5 shadow-2xl">
          <div className="w-14 h-14 bg-red-950/80 border border-red-800/60 text-red-400 rounded-2xl flex items-center justify-center mx-auto shadow-lg">
            <ShieldAlert className="w-7 h-7" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-white">Authentication Required</h2>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              This workspace is restricted to authorized institution nodals and central AICTE officers. Please sign in to continue.
            </p>
          </div>
          <Link
            href="/login"
            className="inline-flex items-center justify-center gap-2 w-full py-2.5 bg-teal-600 hover:bg-teal-500 text-white font-semibold text-xs rounded-xl transition shadow-md"
          >
            <span>Go to Portal Login</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    );
  }

  // INTERCEPTOR: College Nodal attempting to access AICTE Central Regulator Portal
  if (isRestrictedCentralRoute || showCentralPrompt) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-slate-950 p-4 select-none">
        <div className="max-w-lg w-full bg-slate-900 border-2 border-amber-500/60 rounded-3xl p-8 text-center space-y-6 shadow-2xl relative overflow-hidden">
          {/* Subtle decorative glow */}
          <div className="absolute -top-24 -left-24 w-48 h-48 bg-amber-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -right-24 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="w-16 h-16 bg-amber-950/80 border border-amber-500/40 text-amber-400 rounded-2xl flex items-center justify-center mx-auto shadow-lg shadow-amber-950/50">
            <Lock className="w-8 h-8" />
          </div>

          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-mono font-semibold bg-amber-950/60 text-amber-300 border border-amber-800">
              <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
              <span>CENTRAL GOVERNMENT ACCESS RESTRICTION</span>
            </div>
            <h2 className="text-xl font-extrabold text-white tracking-tight">
              Please log in to the AICTE website.
            </h2>
            <p className="text-xs text-slate-300 leading-relaxed max-w-md mx-auto pt-1">
              You are currently logged in under an <strong className="text-white font-semibold">Institutional Nodal Account</strong> (<span className="text-emerald-400 font-mono">{user.institutionName || "College Portal"}</span>).
            </p>
            <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800 text-left text-[11px] text-slate-400 space-y-1 mt-2">
              <div className="flex items-center gap-2 text-slate-300 font-semibold">
                <Building2 className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                <span>Strict Tenant & Regulatory Partitioning Enforced</span>
              </div>
              <p>
                One institution&apos;s records do not exist in another institution, and institutional portals cannot directly access AICTE Central regulatory controls, national registries, or cross-institutional conflicts.
              </p>
            </div>
          </div>

          {/* Action buttons */}
          <div className="pt-2 space-y-3">
            <button
              onClick={handleProceedToCentral}
              className="inline-flex items-center justify-center gap-2 w-full py-3 bg-gradient-to-r from-blue-600 via-blue-500 to-teal-500 hover:from-blue-500 hover:to-teal-400 text-white font-bold text-xs rounded-xl transition shadow-lg shadow-blue-950/60 cursor-pointer"
            >
              <LogOut className="w-4 h-4" />
              <span>Log Out & Go to AICTE Central Website ({countdown}s)</span>
            </button>

            <button
              onClick={() => router.replace("/uploads")}
              className="inline-flex items-center justify-center gap-1.5 w-full py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium text-xs rounded-xl border border-slate-700 transition cursor-pointer"
            >
              <span>Return to My College Submissions</span>
            </button>
          </div>

          <div className="text-[10px] text-slate-500 font-mono">
            Target Route: <span className="text-slate-400">{pathname}</span> &bull; Enforcing DPDP &amp; AICTE Tenant Isolation
          </div>
        </div>
      </div>
    );
  }

  // Authenticated Workspace Layout
  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans">
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopBar />
        <main className="flex-1 overflow-y-auto p-6 bg-slate-50">
          {children}
        </main>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AppShellContent>{children}</AppShellContent>
    </AuthProvider>
  );
}
