"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { apiRequest } from "./api";

export interface UserContextType {
  email: string;
  role: string;
  fullName: string;
  institutionId?: number | null;
  institutionName?: string | null;
  aicteId?: string | null;
  token: string | null;
}

interface AuthContextValue {
  user: UserContextType | null;
  isLoading: boolean;
  login: (email: string, pass: string) => Promise<UserContextType>;
  logout: (redirectUrl?: string) => void;
  switchDemoUser: (persona: "admin" | "dtu" | "coep" | "verifier") => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export const DEMO_CREDENTIALS = {
  admin: {
    email: "aicte.admin@pramaan.gov.in",
    pass: "Admin@12345",
    label: "AICTE Central Admin",
    subtitle: "Bureau of Approval",
  },
  dtu: {
    email: "nodal.dtu@dtu.ac.in",
    pass: "College@12345",
    label: "DTU Delhi (Nodal)",
    subtitle: "State Govt Aided",
  },
  coep: {
    email: "nodal.coep@coep.ac.in",
    pass: "College@12345",
    label: "COEP Pune (Nodal)",
    subtitle: "State Govt Autonomous",
  },
  verifier: {
    email: "verifier.corp@tcs.com",
    pass: "Verify@12345",
    label: "Authorized Verifier",
    subtitle: "Corporate / University",
  },
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserContextType | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check saved session
    const savedUser = localStorage.getItem("pramaan_user");
    const savedToken = localStorage.getItem("pramaan_token");
    if (savedUser && savedToken) {
      try {
        const parsed = JSON.parse(savedUser);
        setUser({ ...parsed, token: savedToken });
      } catch {
        localStorage.removeItem("pramaan_user");
        localStorage.removeItem("pramaan_token");
        setUser(null);
      }
    } else {
      setUser(null);
    }
    setIsLoading(false);
  }, []);

  const login = async (email: string, pass: string) => {
    setIsLoading(true);
    try {
      const res = await apiRequest("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password: pass }),
      });
      const userData: UserContextType = {
        email: res.email,
        role: res.role,
        fullName: res.full_name,
        institutionId: res.institution_id,
        institutionName: res.institution_name,
        aicteId: res.aicte_id,
        token: res.access_token,
      };
      localStorage.setItem("pramaan_token", res.access_token);
      localStorage.setItem("pramaan_user", JSON.stringify(userData));
      setUser(userData);
      return userData;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = (redirectUrl: string = "/login") => {
    localStorage.removeItem("pramaan_token");
    localStorage.removeItem("pramaan_user");
    setUser(null);
    if (typeof window !== "undefined") {
      window.location.href = redirectUrl;
    }
  };

  const switchDemoUser = async (persona: "admin" | "dtu" | "coep" | "verifier") => {
    const cred = DEMO_CREDENTIALS[persona];
    await login(cred.email, cred.pass);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, login, logout, switchDemoUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
