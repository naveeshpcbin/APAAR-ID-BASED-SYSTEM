"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ConflictCaseRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/conflicts");
  }, [router]);
  return null;
}
