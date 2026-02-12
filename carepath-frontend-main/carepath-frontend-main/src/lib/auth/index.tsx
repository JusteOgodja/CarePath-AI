import React from "react";

// Auth placeholder – ready for future RBAC implementation
export const isDemoMode = true;

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}
