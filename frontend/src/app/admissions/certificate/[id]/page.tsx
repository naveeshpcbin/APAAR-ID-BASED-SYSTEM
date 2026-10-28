"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Printer,
  ArrowLeft,
  ShieldCheck,
  Award,
  CheckCircle2,
  FileCheck2,
  QrCode,
  Building2,
  Calendar,
  User,
  Hash,
} from "lucide-react";
import { apiRequest } from "@/lib/api";

export default function StudentCertificatePage() {
  const params = useParams();
  const id = params?.id;
  const [admission, setAdmission] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAdmission = async () => {
      try {
        setLoading(true);
        try {
          const direct = await apiRequest(`/admissions/${id}`);
          if (direct && direct.id) {
            setAdmission(direct);
            return;
          }
        } catch {
          // fallback to list search
        }
        const data = await apiRequest(`/admissions?limit=200`);
        const found = data.find((a: any) => String(a.id) === String(id));
        if (found) {
          setAdmission(found);
        } else {
          setError("Admission record not found.");
        }
      } catch (err: any) {
        setError(err.message || "Failed to load admission details.");
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      fetchAdmission();
    }
  }, [id]);

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[500px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-govNavy-700"></div>
      </div>
    );
  }

  if (error || !admission) {
    return (
      <div className="max-w-xl mx-auto p-8 text-center space-y-4">
        <div className="p-4 bg-red-50 text-red-700 rounded-xl text-sm font-medium">
          {error || "Record could not be loaded."}
        </div>
        <Link
          href="/admissions"
          className="inline-flex items-center gap-1.5 text-xs text-govNavy-700 font-semibold hover:underline"
        >
          <ArrowLeft className="w-4 h-4" /> Return to Admissions
        </Link>
      </div>
    );
  }

  const student = admission.student || {};

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Top Toolbar (Hidden during print) */}
      <div className="print:hidden flex items-center justify-between pb-3 border-b border-slate-200">
        <Link
          href="/admissions"
          className="inline-flex items-center gap-1.5 text-xs text-slate-600 hover:text-slate-900 font-medium transition"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Admissions Repository
        </Link>
        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-500">
            SIH-R10 Compliant Academic Verification Record
          </span>
          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-govNavy-800 hover:bg-govNavy-900 text-white rounded-lg text-xs font-semibold shadow-xs transition"
          >
            <Printer className="w-4 h-4" /> Print / Save as PDF
          </button>
        </div>
      </div>

      {/* Synthetic Demonstration Notice Banner (Hidden during print) */}
      <div className="print:hidden bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-900 flex items-center gap-2">
        <span className="font-bold uppercase tracking-wider text-[10px] bg-amber-200 text-amber-900 px-2 py-0.5 rounded">
          Synthetic Record
        </span>
        <span>
          This is an automated demonstration template fulfilling SIH26263 (SIH-R10) to display Student Enrollment ID alongside APAAR ID. It is not an official degree or statutory certificate.
        </span>
      </div>

      {/* Printable Certificate Container */}
      <div className="bg-white border-4 border-double border-slate-300 rounded-2xl p-8 sm:p-12 shadow-md relative overflow-hidden print:border-2 print:shadow-none print:m-0 print:p-8">
        {/* Subtle Watermark */}
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none opacity-[0.03] select-none">
          <span className="text-9xl font-black rotate-[-30deg] tracking-widest text-slate-900">
            PRAMAAN AICTE
          </span>
        </div>

        {/* Certificate Header */}
        <div className="text-center space-y-2 border-b-2 border-slate-200 pb-6 relative z-10">
          <div className="flex items-center justify-center gap-3">
            <div className="w-12 h-12 bg-govNavy-900 text-white rounded-full flex items-center justify-center shadow-xs">
              <Award className="w-7 h-7 text-govTeal-400" />
            </div>
          </div>
          <div className="text-xs font-bold uppercase tracking-widest text-govTeal-700">
            All India Council for Technical Education (AICTE)
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-govNavy-950 tracking-tight font-serif">
            Student Academic Identity & Enrolment Certificate
          </h1>
          <p className="text-xs text-slate-500 max-w-xl mx-auto">
            Issued in accordance with the National Academic Depository (NAD) & APAAR Digital Identity Framework under the National Education Policy (NEP 2020)
          </p>
        </div>

        {/* Main Body */}
        <div className="py-8 space-y-6 relative z-10">
          <p className="text-center text-sm text-slate-700 italic">
            This is to certify that the student record detailed herein is authenticated and registered on the PRAMAAN-AICTE Central Academic Ledger for the academic session:
          </p>

          {/* Key Identification Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-50 border border-slate-200 rounded-xl p-5">
            <div className="space-y-3">
              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                  Student Full Name
                </span>
                <span className="text-base font-bold text-slate-900">
                  {student.full_name || "N/A"}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                    Institutional Student ID
                  </span>
                  <span className="text-xs font-mono font-bold text-govNavy-800">
                    {admission.enrollment_no}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                    APAAR ID (Masked)
                  </span>
                  <span className="text-xs font-mono font-bold text-govTeal-700">
                    {student.apaar_masked}
                  </span>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                    Date of Birth
                  </span>
                  <span className="text-xs font-medium text-slate-700">
                    {student.dob || "N/A"}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                    Gender / Category
                  </span>
                  <span className="text-xs font-medium text-slate-700">
                    {student.gender} • {admission.category}
                  </span>
                </div>
              </div>
            </div>

            <div className="space-y-3 md:border-l md:border-slate-200 md:pl-5">
              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                  Enrolling Institution
                </span>
                <span className="text-xs font-bold text-slate-900 block">
                  {admission.institution_name || "AICTE Approved Institution"}
                </span>
              </div>
              <div>
                <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                  Academic Programme
                </span>
                <span className="text-xs font-bold text-govNavy-800 block">
                  {admission.programme_name || admission.programme_code} ({admission.programme_code})
                </span>
              </div>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                    Academic Year
                  </span>
                  <span className="text-xs font-medium text-slate-700">
                    {admission.academic_year}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] font-bold uppercase text-slate-400 tracking-wider block">
                    Admission Quota
                  </span>
                  <span className="text-xs font-medium text-slate-700">
                    {admission.admission_quota}
                    {admission.is_supernumerary ? " (Supernumerary)" : ""}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Verification Status Badge */}
          <div className="flex flex-col sm:flex-row items-center justify-between p-4 bg-emerald-50 border border-emerald-200 rounded-xl gap-3">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-8 h-8 text-emerald-600 flex-shrink-0" />
              <div>
                <div className="text-xs font-bold text-emerald-950 flex items-center gap-1.5">
                  <span>APAAR Identity Cryptographically Verified</span>
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                </div>
                <div className="text-[11px] text-emerald-800">
                  Authenticated via Mock APAAR Identity Provider • Provider Status: {student.verification_status}
                </div>
              </div>
            </div>
            <div className="text-right">
              <span className="px-2.5 py-1 bg-emerald-200 text-emerald-900 rounded text-[10px] font-bold uppercase">
                Status: {admission.status}
              </span>
            </div>
          </div>
        </div>

        {/* Certificate Footer / Signature Line */}
        <div className="pt-6 border-t border-slate-200 flex flex-col sm:flex-row items-end justify-between gap-6 relative z-10">
          <div className="text-left space-y-1">
            <div className="w-20 h-20 bg-slate-100 border border-slate-200 rounded-lg flex flex-col items-center justify-center p-2">
              <QrCode className="w-12 h-12 text-slate-700" />
              <span className="text-[8px] font-mono text-slate-500 uppercase mt-0.5">Scan to Verify</span>
            </div>
            <span className="text-[9px] text-slate-400 font-mono block">
              Digest: SHA256:{admission.enrollment_no}
            </span>
          </div>

          <div className="text-center sm:text-right space-y-1">
            <div className="w-48 border-b border-slate-400 pb-1 mb-1">
              <span className="text-[11px] font-serif font-bold text-slate-700 italic">
                Digital Verification Officer
              </span>
            </div>
            <span className="text-[10px] font-bold text-slate-900 block">
              PRAMAAN Regulatory Authority
            </span>
            <span className="text-[9px] text-slate-500 block">
              All India Council for Technical Education, New Delhi
            </span>
          </div>
        </div>

        {/* Mandatory SIH Demonstration Disclaimer */}
        <div className="mt-8 pt-4 border-t border-slate-100 text-center">
          <p className="text-[9px] text-slate-400 uppercase tracking-widest font-semibold">
            SYNTHETIC DEMONSTRATION RECORD — NOT AN OFFICIAL DEGREE OR STATUTORY CERTIFICATE
          </p>
        </div>
      </div>
    </div>
  );
}
