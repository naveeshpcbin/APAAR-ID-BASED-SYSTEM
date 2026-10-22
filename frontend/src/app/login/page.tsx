"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldCheck, Lock, Mail, ArrowRight, CheckCircle2 } from "lucide-react";
import { useAuth, DEMO_CREDENTIALS } from "@/lib/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { login, switchDemoUser, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid credentials.");
    }
  };

  const handleQuickLogin = async (persona: "admin" | "dtu" | "coep" | "verifier") => {
    setError(null);
    try {
      await switchDemoUser(persona);
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Quick sign in failed.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <div className="w-12 h-12 rounded-xl bg-govTeal-600 text-white flex items-center justify-center mx-auto mb-3 shadow-lg shadow-govTeal-900/50">
          <ShieldCheck className="w-7 h-7" />
        </div>
        <h1 className="text-2xl font-bold tracking-tight text-white">PRAMAAN-AICTE</h1>
        <p className="mt-1 text-xs text-slate-400">
          Platform for Real-time APAAR-linked Monitoring, Auditing, and Academic Network
        </p>
        <span className="inline-block mt-2 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-slate-800 text-govTeal-400 border border-slate-700">
          SIH 2026 Problem Statement SIH26263
        </span>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10 space-y-6">
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-xs">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div>
              <label className="block font-medium text-slate-700 mb-1">Official Email Address</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <input
                  type="email"
                  required
                  placeholder="name@aicte.gov.in or nodal@college.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-govTeal-600"
                />
              </div>
            </div>

            <div>
              <label className="block font-medium text-slate-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
                <input
                  type="password"
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-9 pr-3 py-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-govTeal-600"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-2.5 bg-govNavy-900 hover:bg-govNavy-800 text-white rounded-lg font-semibold shadow-xs flex items-center justify-center gap-2 transition"
            >
              <span>Authenticate & Enter Workspace</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>

          {/* Quick Demo Switcher Section */}
          <div className="pt-4 border-t border-slate-200 space-y-2">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-center">
              SIH Evaluator Quick Access (One-Click Login)
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <button
                type="button"
                onClick={() => handleQuickLogin("admin")}
                className="p-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-left transition"
              >
                <div className="font-bold text-slate-900">AICTE Central</div>
                <div className="text-[10px] text-slate-500">Bureau of Approval</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin("dtu")}
                className="p-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-left transition"
              >
                <div className="font-bold text-slate-900">DTU Delhi</div>
                <div className="text-[10px] text-slate-500">Nodal Officer Portal</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin("coep")}
                className="p-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-left transition"
              >
                <div className="font-bold text-slate-900">COEP Pune</div>
                <div className="text-[10px] text-slate-500">Nodal Officer Portal</div>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin("verifier")}
                className="p-2.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-lg text-left transition"
              >
                <div className="font-bold text-slate-900">Verifier</div>
                <div className="text-[10px] text-slate-500">Public Verification</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
