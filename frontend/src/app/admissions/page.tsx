"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import {
  GraduationCap,
  Search,
  Filter,
  Plus,
  QrCode,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  Download,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

export default function AdmissionsPage() {
  const { user } = useAuth();
  const [admissions, setAdmissions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [showManualModal, setShowManualModal] = useState(false);

  // Manual form state
  const [manualForm, setManualForm] = useState({
    apaar_id: "400192831999",
    student_name: "Gaurav Malhotra",
    dob: "2005-08-15",
    gender: "MALE",
    programme_code: "BTECH-CSE",
    academic_year: "2026-27",
    enrollment_no: "DTU/2026/CSE/220",
    category: "OPEN",
    admission_quota: "STATE_GOVT",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const loadAdmissions = async () => {
    try {
      setLoading(true);
      let query = "/admissions?limit=100";
      if (statusFilter) query += `&status=${statusFilter}`;
      if (categoryFilter) query += `&category=${categoryFilter}`;
      if (searchTerm) query += `&search=${encodeURIComponent(searchTerm)}`;
      const res = await apiRequest(query);
      setAdmissions(res);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAdmissions();
  }, [user, statusFilter, categoryFilter]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadAdmissions();
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(null);
    try {
      await apiRequest("/admissions/manual", {
        method: "POST",
        body: JSON.stringify(manualForm),
      });
      setShowManualModal(false);
      await loadAdmissions();
    } catch (err: any) {
      setFormError(err.message || "Failed to submit admission.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Title */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Central Student Admission Repository
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Verified technical education enrolments anchored by 12-digit APAAR academic identifiers.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setShowManualModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-govTeal-600 hover:bg-govTeal-700 text-white text-xs font-semibold rounded-lg shadow-xs transition"
          >
            <Plus className="w-4 h-4" />
            <span>Manual Student Entry</span>
          </button>
          <a
            href="http://localhost:8000/api/v1/reports/admissions.csv"
            download
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-xs transition"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </a>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200/90 shadow-xs flex flex-col md:flex-row gap-3 items-center justify-between">
        <form onSubmit={handleSearch} className="flex-1 w-full flex gap-2">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search by student name, enrollment no, or masked APAAR..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-govTeal-500"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-govNavy-900 hover:bg-govNavy-800 text-white rounded-lg text-xs font-semibold transition"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg p-2 bg-white"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">ACTIVE</option>
            <option value="UNDER_REVIEW">UNDER_REVIEW</option>
            <option value="TRANSFERRED">TRANSFERRED</option>
            <option value="CANCELLED">CANCELLED</option>
          </select>

          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg p-2 bg-white"
          >
            <option value="">All Categories</option>
            <option value="OPEN">OPEN</option>
            <option value="OBC_NCL">OBC_NCL</option>
            <option value="SC">SC</option>
            <option value="ST">ST</option>
            <option value="EWS">EWS</option>
          </select>
        </div>
      </div>

      {/* Admissions Table */}
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs overflow-hidden">
        <table className="w-full text-xs text-left">
          <thead className="bg-slate-100 text-slate-600 font-semibold uppercase text-[10px]">
            <tr>
              <th className="px-4 py-3">Student Name</th>
              <th className="px-4 py-3">Masked APAAR</th>
              <th className="px-4 py-3">Institution</th>
              <th className="px-4 py-3">Programme</th>
              <th className="px-4 py-3">Enrollment No</th>
              <th className="px-4 py-3">Category / Quota</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Verification</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {admissions.map((adm) => (
              <tr key={adm.id} className="hover:bg-slate-50 transition">
                <td className="px-4 py-3 font-semibold text-slate-900">{adm.student?.full_name}</td>
                <td className="px-4 py-3 font-mono font-bold text-slate-700">
                  {adm.student?.apaar_masked}
                </td>
                <td className="px-4 py-3 text-slate-700">{adm.institution_name}</td>
                <td className="px-4 py-3 font-medium text-govTeal-700">
                  {adm.programme_code}
                </td>
                <td className="px-4 py-3 font-mono text-slate-600">{adm.enrollment_no}</td>
                <td className="px-4 py-3 text-slate-600">
                  {adm.category} ({adm.admission_quota})
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      adm.status === "ACTIVE"
                        ? "bg-emerald-100 text-emerald-800"
                        : adm.status === "UNDER_REVIEW"
                        ? "bg-amber-100 text-amber-800"
                        : "bg-slate-200 text-slate-700"
                    }`}
                  >
                    {adm.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="flex items-center gap-1 text-[11px] text-emerald-700 font-medium">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>{adm.student?.verification_status}</span>
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    href={`/verification`}
                    className="p-1.5 hover:bg-govTeal-50 text-govTeal-700 rounded transition inline-flex items-center gap-1 font-semibold text-[11px]"
                  >
                    <QrCode className="w-3.5 h-3.5" />
                    <span>Issue Receipt</span>
                  </Link>
                </td>
              </tr>
            ))}
            {admissions.length === 0 && !loading && (
              <tr>
                <td colSpan={9} className="px-4 py-8 text-center text-slate-400">
                  No admission records matched the active filters.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Manual Entry Modal */}
      {showManualModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-xl space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900">Add Individual Student Admission</h2>
              <button onClick={() => setShowManualModal(false)} className="text-slate-400 hover:text-slate-600">
                &times;
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-red-50 text-red-700 rounded-lg text-xs">{formError}</div>
            )}

            <form onSubmit={handleManualSubmit} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-700 font-medium mb-1">12-Digit APAAR ID</label>
                <input
                  type="text"
                  required
                  value={manualForm.apaar_id}
                  onChange={(e) => setManualForm({ ...manualForm, apaar_id: e.target.value })}
                  className="w-full border border-slate-300 rounded-lg p-2 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Student Full Name</label>
                  <input
                    type="text"
                    required
                    value={manualForm.student_name}
                    onChange={(e) => setManualForm({ ...manualForm, student_name: e.target.value })}
                    className="w-full border border-slate-300 rounded-lg p-2"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Date of Birth</label>
                  <input
                    type="date"
                    required
                    value={manualForm.dob}
                    onChange={(e) => setManualForm({ ...manualForm, dob: e.target.value })}
                    className="w-full border border-slate-300 rounded-lg p-2"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Programme Code</label>
                  <input
                    type="text"
                    required
                    value={manualForm.programme_code}
                    onChange={(e) => setManualForm({ ...manualForm, programme_code: e.target.value })}
                    className="w-full border border-slate-300 rounded-lg p-2 font-mono uppercase"
                  />
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Enrollment Number</label>
                  <input
                    type="text"
                    required
                    value={manualForm.enrollment_no}
                    onChange={(e) => setManualForm({ ...manualForm, enrollment_no: e.target.value })}
                    className="w-full border border-slate-300 rounded-lg p-2 font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Category</label>
                  <select
                    value={manualForm.category}
                    onChange={(e) => setManualForm({ ...manualForm, category: e.target.value })}
                    className="w-full border border-slate-300 rounded-lg p-2 bg-white"
                  >
                    <option value="OPEN">OPEN</option>
                    <option value="OBC_NCL">OBC_NCL</option>
                    <option value="SC">SC</option>
                    <option value="ST">ST</option>
                    <option value="EWS">EWS</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Quota</label>
                  <select
                    value={manualForm.admission_quota}
                    onChange={(e) => setManualForm({ ...manualForm, admission_quota: e.target.value })}
                    className="w-full border border-slate-300 rounded-lg p-2 bg-white"
                  >
                    <option value="STATE_GOVT">STATE_GOVT</option>
                    <option value="AICTE_TFW">AICTE_TFW (Fee Waiver)</option>
                    <option value="MANAGEMENT">MANAGEMENT</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowManualModal(false)}
                  className="px-4 py-2 border border-slate-300 rounded-lg text-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-govTeal-600 hover:bg-govTeal-700 text-white rounded-lg font-semibold"
                >
                  {isSubmitting ? "Submitting..." : "Save Student Record"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
