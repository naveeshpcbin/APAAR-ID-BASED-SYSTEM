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
  Award,
} from "lucide-react";
import { apiRequest, downloadFileWithAuth } from "@/lib/api";
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
    nationality_type: "DOMESTIC",
    is_supernumerary: false,
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
      {/* Title & Scope */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900 tracking-tight">
              {user?.role === "INSTITUTION_NODAL"
                ? `${user?.institutionName || "College"} Student Admissions Roll`
                : "AICTE Central Student Admission Repository"}
            </h1>
            <span
              className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                user?.role === "INSTITUTION_NODAL"
                  ? "bg-emerald-50 text-emerald-800 border-emerald-300"
                  : "bg-blue-50 text-blue-800 border-blue-300"
              }`}
            >
              {user?.role === "INSTITUTION_NODAL"
                ? `INSTITUTION SCOPE: #${user?.institutionId || "COLLEGE"}`
                : "CENTRAL REGULATOR SCOPE"}
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            {user?.role === "INSTITUTION_NODAL"
              ? "Your institution's technical education enrolments anchored by 12-digit APAAR academic identifiers."
              : "National technical education enrolments anchored by 12-digit APAAR academic identifiers across all institutions."}
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => setShowManualModal(true)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-govTeal-600 hover:bg-govTeal-700 text-white text-xs font-semibold rounded-lg shadow-xs transition"
          >
            <Plus className="w-4 h-4" />
            <span>Manual Student Entry</span>
          </button>
          <button
            onClick={async () => {
              try {
                const filename = `admissions_${user?.institutionName ? user.institutionName.replace(/\s+/g, "_") : "export"}.csv`;
                await downloadFileWithAuth("/reports/admissions.csv", filename);
              } catch (err: any) {
                alert(err.message || "Failed to download export.");
              }
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-semibold rounded-lg shadow-xs transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export CSV</span>
          </button>
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
            className="px-4 py-2 bg-govNavy-900 hover:bg-govNavy-800 text-white rounded-lg text-xs font-semibold transition shrink-0"
          >
            Search
          </button>
        </form>

        <div className="flex flex-wrap sm:flex-nowrap items-center gap-2 w-full md:w-auto">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-300 rounded-lg p-2 bg-white flex-1 sm:flex-none"
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
            className="text-xs border border-slate-300 rounded-lg p-2 bg-white flex-1 sm:flex-none"
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
      <div className="bg-white rounded-xl border border-slate-200/90 shadow-xs overflow-x-auto">
        <table className="w-full min-w-[850px] text-xs text-left">
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
                  <div className="font-medium text-slate-900">{adm.category} ({adm.admission_quota})</div>
                  <div className="flex items-center gap-1 mt-1 flex-wrap">
                    {adm.is_supernumerary ? (
                      <span className="px-1.5 py-0.5 bg-purple-100 text-purple-800 rounded text-[9px] font-bold uppercase">
                        Supernumerary
                      </span>
                    ) : null}
                    {adm.nationality_type && adm.nationality_type !== "DOMESTIC" ? (
                      <span className="px-1.5 py-0.5 bg-indigo-100 text-indigo-800 rounded text-[9px] font-bold uppercase">
                        {adm.nationality_type}
                      </span>
                    ) : null}
                  </div>
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
                  <div className="flex items-center justify-end gap-1.5">
                    <Link
                      href={`/admissions/certificate/${adm.id}`}
                      className="p-1.5 hover:bg-slate-100 text-slate-700 rounded transition inline-flex items-center gap-1 font-semibold text-[11px]"
                      title="View Academic Enrolment Certificate (SIH-R10)"
                    >
                      <Award className="w-3.5 h-3.5 text-govTeal-700" />
                      <span>Certificate</span>
                    </Link>
                    <Link
                      href={`/verification`}
                      className="p-1.5 hover:bg-govTeal-50 text-govTeal-700 rounded transition inline-flex items-center gap-1 font-semibold text-[11px]"
                    >
                      <QrCode className="w-3.5 h-3.5" />
                      <span>Receipt</span>
                    </Link>
                  </div>
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
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-3 sm:p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-4 sm:p-6 shadow-xl space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h2 className="text-sm font-bold text-slate-900">Add Individual Student Admission</h2>
              <button onClick={() => setShowManualModal(false)} className="text-slate-400 hover:text-slate-600 text-base">
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

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Nationality / Status (Req. 2)</label>
                  <select
                    value={manualForm.nationality_type}
                    onChange={(e) => setManualForm({ ...manualForm, nationality_type: e.target.value })}
                    className="w-full border border-slate-300 rounded-lg p-2 bg-white font-medium"
                  >
                    <option value="DOMESTIC">Indian / Domestic (General)</option>
                    <option value="NRI">NRI (Non-Resident Indian)</option>
                    <option value="OCI">OCI (Overseas Citizen of India)</option>
                    <option value="FOREIGN_NATIONAL">FN (Foreign National Status)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-700 font-medium mb-1">Supernumerary Seat</label>
                  <select
                    value={manualForm.is_supernumerary ? "true" : "false"}
                    onChange={(e) => setManualForm({ ...manualForm, is_supernumerary: e.target.value === "true" })}
                    className="w-full border border-slate-300 rounded-lg p-2 bg-white font-medium"
                  >
                    <option value="false">No (Sanctioned Intake)</option>
                    <option value="true">Yes (Supernumerary Intake)</option>
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
