import React from "react";
import { motion } from "framer-motion";
import { Clock, MapPin, Star, TrendingUp, Copy, Check, Timer } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { RecommandationResponse } from "@/lib/types";
import { PathTimeline } from "./PathTimeline";
import { JsonViewer } from "@/components/common/JsonViewer";

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
          <p className="stat-label">Destination</p>
          <p className="text-xl font-bold mt-2">{result.destination_name}</p>
          <p className="text-xs text-muted-foreground font-mono mt-1">{result.destination_id}</p>
        </motion.div>

        <motion.div variants={item} className="kpi-card">
          <p className="stat-label flex items-center gap-1.5"><MapPin className="h-3 w-3" /> Temps de trajet</p>
          <p className="stat-value mt-2">{result.estimated_travel_minutes}<span className="text-sm font-normal text-muted-foreground ml-1">min</span></p>
        </motion.div>

        <motion.div variants={item} className="kpi-card">
          <p className="stat-label flex items-center gap-1.5"><Timer className="h-3 w-3" /> Attente estimée</p>
          <p className="stat-value mt-2">{result.estimated_wait_minutes}<span className="text-sm font-normal text-muted-foreground ml-1">min</span></p>
        </motion.div>

        <motion.div variants={item} className="kpi-card">
          <p className="stat-label flex items-center gap-1.5"><Star className="h-3 w-3" /> Score final</p>
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
            <TrendingUp className="h-3.5 w-3.5 text-primary" /> Détail du score
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
          <button
            onClick={() => setShowExplanation(!showExplanation)}
            className="stat-label text-primary hover:text-primary/80 transition-colors"
          >
            {showExplanation ? "▾ Masquer l'explication" : "▸ Voir l'explication détaillée"}
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
          {copied ? "Copié !" : "Copier JSON"}
        </Button>
      </motion.div>

      <motion.div variants={item}>
        <JsonViewer data={result} title="Réponse JSON complète" />
      </motion.div>
    </motion.div>
  );
}
