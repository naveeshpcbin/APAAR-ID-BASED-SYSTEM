"use client";

import React, { useState } from "react";
import { Settings, ShieldCheck, Key, Database, Server, CheckCircle2, Lock } from "lucide-react";

export default function SettingsPage() {
  const [mockLatency, setMockLatency] = useState(15);
  const [strictMode, setStrictMode] = useState(true);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Platform Settings & Trust Architecture Configuration
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Cryptographic key management, identity provider adapter status, and regulatory parameters.
          </p>
        </div>
        <span className="text-xs font-mono font-semibold px-2.5 py-1 rounded bg-slate-100 text-slate-700 border border-slate-200">
          SIH26263 Prototype Build v1.0.0
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Card 1: Cryptographic Trust Root */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-govTeal-600" />
            <h2 className="text-sm font-bold text-slate-900">
              Ed25519 Authority Key Registry
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Public verification key utilized for issuing and validating signed non-PII verification receipts and QR codes.
          </p>

          <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1 font-mono text-xs">
            <div className="text-[10px] text-slate-400 font-bold uppercase">
              Asymmetric Curve25519 Public Key (Base64)
            </div>
            <div className="text-slate-900 break-all font-semibold">
              Wc4V9m1V5kM+2K2Q8fP/O1Kk7J/QpM8k1+P1W7M3k2Y=
            </div>
          </div>

          <div className="space-y-2 text-xs text-slate-600 pt-2 border-t border-slate-100">
            <div className="flex justify-between">
              <span>Cryptographic Primitive:</span>
              <span className="font-semibold text-slate-900">Ed25519 (RFC 8032)</span>
            </div>
            <div className="flex justify-between">
              <span>Token Format:</span>
              <span className="font-semibold text-slate-900">Opaque UUID4 (Zero PII in URL)</span>
            </div>
            <div className="flex justify-between">
              <span>Audit Chain Integrity:</span>
              <span className="font-semibold text-emerald-600">SHA-256 Tamper-Evident</span>
            </div>
          </div>
        </div>

        {/* Card 2: Identity Provider Adapter */}
        <div className="bg-white p-6 rounded-xl border border-slate-200/90 shadow-xs space-y-4">
          <div className="flex items-center gap-2">
            <Server className="w-5 h-5 text-govTeal-600" />
            <h2 className="text-sm font-bold text-slate-900">
              APAAR Identity Adapter (Mock Gateway)
            </h2>
          </div>
          <p className="text-xs text-slate-500">
            Deterministic simulation profile for testing regulatory error states without leaking real student records.
          </p>

          <div className="space-y-3 text-xs">
            <div>
              <label className="block text-slate-700 font-medium mb-1">
                Simulated Gateway Response Latency ({mockLatency} ms)
              </label>
              <input
                type="range"
                min={5}
                max={150}
                value={mockLatency}
                onChange={(e) => setMockLatency(Number(e.target.value))}
                className="w-full accent-govTeal-600"
              />
            </div>

            <div className="p-3 bg-slate-50 rounded-lg border border-slate-200 space-y-1.5 text-[11px] text-slate-600">
              <div className="font-semibold text-slate-800">Deterministic Suffix Test Vectors:</div>
              <div>&bull; Ending 0000 - 8999: Passed (100% Verified)</div>
              <div>&bull; Ending 9000 - 9299: Demographic Mismatch</div>
              <div>&bull; Ending 9300 - 9599: Not Found in ABC Registry</div>
              <div>&bull; Ending 9600 - 9799: Upstream Gateway 503 Timeout</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
