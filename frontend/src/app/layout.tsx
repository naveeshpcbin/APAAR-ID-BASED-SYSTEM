import type { Metadata } from "next";
import "./globals.css";
import { AppShell } from "@/components/layout/AppShell";

export const metadata: Metadata = {
  title: "PRAMAAN-AICTE | Regulatory Monitoring & APAAR Verification Platform",
  description:
    "Platform for Real-time APAAR-linked Monitoring, Auditing, and Academic Network. SIH 2026 Problem Statement SIH26263.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased text-slate-900 bg-slate-50">
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
