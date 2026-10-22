"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard");
  }, [router]);

  return (
    <div className="flex h-screen items-center justify-center bg-slate-50">
      <div className="text-center">
        <div className="inline-block w-8 h-8 border-4 border-govTeal-600 border-t-transparent rounded-full animate-spin mb-3"></div>
        <p className="text-sm font-medium text-slate-600">Loading PRAMAAN-AICTE Regulatory Workspace...</p>
      </div>
    </div>
  );
}
