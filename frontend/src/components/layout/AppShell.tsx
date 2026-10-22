"use client";

import React from "react";
import { usePathname } from "next/navigation";
import { AuthProvider } from "@/lib/auth-context";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isPublicPage = pathname.startsWith("/verification/receipt/") || pathname === "/login";

  return (
    <AuthProvider>
      {isPublicPage ? (
        <main className="min-h-screen bg-slate-100">{children}</main>
      ) : (
        <div className="flex h-screen w-screen overflow-hidden bg-slate-50 font-sans">
          <Sidebar />
          <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
            <TopBar />
            <main className="flex-1 overflow-y-auto p-6 bg-slate-50">
              {children}
            </main>
          </div>
        </div>
      )}
    </AuthProvider>
  );
}
