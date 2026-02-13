import React from "react";
import { Navigate, useLocation } from "react-router-dom";

export type AuthRole = "admin" | "viewer";

export interface AuthSession {
  access_token: string;
  token_type: "bearer";
  role: AuthRole;
  username: string;
}

const SESSION_KEY = "carepath_auth_session";
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

interface AuthContextValue {
  session: AuthSession | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<AuthSession>;
  logout: () => void;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

function readSession(): AuthSession | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as AuthSession;
  } catch {
    window.localStorage.removeItem(SESSION_KEY);
    return null;
  }
}

function writeSession(session: AuthSession | null): void {
  if (typeof window === "undefined") return;
  if (!session) {
    window.localStorage.removeItem(SESSION_KEY);
    return;
  }
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function getAuthToken(): string | null {
  return readSession()?.access_token ?? null;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = React.useState<AuthSession | null>(() => readSession());

  const login = React.useCallback(async (username: string, password: string) => {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      throw new Error("Identifiants invalides");
    }
    const data = (await response.json()) as AuthSession;
    writeSession(data);
    setSession(data);
    return data;
  }, []);

  const logout = React.useCallback(() => {
    writeSession(null);
    setSession(null);
  }, []);

  const value = React.useMemo<AuthContextValue>(
    () => ({
      session,
      isAuthenticated: Boolean(session?.access_token),
      login,
      logout,
    }),
    [session, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}

export function ProtectedRoute({
  children,
  requiredRole,
}: {
  children: React.ReactNode;
  requiredRole?: AuthRole;
}) {
  const { session, isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  if (requiredRole && session?.role !== requiredRole) {
    return <Navigate to="/system" replace />;
  }

  return <>{children}</>;
}
