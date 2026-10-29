"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  QrCode,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Copy,
  ExternalLink,
  RefreshCw,
  AlertTriangle,
  FileKey,
  Key,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function VerificationPage() {
  const { user } = useAuth();
  const [admissions, setAdmissions] = useState<any[]>([]);
  const [selectedAdmissionId, setSelectedAdmissionId] = useState<number | null>(null);
  const [issuedReceipt, setIssuedReceipt] = useState<any | null>(null);
  const [verifyTokenInput, setVerifyTokenInput] = useState("");
  const [verifyResult, setVerifyResult] = useState<any | null>(null);
  const [isIssuing, setIsIssuing] = useState(false);
  const [isVerifying, setIsVerifying] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function loadAdmissions() {
      try {
        const res = await apiRequest("/admissions?limit=15");
        setAdmissions(res);
        if (res.length > 0) {
          setSelectedAdmissionId(res[0].id);
        }
      } catch (err: any) {
        console.error(err);
      }
    }
    loadAdmissions();
  }, [user]);

  const handleIssueReceipt = async () => {
    if (!selectedAdmissionId) return;
    setIsIssuing(true);
    setIssuedReceipt(null);
    try {
      const res = await apiRequest("/verification/receipts", {
        method: "POST",
        body: JSON.stringify({
          admission_id: selectedAdmissionId,
          expiry_days: 30,
          claim_scope: "ACTIVE_ENROLMENT_STATUS",
        }),
      });
      setIssuedReceipt(res);
      setVerifyTokenInput(res.receipt_token);
    } catch (err: any) {
      alert(`Failed to issue receipt: ${err.message}`);
    } finally {
      setIsIssuing(false);
    }
  };

  const handleVerifyToken = async (overrideToken?: string) => {
    const token = overrideToken || verifyTokenInput;
    if (!token) return;
    setIsVerifying(true);
    setVerifyResult(null);
    try {
      const res = await apiRequest(`/verification/receipt/${token}`);
      setVerifyResult(res);
    } catch (err: any) {
      setVerifyResult({
        is_valid: false,
        status: "ERROR",
        message: err.message,
      });
    } finally {
      setIsVerifying(false);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Cryptographic Ed25519 Signed Verification Receipts
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Privacy-preserving credential verification. Opaque tokens with asymmetric digital signatures. Zero raw student PII in public URLs.
          </p>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-govTeal-700 bg-govTeal-50 border border-govTeal-200 px-3 py-1 rounded-lg font-mono">
          <Key className="w-3.5 h-3.5" />
          <span>Ed25519 Curve25519 Public Key Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Issue Receipt */}
        <div className="bg-white p-4 sm:p-6 rounded-xl border border-slate-200/90 shadow-xs space-y-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileKey className="w-4 h-4 text-govTeal-600" />
              Issue Signed Receipt for Student Record
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Select an admitted student to generate a tamper-evident, cryptographically signed verification receipt and QR code.
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-700 mb-1">
              Select Enrolled Student Record
            </label>
            <select
              value={selectedAdmissionId || ""}
              onChange={(e) => setSelectedAdmissionId(Number(e.target.value))}
              className="w-full text-xs border border-slate-300 rounded-lg p-2.5 bg-white"
            >
              {admissions.map((adm) => (
                <option key={adm.id} value={adm.id}>
                  {adm.student?.full_name} ({adm.student?.apaar_masked}) — {adm.programme_code} ({adm.institution_name})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleIssueReceipt}
            disabled={!selectedAdmissionId || isIssuing}
            className="w-full py-2.5 bg-govTeal-600 hover:bg-govTeal-700 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center justify-center gap-2 transition"
          >
            {isIssuing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Signing Payload with Ed25519 Private Key...</span>
              </>
            ) : (
              <>
                <QrCode className="w-4 h-4" />
                <span>Issue Asymmetric Signed Receipt & QR Code</span>
              </>
            )}
          </button>

          {/* Generated Receipt Result */}
          {issuedReceipt && (
            <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-4">
              <div className="flex flex-col sm:flex-row items-center sm:items-start gap-4">
                <img
                  src={issuedReceipt.qr_code_base64}
                  alt="Verification QR Code"
                  className="w-28 h-28 rounded-lg border border-slate-300 bg-white p-1 shrink-0"
                />
                <div className="space-y-1 text-xs w-full min-w-0">
                  <div className="text-[10px] uppercase font-bold text-slate-400">
                    Opaque Receipt Token
                  </div>
                  <div className="font-mono text-xs font-bold text-slate-900 break-all">
                    {issuedReceipt.receipt_token}
                  </div>
                  <div className="text-[11px] text-slate-500">
                    Expires: {new Date(issuedReceipt.expires_at).toLocaleDateString()}
                  </div>
                  <div className="pt-1 flex flex-wrap gap-2">
                    <button
                      onClick={() => copyToClipboard(issuedReceipt.receipt_token)}
                      className="px-2 py-1 bg-white border border-slate-300 rounded text-[11px] font-medium flex items-center gap-1 hover:bg-slate-50"
                    >
                      <Copy className="w-3 h-3" />
                      <span>{copied ? "Copied!" : "Copy Token"}</span>
                    </button>
                    <Link
                      href={issuedReceipt.verification_url}
                      target="_blank"
                      className="px-2 py-1 bg-govTeal-600 text-white rounded text-[11px] font-medium flex items-center gap-1 hover:bg-govTeal-700"
                    >
                      <ExternalLink className="w-3 h-3" />
                      <span>Open Public Portal</span>
                    </Link>
                  </div>
                </div>
              </div>

              {/* Cryptographic Proof Details */}
              <div className="pt-2 border-t border-slate-200 text-[11px] space-y-1 font-mono text-slate-600 overflow-hidden">
                <div className="truncate">
                  <span className="text-slate-400">SHA-256 Digest:</span> {issuedReceipt.payload_digest}
                </div>
                <div className="truncate">
                  <span className="text-slate-400">Ed25519 Signature:</span> {issuedReceipt.signature.slice(0, 32)}...
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Right: Verify Receipt Gateway */}
        <div className="bg-white p-4 sm:p-6 rounded-xl border border-slate-200/90 shadow-xs space-y-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-govTeal-600" />
              Receipt Verification Gateway
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Validate authenticity of any student verification receipt using asymmetric signature verification.
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-xs font-medium text-slate-700">
              Receipt Token (from QR Code or URL)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="rcpt_..."
                value={verifyTokenInput}
                onChange={(e) => setVerifyTokenInput(e.target.value)}
                className="flex-1 text-xs border border-slate-300 rounded-lg p-2.5 font-mono"
              />
              <button
                onClick={() => handleVerifyToken()}
                disabled={!verifyTokenInput || isVerifying}
                className="px-4 py-2 bg-govNavy-900 hover:bg-govNavy-800 disabled:opacity-50 text-white rounded-lg text-xs font-semibold shadow-xs flex items-center gap-1.5 transition"
              >
                {isVerifying ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : "Verify"}
              </button>
            </div>
          </div>

          {/* Quick Demo Buttons for Gate 6 */}
          <div className="pt-2 flex flex-wrap items-center gap-2 text-xs">
            <span className="text-slate-400 text-[11px]">Quick Tests:</span>
            <button
              onClick={() => {
                setVerifyTokenInput("rcpt_532763c1caad4cf8bd1ea9bdf7a4b50d");
                handleVerifyToken("rcpt_532763c1caad4cf8bd1ea9bdf7a4b50d");
              }}
              className="px-2 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded text-[11px] font-medium"
            >
              Test Pre-seeded Valid Receipt
            </button>
            <button
              onClick={() => {
                setVerifyTokenInput("rcpt_tampered_forged_9999");
                handleVerifyToken("rcpt_tampered_forged_9999");
              }}
              className="px-2 py-1 bg-rose-50 hover:bg-rose-100 text-rose-700 rounded text-[11px] font-medium border border-rose-200"
            >
              Test Invalid / Forged Token
            </button>
          </div>

          {/* Verification Result Card */}
          {verifyResult && (
            <div
              className={`p-5 rounded-xl border space-y-3 ${
                verifyResult.is_valid
                  ? "bg-emerald-50/50 border-emerald-200"
                  : "bg-rose-50/50 border-rose-200"
              }`}
            >
              <div className="flex items-center gap-2">
                {verifyResult.is_valid ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                ) : (
                  <XCircle className="w-5 h-5 text-rose-600" />
                )}
                <div>
                  <div
                    className={`text-xs font-bold ${
                      verifyResult.is_valid ? "text-emerald-900" : "text-rose-900"
                    }`}
                  >
                    {verifyResult.status}
                  </div>
                  <div className="text-xs text-slate-600">{verifyResult.message}</div>
                </div>
              </div>

              {verifyResult.canonical_payload && (
                <div className="p-3 bg-white rounded-lg border border-slate-200 text-xs space-y-1.5">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Student:</span>
                    <span className="font-semibold text-slate-900">
                      {verifyResult.canonical_payload.student_name}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Masked APAAR:</span>
                    <span className="font-mono text-slate-800">
                      {verifyResult.canonical_payload.apaar_masked}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Institution:</span>
                    <span className="text-slate-800">
                      {verifyResult.canonical_payload.institution_name}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Programme:</span>
                    <span className="font-semibold text-govTeal-700">
                      {verifyResult.canonical_payload.programme_name} ({verifyResult.canonical_payload.programme_code})
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Enrolment Status:</span>
                    <span className="font-bold text-emerald-600">
                      {verifyResult.canonical_payload.enrolment_status}
                    </span>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
