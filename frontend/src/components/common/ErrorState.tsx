import React from "react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { useI18n } from "@/lib/i18n";

interface ErrorStateProps {
  title?: string;
  message: string;
  details?: string;
  onRetry?: () => void;
}

export function ErrorState({ title = "Erreur", message, details, onRetry }: ErrorStateProps) {
  const { language } = useI18n();
  const isFr = language === "fr";
  const [showDetails, setShowDetails] = React.useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center gap-4 py-12 text-center"
    >
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-destructive/10">
        <AlertCircle className="h-6 w-6 text-destructive" />
      </div>
      <div>
        <h3 className="text-lg font-semibold">{title === "Erreur" ? (isFr ? "Erreur" : "Error") : title}</h3>
        <p className="mt-1 text-sm text-muted-foreground">{message}</p>
      </div>
      {details && (
        <div className="w-full max-w-md">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs text-muted-foreground underline"
          >
            {showDetails ? (isFr ? "Masquer les détails" : "Hide details") : (isFr ? "Voir les détails" : "Show details")}
          </button>
          {showDetails && (
            <pre className="mt-2 rounded-md bg-muted p-3 text-left text-xs font-mono overflow-auto max-h-40">
              {details}
            </pre>
          )}
        </div>
      )}
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry}>
          <RefreshCw className="mr-2 h-4 w-4" /> {isFr ? "Réessayer" : "Retry"}
        </Button>
      )}
    </motion.div>
  );
}
