import React from "react";
import { motion } from "framer-motion";
import { MapPin, Star, TrendingUp, Copy, Check, Timer } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { RecommandationResponse } from "@/lib/types";
import { PathTimeline } from "./PathTimeline";
import { JsonViewer } from "@/components/common/JsonViewer";
import { useI18n } from "@/lib/i18n";

interface Props {
  result: RecommandationResponse;
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};
const item = {
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0 },
};

export function RecommendationResult({ result }: Props) {
  const { language } = useI18n();
  const isFr = language === "fr";
  const [copied, setCopied] = React.useState(false);
  const [showExplanation, setShowExplanation] = React.useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(JSON.stringify(result, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="space-y-5">
      {/* KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <motion.div variants={item} className="kpi-card">
          <p className="stat-label">{isFr ? "Destination" : "Destination"}</p>
          <p className="text-xl font-bold mt-2">{result.destination_name}</p>
          <p className="text-xs text-muted-foreground font-mono mt-1">{result.destination_centre_id}</p>
        </motion.div>

        <motion.div variants={item} className="kpi-card">
          <p className="stat-label flex items-center gap-1.5"><MapPin className="h-3 w-3" /> {isFr ? "Temps de trajet" : "Travel time"}</p>
          <p className="stat-value mt-2">{result.estimated_travel_minutes}<span className="text-sm font-normal text-muted-foreground ml-1">min</span></p>
        </motion.div>

        <motion.div variants={item} className="kpi-card">
          <p className="stat-label flex items-center gap-1.5"><Timer className="h-3 w-3" /> {isFr ? "Attente estimée" : "Estimated wait"}</p>
          <p className="stat-value mt-2">{result.estimated_wait_minutes}<span className="text-sm font-normal text-muted-foreground ml-1">min</span></p>
        </motion.div>

        <motion.div variants={item} className="kpi-card">
          <p className="stat-label flex items-center gap-1.5"><Star className="h-3 w-3" /> {isFr ? "Score final" : "Final score"}</p>
          <p className="stat-value mt-2">{result.score.toFixed(2)}</p>
        </motion.div>
      </div>

      {/* Path Timeline */}
      {result.path && result.path.length > 0 && (
        <motion.div variants={item}>
          <PathTimeline path={result.path} />
        </motion.div>
      )}

      {/* Score breakdown */}
      {result.score_breakdown && (
        <motion.div variants={item} className="premium-card p-6">
          <h3 className="stat-label mb-4 flex items-center gap-2">
            <TrendingUp className="h-3.5 w-3.5 text-primary" /> {isFr ? "Détail du score" : "Score breakdown"}
          </h3>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {Object.entries(result.score_breakdown).map(([key, value]) => (
              <div key={key} className="flex justify-between items-center rounded-lg bg-muted/40 px-4 py-2.5 border border-border/50">
                <span className="text-sm text-muted-foreground">{key}</span>
                <Badge variant="secondary" className="font-mono text-xs shadow-none">{String(value)}</Badge>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Explanation */}
      {(result.explanation || result.rationale) && (
        <motion.div variants={item} className="premium-card p-6">
          {result.policy_used && (
            <p className="text-xs text-muted-foreground mb-3">
              {isFr ? "Politique utilisée" : "Policy used"}: <span className="font-medium">{result.policy_used}</span>
              {result.fallback_reason ? ` (${result.fallback_reason})` : ""}
            </p>
          )}
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="stat-label text-primary hover:text-primary/80 transition-colors"
          >
            {showExplanation ? (isFr ? "▾ Masquer l'explication" : "▾ Hide explanation") : (isFr ? "▸ Voir l'explication détaillée" : "▸ View detailed explanation")}
          </button>
          {showExplanation && (
            <motion.div initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: "auto" }} className="mt-4 space-y-3 text-sm text-muted-foreground leading-relaxed">
              {result.explanation && <p>{result.explanation}</p>}
              {result.rationale && (
                <div className="border-l-2 border-primary/30 pl-4 italic text-foreground/70">{result.rationale}</div>
              )}
            </motion.div>
          )}
        </motion.div>
      )}

      {/* Actions */}
      <motion.div variants={item} className="flex gap-3">
        <Button variant="outline" size="sm" onClick={handleCopy} className="shadow-card">
          {copied ? <Check className="mr-2 h-3.5 w-3.5" /> : <Copy className="mr-2 h-3.5 w-3.5" />}
          {copied ? (isFr ? "Copié !" : "Copied!") : (isFr ? "Copier JSON" : "Copy JSON")}
        </Button>
      </motion.div>

      <motion.div variants={item}>
        <JsonViewer data={result} title={isFr ? "Réponse JSON complète" : "Full JSON response"} />
      </motion.div>
    </motion.div>
  );
}
