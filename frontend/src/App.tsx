import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppShell } from "@/components/shell/AppShell";
import { AuthProvider, ProtectedRoute } from "@/lib/auth";
import Index from "./pages/Index";
import Triage from "./pages/Triage";
import AdminNetwork from "./pages/AdminNetwork";
import NetworkGraph from "./pages/NetworkGraph";
import Indicators from "./pages/Indicators";
import System from "./pages/System";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AuthProvider>
        <BrowserRouter>
          <AppShell>
            <Routes>
              <Route path="/" element={<Index />} />
              <Route path="/login" element={<Login />} />
              <Route path="/triage" element={<Triage />} />
              <Route
                path="/admin/network"
                element={
                  <ProtectedRoute requiredRole="admin">
                    <AdminNetwork />
                  </ProtectedRoute>
                }
              />
              <Route path="/network/graph" element={<NetworkGraph />} />
              <Route path="/indicators" element={<Indicators />} />
              <Route path="/system" element={<System />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </AppShell>
        </BrowserRouter>
      </AuthProvider>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
