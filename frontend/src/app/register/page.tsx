"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Building2,
  ShieldCheck,
  Lock,
  Mail,
  User,
  GraduationCap,
  Award,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  MapPin,
  Compass,
} from "lucide-react";
import { apiRequest } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface InstitutionPreset {
  label: string;
  subtitle: string;
  aicte_id: string;
  name: string;
  state: string;
  district: string;
  institution_type: string;
  nodal_name: string;
  nodal_email: string;
  programme_code: string;
  programme_name: string;
  approved_intake: number;
  tfw_quota: number;
}

const PRESET_INSTITUTIONS: InstitutionPreset[] = [
  {
    label: "VIT Vellore",
    subtitle: "Deemed University | Tamil Nadu",
    aicte_id: "1-1099882",
    name: "Vellore Institute of Technology (VIT)",
    state: "Tamil Nadu",
    district: "Vellore",
    institution_type: "DEEMED_UNIVERSITY",
    nodal_name: "Dr. K. Ramanathan",
    nodal_email: "nodal.vit@vit.ac.in",
    programme_code: "BTECH-CSE",
    programme_name: "B.Tech in Computer Science & Engineering",
    approved_intake: 240,
    tfw_quota: 12,
  },
  {
    label: "BITS Pilani",
    subtitle: "Institute of Eminence | Rajasthan",
    aicte_id: "1-1099883",
    name: "Birla Institute of Technology and Science (BITS Pilani)",
    state: "Rajasthan",
    district: "Jhunjhunu",
    institution_type: "DEEMED_UNIVERSITY",
    nodal_name: "Prof. Sudhirkumar Barai",
    nodal_email: "nodal.bits@pilani.bits-pilani.ac.in",
    programme_code: "BTECH-CSE",
    programme_name: "B.E. in Computer Science",
    approved_intake: 180,
    tfw_quota: 9,
  },
  {
    label: "NIT Trichy",
    subtitle: "National Institute of Tech | Tamil Nadu",
    aicte_id: "1-1099884",
    name: "National Institute of Technology Tiruchirappalli (NIT-T)",
    state: "Tamil Nadu",
    district: "Tiruchirappalli",
    institution_type: "CENTRAL_UNIVERSITY",
    nodal_name: "Dr. G. Aghila",
    nodal_email: "nodal.nitt@nitt.edu",
    programme_code: "BTECH-ECE",
    programme_name: "B.Tech in Electronics & Communication",
    approved_intake: 120,
    tfw_quota: 6,
  },
  {
    label: "RVCE Bengaluru",
    subtitle: "Govt Autonomous | Karnataka",
    aicte_id: "1-1099885",
    name: "RV College of Engineering (RVCE)",
    state: "Karnataka",
    district: "Bengaluru Urban",
    institution_type: "GOVT_AUTONOMOUS",
    nodal_name: "Dr. K.N. Subramanya",
    nodal_email: "nodal.rvce@rvce.edu.in",
    programme_code: "BTECH-CSE",
    programme_name: "B.E. in Computer Science & Engineering",
    approved_intake: 180,
    tfw_quota: 9,
  },
];

