"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Building2,
  Lock,
  Mail,
  ArrowRight,
  ArrowLeft,
  ShieldAlert,
  Eye,
  EyeOff,
  CheckCircle2,
  AlertCircle,
  Sparkles,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function CollegeLoginPage() {
  const router = useRouter();
  const { login, logout, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Form input validation
    if (!email.trim() || !password) {
      setError("Please provide both institutional email and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const user = await login(email.trim(), password);

      // Backend role guard: Ensure this account is an institutional account
      if (user.role === "AICTE_ADMIN" || user.role === "REGIONAL_OFFICER") {
        logout();
        setError(
          "Access Restricted: This account possesses AICTE Central Regulator privileges. Please sign in through the AICTE Central Portal."
        );
        return;
      }

      // Valid college user -> Redirect to College smart uploader workspace
      router.push("/uploads");
    } catch (err: any) {
      setError(
        err.message || "Invalid institution nodal credentials or unauthorized account."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  // Quick fill helper for demo/evaluator convenience
  const handleAutofill = async (demoEmail: string, demoPass: string, autoSubmit = false) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setError(null);
    if (autoSubmit) {
      setIsSubmitting(true);
      try {
        const user = await login(demoEmail, demoPass);
        if (user.role === "AICTE_ADMIN" || user.role === "REGIONAL_OFFICER") {
          logout();
          setError(
            "Access Restricted: This account possesses AICTE Central Regulator privileges. Please sign in through the AICTE Central Portal."
          );
          return;
        }
        router.push("/uploads");
      } catch (err: any) {
        setError(
          err.message || "Invalid institution nodal credentials or unauthorized account."
        );
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center py-12 sm:px-6 lg:px-8 relative select-none">
      {/* Background Subtle Gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-emerald-950/20 via-slate-950 to-slate-950 pointer-events-none" />

      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center relative z-10">
        <Link
          href="/login"
          id="back-to-directory-link"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-emerald-400 mb-6 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Portal Directory</span>
        </Link>

        {/* Institution Badge */}
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-700 text-white flex items-center justify-center mx-auto mb-3 shadow-xl shadow-emerald-950/50 border border-emerald-400/30">
          <Building2 className="w-7 h-7" />
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-white">
          College Portal Sign In
        </h1>
        <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
          Institutional Nodal Officer Access for Student Admission Ingestion &amp; 3-Way Reconciliation
        </p>

        <div className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          <span>AUTHORIZED INSTITUTION WORKSPACE</span>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0 relative z-10">
        <div className="bg-white py-8 px-6 shadow-2xl rounded-2xl sm:px-10 space-y-6 border border-slate-200">
          {/* Institution Authorization Requirement Alert */}
          <div className="p-3 bg-emerald-50/80 border border-emerald-200 rounded-xl text-[11px] text-emerald-900 leading-relaxed flex items-start gap-2">
            <Building2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <span>
              <strong>Institutional Membership Notice:</strong> College access requires an active institution nodal account linked to an AICTE-approved institution ID in the authoritative database.
            </span>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              id="college-error-banner"
              role="alert"
              className="p-3.5 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-start gap-2.5 animate-in fade-in duration-200"
            >
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
              <div className="leading-snug">{error}</div>
            </div>
          )}

          {/* Sign In Form */}
          <form onSubmit={handleSubmit} className="space-y-4 text-xs" noValidate>
            <div>
              <label
                htmlFor="college-email-input"
                className="block font-semibold text-slate-700 mb-1"
              >
                Institutional Nodal Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-400 pointer-events-none" />
                <input
                  id="college-email-input"
                  name="email"
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="nodal.dtu@dtu.ac.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-600 text-slate-900 placeholder:text-slate-400 font-sans transition"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="college-password-input"
                className="block font-semibold text-slate-700 mb-1"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-400 pointer-events-none" />
                <input
                  id="college-password-input"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-10 py-2.5 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-emerald-600 text-slate-900 placeholder:text-slate-400 font-sans transition"
                />
                <button
                  id="college-toggle-password-btn"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 p-0.5 rounded focus:outline-none focus:ring-1 focus:ring-emerald-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              id="college-submit-btn"
              type="submit"
              disabled={isSubmitting || isLoading}
              className="w-full py-2.5 bg-emerald-700 hover:bg-emerald-800 disabled:bg-emerald-400 text-white rounded-xl font-semibold shadow-md flex items-center justify-center gap-2 transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-600 cursor-pointer"
            >
              {isSubmitting || isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Authenticating Nodal Officer...</span>
                </>
              ) : (
                <>
                  <span>Sign In &amp; Enter College Workspace</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Development Demo Test Accounts Section */}
          <div className="pt-4 border-t border-slate-100">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500">
                Development Test Accounts [DEMO]
              </span>
              <span className="text-[10px] text-emerald-600 font-medium">Click to fill</span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                id="demo-dtu-btn"
                type="button"
                onClick={() => handleAutofill("nodal.dtu@dtu.ac.in", "College@12345", true)}
                className="p-2.5 bg-slate-50 hover:bg-emerald-50/80 border border-slate-200 hover:border-emerald-300 rounded-xl text-left transition flex flex-col group cursor-pointer focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <span className="font-bold text-slate-800 group-hover:text-emerald-800">
                  DTU Delhi Nodal
                </span>
                <span className="text-[10px] text-slate-500">Prof. Amit Srivastava</span>
                <span className="text-[9px] font-mono text-emerald-700 mt-1">
                  nodal.dtu@dtu.ac.in
                </span>
              </button>

              <button
                id="demo-coep-btn"
                type="button"
                onClick={() => handleAutofill("nodal.coep@coep.ac.in", "College@12345", true)}
                className="p-2.5 bg-slate-50 hover:bg-emerald-50/80 border border-slate-200 hover:border-emerald-300 rounded-xl text-left transition flex flex-col group cursor-pointer focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                <span className="font-bold text-slate-800 group-hover:text-emerald-800">
                  COEP Pune Nodal
                </span>
                <span className="text-[10px] text-slate-500">Dr. Sandeep Meshram</span>
                <span className="text-[9px] font-mono text-emerald-700 mt-1">
                  nodal.coep@coep.ac.in
                </span>
              </button>
            </div>

            {/* New College Registration Link */}
            <div className="mt-4 pt-3 border-t border-slate-100 text-center">
              <Link
                id="college-register-link"
                href="/register"
                className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 hover:text-emerald-900 transition"
              >
                <span>New AICTE-approved institution? Register your college &rarr;</span>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
