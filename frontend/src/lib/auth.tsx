"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { api, User, Business } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  token: string | null;
  businesses: Business[];
  currentBusiness: Business | null;
  isLoading: boolean;
  login: (token: string, user: User) => Promise<void>;
  logout: () => void;
  switchBusiness: (business: Business) => void;
  refreshBusinesses: () => Promise<Business[]>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [currentBusiness, setCurrentBusiness] = useState<Business | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    async function loadAuth() {
      const storedToken = localStorage.getItem("cashflow_token");
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      setToken(storedToken);
      try {
        const currentUser = await api.getMe();
        setUser(currentUser);
        const bizList = await api.getMyBusinesses();
        setBusinesses(bizList);

        const storedBizId = localStorage.getItem("cashflow_current_biz_id");
        const found = bizList.find((b) => b.id === storedBizId);
        if (found) {
          setCurrentBusiness(found);
        } else if (bizList.length > 0) {
          setCurrentBusiness(bizList[0]);
          localStorage.setItem("cashflow_current_biz_id", bizList[0].id);
        }
      } catch (err) {
        console.error("Auth initialization failed:", err);
        localStorage.removeItem("cashflow_token");
        setToken(null);
        setUser(null);
      } finally {
        setIsLoading(false);
      }
    }
    loadAuth();
  }, []);

  const login = async (newToken: string, newUser: User) => {
    localStorage.setItem("cashflow_token", newToken);
    setToken(newToken);
    setUser(newUser);
    try {
      const bizList = await api.getMyBusinesses();
      setBusinesses(bizList);
      if (bizList.length > 0) {
        setCurrentBusiness(bizList[0]);
        localStorage.setItem("cashflow_current_biz_id", bizList[0].id);
        router.push("/dashboard");
      } else {
        router.push("/onboarding");
      }
    } catch {
      router.push("/onboarding");
    }
  };

  const logout = () => {
    localStorage.removeItem("cashflow_token");
    localStorage.removeItem("cashflow_current_biz_id");
    setToken(null);
    setUser(null);
    setBusinesses([]);
    setCurrentBusiness(null);
    router.push("/login");
  };

  const switchBusiness = (biz: Business) => {
    setCurrentBusiness(biz);
    localStorage.setItem("cashflow_current_biz_id", biz.id);
  };

  const refreshBusinesses = async (): Promise<Business[]> => {
    try {
      const bizList = await api.getMyBusinesses();
      setBusinesses(bizList);
      if (!currentBusiness && bizList.length > 0) {
        setCurrentBusiness(bizList[0]);
      } else if (currentBusiness) {
        const updated = bizList.find((b) => b.id === currentBusiness.id);
        if (updated) setCurrentBusiness(updated);
      }
      return bizList;
    } catch {
      return [];
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        businesses,
        currentBusiness,
        isLoading,
        login,
        logout,
        switchBusiness,
        refreshBusinesses,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