export default function RegisterInstitutionPage() {
  const router = useRouter();
  const { login } = useAuth();

  // Form State
  const [formData, setFormData] = useState({
    aicte_id: "",
    name: "",
    state: "",
    district: "",
    institution_type: "PRIVATE_UNAIDED",
    contact_email: "",
    nodal_name: "",
    nodal_email: "",
    password: "College@12345",
    programme_code: "BTECH-CSE",
    programme_name: "B.Tech in Computer Science & Engineering",
    degree_level: "UG",
    approved_intake: 120,
    tfw_quota: 6,
    academic_year: "2026-27",
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]:
        name === "approved_intake" || name === "tfw_quota"
          ? parseInt(value, 10) || 0
          : value,
    }));
    setError(null);
  };

  const handleApplyPreset = (preset: InstitutionPreset) => {
    setFormData((prev) => ({
      ...prev,
      aicte_id: preset.aicte_id,
      name: preset.name,
      state: preset.state,
      district: preset.district,
      institution_type: preset.institution_type,
      nodal_name: preset.nodal_name,
      nodal_email: preset.nodal_email,
      contact_email: preset.nodal_email,
      programme_code: preset.programme_code,
      programme_name: preset.programme_name,
      approved_intake: preset.approved_intake,
      tfw_quota: preset.tfw_quota,
    }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (!formData.aicte_id.trim()) {
      setError("Please provide a valid AICTE Permanent Institute ID.");
      return;
    }
    if (!formData.name.trim()) {
      setError("Please provide the official institution name.");
      return;
    }
    if (!formData.nodal_email.trim() || !formData.password) {
      setError("Please provide nodal officer email and password.");
      return;
    }

    setIsSubmitting(true);
    try {
      const res = await apiRequest("/auth/register-institution", {
        method: "POST",
        body: JSON.stringify(formData),
      });

      // Save session credentials
      localStorage.setItem("pramaan_token", res.access_token);
      localStorage.setItem(
        "pramaan_user",
        JSON.stringify({
          email: res.email,
          role: res.role,
          fullName: res.full_name,
          institutionId: res.institution_id,
          institutionName: res.institution_name,
          aicteId: res.aicte_id,
          token: res.access_token,
        })
      );

      // Force page navigation into the new college workspace
      window.location.href = "/uploads";
    } catch (err: any) {
      setError(err.message || "Failed to register institution.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-center py-8 sm:py-12 px-4 sm:px-6 lg:px-8 relative select-none">
      {/* Background Decorative Grid */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-40 pointer-events-none" />

      <div className="w-full max-w-3xl mx-auto relative z-10">
        {/* Navigation Back Link */}
        <Link
          href="/login/college"
          className="inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-emerald-400 mb-4 transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to College Sign In</span>
        </Link>

        {/* Header Badge & Title */}
        <div className="text-center mb-8">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-emerald-500 via-teal-600 to-slate-900 text-white flex items-center justify-center mx-auto mb-3 shadow-xl shadow-emerald-950/60 border border-emerald-400/40">
            <Building2 className="w-7 h-7" />
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">
            Register New AICTE-Approved Institution
          </h1>
          <p className="mt-2 text-xs text-slate-400 max-w-lg mx-auto">
            Onboard any recognized technical university, autonomous engineering college, or polytechnic onto the National PRAMAAN-AICTE Student Reconciliation Platform.
          </p>

          <div className="mt-3 inline-flex items-center gap-2 px-3 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>AICTE Approval Verification &amp; Cryptographic Tenant Creation</span>
          </div>
        </div>

        {/* Evaluator Quick-Fill Presets */}
        <div className="mb-6 p-4 bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl">
          <div className="flex items-center justify-between mb-2.5">
            <div className="flex items-center gap-2 text-xs font-bold text-slate-300">
              <Sparkles className="w-4 h-4 text-emerald-400" />
              <span>Evaluator Demo Presets — Register Any Top Indian Technical College</span>
            </div>
            <span className="text-[10px] text-slate-500 font-mono">1-Click Fill</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
            {PRESET_INSTITUTIONS.map((preset) => (
              <button
                key={preset.aicte_id}
                type="button"
                onClick={() => handleApplyPreset(preset)}
                className="p-2.5 rounded-xl bg-slate-950/80 hover:bg-emerald-950/40 border border-slate-800 hover:border-emerald-600 text-left transition group cursor-pointer"
              >
                <div className="text-xs font-bold text-slate-200 group-hover:text-emerald-300 truncate">
                  {preset.label}
                </div>
                <div className="text-[10px] text-slate-500 truncate mt-0.5">
                  {preset.subtitle}
                </div>
                <div className="text-[9px] font-mono text-emerald-500 mt-1">
                  ID: {preset.aicte_id}
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Registration Form Card */}
        <div className="bg-white text-slate-900 p-4 sm:p-8 rounded-2xl sm:rounded-3xl shadow-2xl border border-slate-200 space-y-6">
          {error && (
            <div className="p-3.5 bg-red-50 border border-red-200 text-red-700 rounded-xl text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
              <div className="leading-snug">{error}</div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6 text-xs">
            {/* Step 1: Institutional Identity */}
            <div className="space-y-3 pb-5 border-b border-slate-200">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-800 uppercase tracking-wider">
                <Compass className="w-4 h-4 text-emerald-600" />
                <span>1. AICTE Approval &amp; Institution Identification</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    AICTE Permanent Institute ID *
                  </label>
                  <input
                    type="text"
                    name="aicte_id"
                    required
                    placeholder="e.g. 1-1099882"
                    value={formData.aicte_id}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 font-mono text-xs"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Permanent ID issued in AICTE Approval Letter
                  </span>
                </div>

                <div className="sm:col-span-2">
                  <label className="block font-semibold text-slate-700 mb-1">
                    Full Legal Institution Name *
                  </label>
                  <input
                    type="text"
                    name="name"
                    required
                    placeholder="e.g. Vellore Institute of Technology"
                    value={formData.name}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs font-semibold"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    State / UT *
                  </label>
                  <input
                    type="text"
                    name="state"
                    required
                    placeholder="e.g. Tamil Nadu"
                    value={formData.state}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    District *
                  </label>
                  <input
                    type="text"
                    name="district"
                    required
                    placeholder="e.g. Vellore"
                    value={formData.district}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Institution Category / Type *
                  </label>
                  <select
                    name="institution_type"
                    value={formData.institution_type}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs bg-white"
                  >
                    <option value="PRIVATE_UNAIDED">Private Unaided</option>
                    <option value="STATE_GOVT_AIDED">State Govt Aided</option>
                    <option value="GOVT_AUTONOMOUS">Govt Autonomous</option>
                    <option value="CENTRAL_UNIVERSITY">Central University / Institute</option>
                    <option value="DEEMED_UNIVERSITY">Deemed to be University</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Step 2: Nodal Officer Account */}
            <div className="space-y-3 pb-5 border-b border-slate-200">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-800 uppercase tracking-wider">
                <User className="w-4 h-4 text-emerald-600" />
                <span>2. Authorized Institutional Nodal Officer Profile</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Nodal Officer Name *
                  </label>
                  <input
                    type="text"
                    name="nodal_name"
                    required
                    placeholder="e.g. Dr. K. Ramanathan"
                    value={formData.nodal_name}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Official Institutional Email *
                  </label>
                  <input
                    type="email"
                    name="nodal_email"
                    required
                    placeholder="e.g. nodal@vit.ac.in"
                    value={formData.nodal_email}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Password *
                  </label>
                  <input
                    type="password"
                    name="password"
                    required
                    value={formData.password}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Step 3: Primary Approved Programme & Sanctioned Capacity */}
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-800 uppercase tracking-wider">
                <GraduationCap className="w-4 h-4 text-emerald-600" />
                <span>3. Primary Sanctioned Academic Programme (AICTE Approval)</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Programme Code *
                  </label>
                  <input
                    type="text"
                    name="programme_code"
                    required
                    placeholder="e.g. BTECH-CSE"
                    value={formData.programme_code}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs font-mono uppercase"
                  />
                </div>

                <div className="sm:col-span-2">
                  <label className="block font-semibold text-slate-700 mb-1">
                    Programme Name *
                  </label>
                  <input
                    type="text"
                    name="programme_name"
                    required
                    placeholder="e.g. B.Tech in Computer Science & Engineering"
                    value={formData.programme_name}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Sanctioned Intake Capacity *
                  </label>
                  <input
                    type="number"
                    name="approved_intake"
                    required
                    min={1}
                    max={1200}
                    value={formData.approved_intake}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs font-semibold"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Seats approved by AICTE Council
                  </span>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Supernumerary TFW Quota
                  </label>
                  <input
                    type="number"
                    name="tfw_quota"
                    min={0}
                    value={formData.tfw_quota}
                    onChange={handleChange}
                    className="w-full p-2.5 border border-slate-300 rounded-xl focus:ring-2 focus:ring-emerald-500 text-xs"
                  />
                  <span className="text-[10px] text-slate-400 mt-0.5 block">
                    Tuition Fee Waiver supernumerary
                  </span>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    Academic Session
                  </label>
                  <input
                    type="text"
                    name="academic_year"
                    value={formData.academic_year}
                    readOnly
                    className="w-full p-2.5 border border-slate-200 rounded-xl bg-slate-100 text-slate-600 text-xs font-mono"
                  />
                </div>
              </div>
            </div>

            {/* Submit Action */}
            <div className="pt-4 border-t border-slate-200">
              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full py-3 bg-gradient-to-r from-emerald-600 to-teal-700 hover:from-emerald-500 hover:to-teal-600 text-white rounded-xl font-bold text-xs shadow-lg shadow-emerald-950/40 flex items-center justify-center gap-2 transition focus:outline-none focus:ring-2 focus:ring-emerald-500 cursor-pointer disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    <span>Verifying AICTE Permanent ID &amp; Creating Tenant...</span>
                  </>
                ) : (
                  <>
                    <span>Complete Institutional Registration &amp; Access Workspace</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Security & Regulatory Notice */}
        <div className="mt-6 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>
            Strict Multi-Tenant Partitioning: Upon registration, your institution operates in a completely isolated sovereign workspace.
          </span>
        </div>
      </div>
    </div>
  );
}
