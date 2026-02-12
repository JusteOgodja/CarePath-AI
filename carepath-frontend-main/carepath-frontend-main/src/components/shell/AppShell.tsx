import React from "react";
import { Link, useLocation } from "react-router-dom";
import {
  Stethoscope,
  Network,
  BarChart3,
  Settings,
  Menu,
  X,
  Moon,
  Sun,
  Activity,
  ChevronRight,
  Bell,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

const navItems = [
  { label: "Triage", path: "/triage", icon: Stethoscope, description: "Recommandation" },
  { label: "Réseau", path: "/admin/network", icon: Network, description: "Administration" },
  { label: "Indicateurs", path: "/indicators", icon: BarChart3, description: "Données santé" },
  { label: "Système", path: "/system", icon: Settings, description: "Configuration" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);
  const [dark, setDark] = React.useState(() =>
    typeof window !== "undefined" && document.documentElement.classList.contains("dark")
  );

  const toggleDark = () => {
    document.documentElement.classList.toggle("dark");
    setDark(!dark);
  };

  const currentPage = navItems.find((item) => location.pathname.startsWith(item.path));

  return (
    <div className="flex min-h-screen w-full">
      {/* Desktop sidebar — dark themed */}
      <aside className="hidden lg:flex lg:w-[260px] flex-col bg-sidebar border-r border-sidebar-border">
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 h-16">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg" style={{ background: "var(--gradient-primary)" }}>
            <Activity className="h-5 w-5 text-sidebar-primary-foreground" />
          </div>
          <div>
            <span className="text-[15px] font-bold text-sidebar-accent-foreground tracking-tight">CarePath AI</span>
            <p className="text-2xs text-sidebar-foreground">Healthcare Routing</p>
          </div>
        </div>

        <Separator className="bg-sidebar-border" />

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-1">
          <p className="px-3 text-2xs font-semibold uppercase tracking-widest text-sidebar-foreground/50 mb-3">Navigation</p>
          {navItems.map((item) => {
            const active = location.pathname.startsWith(item.path);
            return (
              <Link
                key={item.path}
                to={item.path}
                className={cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                  active
                    ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
                    : "text-sidebar-foreground hover:bg-sidebar-muted hover:text-sidebar-accent-foreground"
                )}
              >
                <div className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-md transition-colors",
                  active ? "bg-primary/20 text-primary" : "bg-sidebar-muted text-sidebar-foreground group-hover:text-sidebar-accent-foreground"
                )}>
                  <item.icon className="h-4 w-4" />
                </div>
                <div className="flex-1 min-w-0">
                  <span className="block text-[13px]">{item.label}</span>
                  <span className={cn("block text-2xs", active ? "text-sidebar-foreground" : "text-sidebar-foreground/50")}>{item.description}</span>
                </div>
                {active && <ChevronRight className="h-3.5 w-3.5 text-primary" />}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="px-4 pb-4">
          <div className="rounded-lg bg-sidebar-muted px-3 py-3">
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-full bg-sidebar-accent flex items-center justify-center">
                <span className="text-2xs font-bold text-sidebar-accent-foreground">D</span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-sidebar-accent-foreground truncate">Mode Démo</p>
                <p className="text-2xs text-sidebar-foreground/50">Aucune authentification</p>
              </div>
            </div>
          </div>
        </div>
      </aside>

      {/* Mobile sidebar overlay */}
      <AnimatePresence>
        {sidebarOpen && (
          <div className="fixed inset-0 z-50 lg:hidden">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-foreground/40 backdrop-blur-sm"
              onClick={() => setSidebarOpen(false)}
            />
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="fixed left-0 top-0 bottom-0 w-[280px] bg-sidebar border-r border-sidebar-border z-50 flex flex-col"
            >
              <div className="flex items-center justify-between px-5 h-16">
                <div className="flex items-center gap-3">
                  <div className="flex h-9 w-9 items-center justify-center rounded-lg" style={{ background: "var(--gradient-primary)" }}>
                    <Activity className="h-5 w-5 text-sidebar-primary-foreground" />
                  </div>
                  <span className="text-[15px] font-bold text-sidebar-accent-foreground">CarePath AI</span>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(false)} className="text-sidebar-foreground hover:bg-sidebar-muted">
                  <X className="h-5 w-5" />
                </Button>
              </div>
              <Separator className="bg-sidebar-border" />
              <nav className="flex-1 px-3 py-4 space-y-1">
                {navItems.map((item) => {
                  const active = location.pathname.startsWith(item.path);
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={cn(
                        "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all",
                        active
                          ? "bg-sidebar-accent text-sidebar-accent-foreground"
                          : "text-sidebar-foreground hover:bg-sidebar-muted hover:text-sidebar-accent-foreground"
                      )}
                    >
                      <item.icon className="h-4 w-4" />
                      {item.label}
                    </Link>
                  );
                })}
              </nav>
            </motion.aside>
          </div>
        )}
      </AnimatePresence>

      {/* Main area */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Topbar */}
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-card/80 backdrop-blur-xl px-4 lg:px-8">
          <Button
            variant="ghost"
            size="icon"
            className="lg:hidden"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="h-5 w-5" />
          </Button>

          {/* Breadcrumb */}
          <div className="hidden sm:flex items-center gap-2 text-sm">
            <span className="text-muted-foreground">CarePath</span>
            {currentPage && (
              <>
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50" />
                <span className="font-medium">{currentPage.label}</span>
              </>
            )}
          </div>

          <div className="flex-1" />

          <Badge className="hidden sm:flex text-2xs font-medium bg-primary/10 text-primary border-primary/20 hover:bg-primary/15">
            <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-primary animate-pulse-soft inline-block" />
            Demo Mode
          </Badge>

          <Button variant="ghost" size="icon" className="relative" aria-label="Notifications">
            <Bell className="h-4 w-4" />
            <span className="absolute top-2.5 right-2.5 h-1.5 w-1.5 rounded-full bg-primary" />
          </Button>

          <Separator orientation="vertical" className="h-6" />

          <Button variant="ghost" size="icon" onClick={toggleDark} aria-label="Basculer le thème">
            {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </Button>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-8 max-w-[1400px]">{children}</main>
      </div>

      {/* Mobile bottom nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-30 flex lg:hidden border-t bg-card/95 backdrop-blur-xl shadow-elevated">
        {navItems.map((item) => {
          const active = location.pathname.startsWith(item.path);
          return (
            <Link
              key={item.path}
              to={item.path}
              className={cn(
                "flex flex-1 flex-col items-center gap-0.5 py-2.5 text-[10px] font-medium transition-colors relative",
                active ? "text-primary" : "text-muted-foreground"
              )}
            >
              {active && (
                <span className="absolute top-0 left-1/2 -translate-x-1/2 h-0.5 w-8 rounded-full bg-primary" />
              )}
              <item.icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
