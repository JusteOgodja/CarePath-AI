import { IndicatorsDashboard } from "@/components/indicators/IndicatorsDashboard";
import { BarChart3 } from "lucide-react";
import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";

export default function IndicatorsPage() {
  const { language } = useI18n();
  const isFr = language === "fr";

  return (
    <div className="space-y-8 pb-20 lg:pb-0">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="page-header">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl shadow-card" style={{ background: "var(--gradient-primary)" }}>
            <BarChart3 className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1>{isFr ? "Indicateurs de santé" : "Health Indicators"}</h1>
            <p>{isFr ? "Explorez les indicateurs par pays et par code" : "Explore indicators by country and code"}</p>
          </div>
        </div>
      </motion.div>
      <IndicatorsDashboard />
    </div>
  );
}
