"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import {
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Building2,
  GraduationCap,
  Calendar,
  Lock,
  Award,
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function PublicReceiptVerificationPage() {
  const params = useParams();
  const token = params?.token as string;

  const [result, setResult] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function verify() {
      if (!token) return;
      try {
        setLoading(true);
        const res = await apiRequest(`/verification/receipt/${token}`);
        setResult(res);
      } catch (err: any) {
        setResult({
          is_valid: false,
          status: "VERIFICATION_ERROR",
          message: err.message || "Failed to reach verification gateway.",
        });
      } finally {
        setLoading(false);
      }
    }
    verify();
  }, [token]);

  return (
    <div className="min-h-screen bg-slate-100 flex flex-col justify-between p-4 sm:p-6">
      {/* Top Banner */}
      <header className="max-w-2xl mx-auto w-full flex items-center justify-between pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-govTeal-600 text-white flex items-center justify-center font-bold">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-900 tracking-tight">
              PRAMAAN-AICTE National Verification Gateway
            </div>
            <div className="text-[11px] text-slate-500">
              Government of India | AICTE Approved Technical Education Registry
            </div>
          </div>
        </div>
        <span className="text-[10px] font-mono font-semibold px-2 py-0.5 rounded bg-slate-200 text-slate-700">
          Ed25519 Verified
        </span>
      </header>

      {/* Main Verification Certificate Card */}
      <div className="max-w-2xl mx-auto w-full my-auto">
        {loading ? (
          <div className="bg-white p-12 rounded-2xl border border-slate-200 shadow-sm text-center">
            <div className="inline-block w-8 h-8 border-3 border-govTeal-600 border-t-transparent rounded-full animate-spin mb-3" />
            <p className="text-xs text-slate-500 font-medium">
              Verifying cryptographic digital signature against AICTE national key registry...
            </p>
          </div>
        ) : result?.is_valid ? (
          <div className="bg-white rounded-2xl border border-emerald-200 shadow-md overflow-hidden">
            {/* Verified Header */}
            <div className="bg-gradient-to-r from-emerald-600 to-teal-700 p-6 text-white text-center">
              <CheckCircle2 className="w-12 h-12 mx-auto mb-2 text-white" />
              <h1 className="text-lg font-bold tracking-tight">
                Authentic & Cryptographically Verified Enrolment
              </h1>
              <p className="text-xs text-emerald-100 mt-0.5">
                Digital signature matches the official AICTE PRAMAAN authority private key.
              </p>
            </div>

            {/* Certificate Details */}
            <div className="p-6 space-y-5">
              <div className="grid grid-cols-2 gap-4 text-xs pb-4 border-b border-slate-100">
                <div>
                  <div className="text-slate-400 font-medium uppercase text-[10px]">
                    Student Full Name
                  </div>
                  <div className="text-sm font-bold text-slate-900 mt-0.5">
                    {result.canonical_payload.student_name}
                  </div>
                </div>
                <div>
                  <div className="text-slate-400 font-medium uppercase text-[10px]">
                    Academic Identifier (APAAR)
                  </div>
                  <div className="text-sm font-mono font-bold text-slate-900 mt-0.5">
                    {result.canonical_payload.apaar_masked}
                  </div>
                </div>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <div className="text-slate-400 font-medium text-[10px] uppercase">
                    AICTE Approved Technical Institution
                  </div>
                  <div className="text-xs font-bold text-slate-900 flex items-center gap-1.5 mt-0.5">
                    <Building2 className="w-3.5 h-3.5 text-slate-400" />
                    <span>{result.canonical_payload.institution_name}</span>
                    <span className="text-slate-400 font-mono text-[11px]">
                      (AICTE ID: {result.canonical_payload.aicte_id})
                    </span>
                  </div>
                </div>

                <div>
                  <div className="text-slate-400 font-medium text-[10px] uppercase">
                    Approved Technical Programme
                  </div>
                  <div className="text-xs font-semibold text-govTeal-700 flex items-center gap-1.5 mt-0.5">
                    <GraduationCap className="w-3.5 h-3.5" />
                    <span>{result.canonical_payload.programme_name}</span>
                    <span className="font-mono text-slate-500">
                      ({result.canonical_payload.programme_code})
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2">
                  <div>
                    <div className="text-slate-400 font-medium text-[10px] uppercase">
                      Academic Session
                    </div>
                    <div className="text-xs font-mono font-semibold text-slate-800">
                      {result.canonical_payload.academic_year}
                    </div>
                  </div>
                  <div>
                    <div className="text-slate-400 font-medium text-[10px] uppercase">
                      Enrolment Status
                    </div>
                    <div className="text-xs font-bold text-emerald-600">
                      {result.canonical_payload.enrolment_status}
                    </div>
                  </div>
                </div>
              </div>

              {/* Cryptographic Signature Footer */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-[11px] font-mono text-slate-500 space-y-1">
                <div className="flex items-center gap-1.5 text-slate-700 font-semibold text-xs">
                  <Lock className="w-3.5 h-3.5 text-govTeal-600" />
                  <span>Cryptographic Assertion Provenance</span>
                </div>
                <div className="truncate">
                  <span>Signature (Base64):</span> {result.signature}
                </div>
                <div className="truncate">
                  <span>SHA-256 Digest:</span> {result.payload_digest}
                </div>
                <div className="text-slate-400 text-[10px] pt-1">
                  Verified against PRAMAAN Trust Root | Token: {token}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-rose-200 shadow-md p-8 text-center space-y-3">
            <XCircle className="w-12 h-12 mx-auto text-rose-600" />
            <h1 className="text-lg font-bold text-slate-900">
              Receipt Verification Failed
            </h1>
            <p className="text-xs text-rose-600 font-medium max-w-md mx-auto">
              {result?.message || "Invalid token or signature mismatch. This claim could not be verified."}
            </p>
            <div className="text-[11px] font-mono text-slate-400 pt-3 border-t border-slate-100">
              Token ID: {token}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <footer className="max-w-2xl mx-auto w-full text-center text-[10px] text-slate-400 pt-4">
        PRAMAAN-AICTE National Academic Verification Network | Smart India Hackathon 2026 Problem Statement SIH26263
      </footer>
    </div>
  );
}
