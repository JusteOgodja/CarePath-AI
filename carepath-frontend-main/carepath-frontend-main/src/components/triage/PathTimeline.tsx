import { motion } from "framer-motion";
import { Circle, ArrowRight, MapPin } from "lucide-react";

export function PathTimeline({ path }: { path: string[] }) {
  return (
    <div className="premium-card p-6">
      <p className="stat-label mb-4 flex items-center gap-2">
        <MapPin className="h-3.5 w-3.5 text-primary" /> Chemin de référence
      </p>
      <div className="flex items-center gap-2 overflow-x-auto pb-2">
        {path.map((node, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1, type: "spring", stiffness: 300 }}
            className="flex items-center gap-2 shrink-0"
          >
            <div className="flex items-center gap-2.5 rounded-xl bg-primary/8 border border-primary/15 px-4 py-2.5">
              <div className="h-2.5 w-2.5 rounded-full bg-primary shadow-sm" />
              <span className="text-sm font-semibold">{node}</span>
            </div>
            {i < path.length - 1 && (
              <div className="flex items-center gap-0.5">
                <div className="w-6 h-px bg-primary/30" />
                <ArrowRight className="h-3.5 w-3.5 text-primary/50 shrink-0" />
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
