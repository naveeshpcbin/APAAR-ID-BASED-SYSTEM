"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";

export default function Home() {
  const router = useRouter();
  const { user, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading) {
      if (!user) {
        router.replace("/login");
      } else if (user.role === "AICTE_ADMIN" || user.role === "REGIONAL_OFFICER") {
        router.replace("/dashboard");
      } else {
        router.replace("/uploads");
      }
    }
  }, [user, isLoading, router]);

  return (
    <div className="flex h-screen items-center justify-center bg-slate-900">
      <div className="text-center space-y-3">
        <div className="inline-block w-8 h-8 border-3 border-teal-500 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-xs font-medium text-slate-400 tracking-wide uppercase">
          Routing to authorized workspace...
        </p>
      </div>
    </div>
  );
}
