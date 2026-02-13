import React from "react";
import { useQuery } from "@tanstack/react-query";
import { getHealth } from "@/lib/api/endpoints";
import { getApiBaseUrl } from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Activity, RefreshCw, CheckCircle, XCircle, Clock, Globe } from "lucide-react";
import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";

export function HealthCard() {
  const { language } = useI18n();
  const isFr = language === "fr";
  const [latency, setLatency] = React.useState<number | null>(null);

  const { data, isLoading, error, refetch, isFetching } = useQuery({
    queryKey: ["health"],
    queryFn: async () => {
      const start = performance.now();
      const result = await getHealth();
      setLatency(Math.round(performance.now() - start));
      return result;
    },
    refetchInterval: 30000,
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="premium-card p-6 space-y-5"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
            <Activity className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-bold text-[15px]">{isFr ? "Statut du système" : "System status"}</h3>
            <p className="text-xs text-muted-foreground">{isFr ? "Monitoring temps réel" : "Real-time monitoring"}</p>
          </div>
        </div>
        <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching} className="shadow-card">
          <RefreshCw className={`h-3.5 w-3.5 mr-2 ${isFetching ? "animate-spin" : ""}`} />
          {isFr ? "Actualiser" : "Refresh"}
        </Button>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-xl bg-muted/40 border border-border/50 p-4">
          <p className="stat-label mb-2">{isFr ? "Statut" : "Status"}</p>
          {isLoading ? (
            <div className="h-7 w-20 bg-muted rounded-md animate-pulse" />
          ) : error ? (
            <div className="flex items-center gap-2">
              <XCircle className="h-4 w-4 text-destructive" />
              <Badge variant="destructive" className="shadow-none">{isFr ? "Hors ligne" : "Offline"}</Badge>
            </div>
          ) : (
            <div className="flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-success" />
              <Badge className="bg-success/10 text-success border-success/20 hover:bg-success/15 shadow-none">{isFr ? "En ligne" : "Online"}</Badge>
            </div>
          )}
        </div>

        <div className="rounded-xl bg-muted/40 border border-border/50 p-4">
          <p className="stat-label mb-2 flex items-center gap-1.5"><Clock className="h-3 w-3" /> {isFr ? "Latence" : "Latency"}</p>
          {latency != null ? (
            <p className="text-2xl font-extrabold">{latency}<span className="text-sm font-normal text-muted-foreground ml-1">ms</span></p>
          ) : (
            <span className="text-muted-foreground">—</span>
          )}
        </div>

        <div className="rounded-xl bg-muted/40 border border-border/50 p-4">
          <p className="stat-label mb-2 flex items-center gap-1.5"><Globe className="h-3 w-3" /> Endpoint</p>
          <p className="text-xs font-mono break-all text-muted-foreground leading-relaxed">{getApiBaseUrl()}</p>
        </div>
      </div>
    </motion.div>
  );
}
