import React from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { listCentres, recommend } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Stethoscope, RotateCcw, Loader2, Send } from "lucide-react";
import { motion } from "framer-motion";
import type { RecommandationRequest, RecommandationResponse } from "@/lib/types";
import { RecommendationResult } from "./RecommendationResult";
import { ApiClientError } from "@/lib/api/client";

const schema = z.object({
  patient_id: z.string().trim().min(1, "Patient ID requis").max(100),
  current_centre_id: z.string().min(1, "Centre requis"),
  needed_speciality: z.string().min(1, "Spécialité requise"),
  severity: z.enum(["low", "medium", "high"]),
});

type FormData = z.infer<typeof schema>;

const severityOptions = [
  { value: "low" as const, label: "Faible", color: "bg-severity-low" },
  { value: "medium" as const, label: "Modéré", color: "bg-severity-medium" },
  { value: "high" as const, label: "Élevé", color: "bg-severity-high" },
];

const specialities = ["maternal", "pediatric", "general"];

export function TriageForm() {
  const [result, setResult] = React.useState<RecommandationResponse | null>(null);

  const { data: centres = [], isLoading: centresLoading } = useQuery({
    queryKey: ["centres"],
    queryFn: listCentres,
  });

  const mutation = useMutation({
    mutationFn: recommend,
    onSuccess: (data) => setResult(data),
  });

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      patient_id: "",
      current_centre_id: "",
      needed_speciality: "",
      severity: "medium",
    },
  });

  const onSubmit = (data: FormData) => {
    mutation.mutate(data as RecommandationRequest);
  };

  const handleReset = () => {
    reset();
    setResult(null);
    mutation.reset();
  };

  const errorMessage = React.useMemo(() => {
    if (!mutation.error) return null;
    if (mutation.error instanceof ApiClientError) {
      if (mutation.error.status === 400) {
        const msg = mutation.error.message.toLowerCase();
        if (msg.includes("vide") || msg.includes("empty")) return "Le réseau est vide, ajoutez des centres d'abord.";
        if (msg.includes("atteignable") || msg.includes("reachable")) return "Aucune destination atteignable depuis ce centre.";
        if (msg.includes("compatible")) return "Aucune destination compatible avec cette spécialité.";
        return mutation.error.message;
      }
      return mutation.error.message;
    }
    return "Une erreur inattendue est survenue.";
  }, [mutation.error]);

  return (
    <div className="space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="premium-card p-6 lg:p-8"
      >
        <div className="flex items-center gap-3 mb-8">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10">
            <Stethoscope className="h-5 w-5 text-primary" />
          </div>
          <div>
            <h2 className="text-[15px] font-bold">Recommandation de transfert</h2>
            <p className="text-xs text-muted-foreground">Renseignez les informations patient pour obtenir une recommandation</p>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <div className="grid gap-5 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="patient_id" className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Patient ID</Label>
              <Input id="patient_id" placeholder="ex: PAT-001" {...register("patient_id")} className="h-11" />
              {errors.patient_id && <p className="text-xs text-destructive">{errors.patient_id.message}</p>}
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Centre actuel</Label>
              <Controller
                name="current_centre_id"
                control={control}
                render={({ field }) => (
                  <Select onValueChange={field.onChange} value={field.value}>
                    <SelectTrigger className="h-11">
                      <SelectValue placeholder={centresLoading ? "Chargement..." : "Sélectionner un centre"} />
                    </SelectTrigger>
                    <SelectContent>
                      {centres.map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.name} <span className="text-muted-foreground">({c.id})</span>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.current_centre_id && <p className="text-xs text-destructive">{errors.current_centre_id.message}</p>}
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Spécialité requise</Label>
              <Controller
                name="needed_speciality"
                control={control}
                render={({ field }) => (
                  <Select onValueChange={field.onChange} value={field.value}>
                    <SelectTrigger className="h-11">
                      <SelectValue placeholder="Choisir une spécialité" />
                    </SelectTrigger>
                    <SelectContent>
                      {specialities.map((s) => (
                        <SelectItem key={s} value={s}>
                          {s.charAt(0).toUpperCase() + s.slice(1)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
              {errors.needed_speciality && <p className="text-xs text-destructive">{errors.needed_speciality.message}</p>}
            </div>

            <div className="space-y-2">
              <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Sévérité</Label>
              <Controller
                name="severity"
                control={control}
                render={({ field }) => (
                  <Select onValueChange={field.onChange} value={field.value}>
                    <SelectTrigger className="h-11">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {severityOptions.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          <div className="flex items-center gap-2">
                            <span className={`inline-block h-2.5 w-2.5 rounded-full ${opt.color}`} />
                            {opt.label}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <Button type="submit" disabled={mutation.isPending} className="h-11 px-6 shadow-card" style={{ background: "var(--gradient-primary)" }}>
              {mutation.isPending ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : <Send className="mr-2 h-4 w-4" />}
              Recommander
            </Button>
            <Button type="button" variant="outline" onClick={handleReset} className="h-11">
              <RotateCcw className="mr-2 h-4 w-4" /> Réinitialiser
            </Button>
          </div>
        </form>

        {errorMessage && (
          <motion.div
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 rounded-xl border border-destructive/20 bg-destructive/5 p-4 text-sm text-destructive flex items-start gap-3"
          >
            <span className="h-5 w-5 rounded-full bg-destructive/10 flex items-center justify-center shrink-0 mt-0.5">!</span>
            {errorMessage}
          </motion.div>
        )}
      </motion.div>

      {mutation.isPending && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="kpi-card space-y-3 animate-pulse">
              <div className="h-3 w-16 bg-muted rounded" />
              <div className="h-8 w-24 bg-muted rounded" />
              <div className="h-2.5 w-12 bg-muted rounded" />
            </div>
          ))}
        </div>
      )}

      {result && !mutation.isPending && <RecommendationResult result={result} />}
    </div>
  );
}
