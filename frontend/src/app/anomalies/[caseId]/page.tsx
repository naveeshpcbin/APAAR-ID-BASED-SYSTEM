"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AnomalyCaseRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/anomalies");
  }, [router]);
  return null;
}
