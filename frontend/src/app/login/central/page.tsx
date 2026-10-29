"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  ShieldCheck,
  Lock,
  Mail,
  ArrowRight,
  ArrowLeft,
  Scale,
  Eye,
  EyeOff,
  AlertCircle,
  ShieldAlert,
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";

export default function CentralLoginPage() {
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
      setError("Please provide both official reviewer email and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const user = await login(email.trim(), password);

      // Backend role guard: Ensure this account has central regulatory authority
      if (user.role !== "AICTE_ADMIN" && user.role !== "REGIONAL_OFFICER") {
        logout();
        setError(
          "Access Restricted: This account is an Institutional Nodal account. Please sign in through the College Portal."
        );
        return;
      }

      // Valid central reviewer -> Redirect to central dashboard
      router.push("/dashboard");
    } catch (err: any) {
      setError(
        err.message || "Invalid central reviewer credentials or unassigned regulatory role."
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
        if (user.role !== "AICTE_ADMIN" && user.role !== "REGIONAL_OFFICER") {
          logout();
          setError(
            "Access Restricted: This account does not possess AICTE Central Regulator authority. Please sign in through your respective College Portal."
          );
          return;
        }
        router.push("/dashboard");
      } catch (err: any) {
        setError(
          err.message || "Invalid central reviewer credentials or unassigned regulatory role."
        );
      } finally {
        setIsSubmitting(false);
      }
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center px-4 py-8 sm:py-12 sm:px-6 lg:px-8 relative select-none">
      {/* Background Subtle Gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-blue-950/20 via-slate-950 to-slate-950 pointer-events-none" />

      <div className="w-full max-w-md mx-auto text-center relative z-10">
        <Link
          href="/login"
          id="back-to-directory-link"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-blue-400 mb-6 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Portal Directory</span>
        </Link>

        {/* Regulatory Seal Badge */}
        <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-900 text-white flex items-center justify-center mx-auto mb-3 shadow-xl shadow-blue-950/60 border border-blue-400/30">
          <Scale className="w-7 h-7" />
        </div>

        <h1 className="text-2xl font-bold tracking-tight text-white">
          AICTE Central Portal
        </h1>
        <p className="mt-1 text-xs text-slate-400 max-w-sm mx-auto">
          Bureau of Approval &amp; Regional Directorate Adjudication Workspace
        </p>

        <div className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-blue-950 text-blue-400 border border-blue-800">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
          <span>RESTRICTED REGULATORY ACCESS (APH 2026-27)</span>
        </div>
      </div>

      <div className="mt-6 sm:mt-8 w-full max-w-md mx-auto relative z-10">
        <div className="bg-white py-6 px-4 sm:py-8 sm:px-10 shadow-2xl rounded-2xl space-y-6 border border-slate-200">
          {/* Regulatory Access Notice */}
          <div className="p-3 bg-blue-50/80 border border-blue-200 rounded-xl text-[11px] text-blue-950 leading-relaxed flex items-start gap-2">
            <ShieldCheck className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <span>
              <strong>Administrative Provisioning Notice:</strong> Central privileges are provisioned strictly through an internal administrator process. Public self-registration never grants central review authority.
            </span>
          </div>

          {/* Error Banner */}
          {error && (
            <div
              id="central-error-banner"
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
                htmlFor="central-email-input"
                className="block font-semibold text-slate-700 mb-1"
              >
                Official AICTE Reviewer Email
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-400 pointer-events-none" />
                <input
                  id="central-email-input"
                  name="email"
                  type="email"
                  required
                  autoComplete="email"
                  placeholder="aicte.admin@pramaan.gov.in"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900 placeholder:text-slate-400 font-sans transition"
                />
              </div>
            </div>

            <div>
              <label
                htmlFor="central-password-input"
                className="block font-semibold text-slate-700 mb-1"
              >
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-400 pointer-events-none" />
                <input
                  id="central-password-input"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  required
                  autoComplete="current-password"
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-10 py-2.5 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-600 text-slate-900 placeholder:text-slate-400 font-sans transition"
                />
                <button
                  id="central-toggle-password-btn"
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-2.5 text-slate-400 hover:text-slate-600 p-0.5 rounded focus:outline-none focus:ring-1 focus:ring-blue-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              id="central-submit-btn"
              type="submit"
              disabled={isSubmitting || isLoading}
              className="w-full py-2.5 bg-blue-900 hover:bg-blue-800 disabled:bg-blue-400 text-white rounded-xl font-semibold shadow-md flex items-center justify-center gap-2 transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-600 cursor-pointer"
            >
              {isSubmitting || isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Verifying Regulatory Credentials...</span>
                </>
              ) : (
                <>
                  <span>Sign In &amp; Enter Central Workspace</span>
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
              <span className="text-[10px] text-blue-600 font-medium">Click to fill</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
              <button
                id="demo-central-admin-btn"
                type="button"
                onClick={() =>
                  handleAutofill("aicte.admin@pramaan.gov.in", "Admin@12345", true)
                }
                className="p-2.5 bg-slate-50 hover:bg-blue-50/80 border border-slate-200 hover:border-blue-300 rounded-xl text-left transition flex flex-col group cursor-pointer focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <span className="font-bold text-slate-800 group-hover:text-blue-800">
                  AICTE Central HQ
                </span>
                <span className="text-[10px] text-slate-500">Dr. Sunita Deshmukh</span>
                <span className="text-[9px] font-mono text-blue-700 mt-1 break-all">
                  aicte.admin@pramaan.gov.in
                </span>
              </button>

              <button
                id="demo-regional-officer-btn"
                type="button"
                onClick={() => handleAutofill("ro.mumbai@aicte.gov.in", "Officer@12345", true)}
                className="p-2.5 bg-slate-50 hover:bg-blue-50/80 border border-slate-200 hover:border-blue-300 rounded-xl text-left transition flex flex-col group cursor-pointer focus:outline-none focus:ring-1 focus:ring-blue-500"
              >
                <span className="font-bold text-slate-800 group-hover:text-blue-800">
                  Regional Office (WRO)
                </span>
                <span className="text-[10px] text-slate-500">Rajesh Verma</span>
                <span className="text-[9px] font-mono text-blue-700 mt-1 break-all">
                  ro.mumbai@aicte.gov.in
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
