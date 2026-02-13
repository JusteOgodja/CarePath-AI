import { HealthCard } from "@/components/system/HealthCard";
import { Badge } from "@/components/ui/badge";
import { Settings, Info } from "lucide-react";
import { motion } from "framer-motion";

export default function SystemPage() {
  return (
    <div className="space-y-8 pb-20 lg:pb-0">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="page-header">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl shadow-card" style={{ background: "var(--gradient-primary)" }}>
            <Settings className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1>Système</h1>
            <p>Statut, configuration et informations</p>
          </div>
        </div>
      </motion.div>

      <HealthCard />

      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.15 }}
        className="premium-card p-6 space-y-5"
      >
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
            <Info className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-[15px]">À propos</h3>
            <p className="text-xs text-muted-foreground">CarePath AI Frontend</p>
          </div>
        </div>

        <div className="space-y-3 text-sm leading-relaxed">
          <p className="text-muted-foreground">
            <strong className="text-foreground">CarePath AI</strong> est un système d'aide à la décision pour le triage et le transfert de patients dans les réseaux de santé.
            Il recommande le meilleur centre de référence en fonction de la spécialité requise, de la sévérité, de la capacité et du temps de trajet.
          </p>
          <div className="flex gap-2 flex-wrap">
            <Badge variant="outline" className="text-2xs">React + Vite</Badge>
            <Badge variant="outline" className="text-2xs">TypeScript</Badge>
            <Badge variant="outline" className="text-2xs">TanStack Query</Badge>
            <Badge variant="outline" className="text-2xs">shadcn/ui</Badge>
            <Badge variant="outline" className="text-2xs">Framer Motion</Badge>
          </div>
          <p className="text-xs text-muted-foreground">Version 1.0.0</p>
        </div>
      </motion.div>
    </div>
  );
}
