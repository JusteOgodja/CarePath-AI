import { TriageForm } from "@/components/triage/TriageForm";
import { Stethoscope } from "lucide-react";
import { motion } from "framer-motion";

export default function TriagePage() {
  return (
    <div className="space-y-8 pb-20 lg:pb-0">
      <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="page-header">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl shadow-card" style={{ background: "var(--gradient-primary)" }}>
            <Stethoscope className="h-5 w-5 text-primary-foreground" />
          </div>
          <div>
            <h1>Triage & Recommandation</h1>
            <p>Trouvez le meilleur centre de transfert pour votre patient</p>
          </div>
        </div>
      </motion.div>
      <TriageForm />
    </div>
  );
}
