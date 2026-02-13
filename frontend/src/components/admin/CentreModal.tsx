import React from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createCentre, updateCentre } from "@/lib/api/endpoints";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import type { Centre } from "@/lib/types";

const schema = z.object({
  id: z.string().trim().min(1, "ID requis").max(50),
  name: z.string().trim().min(1, "Nom requis").max(200),
  level: z.enum(["primary", "secondary", "tertiary"]),
  specialities_input: z.string().trim(),
  capacity_max: z.coerce.number().min(0, "≥ 0"),
  capacity_available: z.coerce.number().min(0, "≥ 0"),
  estimated_wait_minutes: z.coerce.number().min(0, "≥ 0"),
  lat: z.coerce.number().min(-90).max(90),
  lon: z.coerce.number().min(-180).max(180),
  catchment_population: z.coerce.number().min(0, "≥ 0"),
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  centre: Centre | null;
}

const toFormDefaults = (centre: Centre | null): FormData => {
  if (!centre) {
    return {
      id: "",
      name: "",
      level: "primary",
      specialities_input: "",
      capacity_max: 0,
      capacity_available: 0,
      estimated_wait_minutes: 0,
      lat: 0,
      lon: 0,
      catchment_population: 0,
    };
  }

  const level = ["primary", "secondary", "tertiary"].includes(centre.level)
    ? (centre.level as "primary" | "secondary" | "tertiary")
    : "primary";

  return {
    id: centre.id,
    name: centre.name,
    level,
    specialities_input: centre.specialities.join(", "),
    capacity_max: centre.capacity_max ?? 0,
    capacity_available: centre.capacity_available ?? 0,
    estimated_wait_minutes: centre.estimated_wait_minutes ?? 0,
    lat: centre.lat ?? 0,
    lon: centre.lon ?? 0,
    catchment_population: centre.catchment_population ?? 0,
  };
};

export function CentreModal({ open, onOpenChange, centre }: Props) {
  const queryClient = useQueryClient();
  const isEdit = !!centre;

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: toFormDefaults(centre),
  });

  React.useEffect(() => {
    if (open) {
      reset(toFormDefaults(centre));
    }
  }, [open, centre, reset]);

  const mutation = useMutation({
    mutationFn: (data: Centre) => (isEdit ? updateCentre(data) : createCentre(data)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["centres"] });
      toast.success(isEdit ? "Centre mis à jour" : "Centre créé");
      onOpenChange(false);
    },
    onError: () => toast.error("Erreur lors de l'enregistrement"),
  });

  const onSubmit = (data: FormData) => {
    const centreData: Centre = {
      id: data.id,
      name: data.name,
      level: data.level,
      specialities: data.specialities_input.split(",").map((s) => s.trim()).filter(Boolean),
      capacity_max: data.capacity_max,
      capacity_available: data.capacity_available,
      estimated_wait_minutes: data.estimated_wait_minutes,
      lat: data.lat,
      lon: data.lon,
      catchment_population: data.catchment_population,
    };
    mutation.mutate(centreData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Modifier le centre" : "Nouveau centre"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1">
            <Label>ID</Label>
            <Input {...register("id")} disabled={isEdit} />
            {errors.id && <p className="text-xs text-destructive">{errors.id.message}</p>}
          </div>
          <div className="space-y-1">
            <Label>Nom</Label>
            <Input {...register("name")} />
            {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
          </div>
          <div className="space-y-1">
            <Label>Niveau</Label>
            <Controller
              name="level"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} value={field.value}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="primary">Primary</SelectItem>
                    <SelectItem value="secondary">Secondary</SelectItem>
                    <SelectItem value="tertiary">Tertiary</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
          <div className="space-y-1">
            <Label>Spécialités (virgules)</Label>
            <Input {...register("specialities_input")} placeholder="maternal, pediatric" />
          </div>
          <div className="space-y-1">
            <Label>Capacité max</Label>
            <Input type="number" {...register("capacity_max")} />
            {errors.capacity_max && <p className="text-xs text-destructive">{errors.capacity_max.message}</p>}
          </div>
          <div className="space-y-1">
            <Label>Capacité disponible</Label>
            <Input type="number" {...register("capacity_available")} />
          </div>
          <div className="space-y-1">
            <Label>Attente (min)</Label>
            <Input type="number" {...register("estimated_wait_minutes")} />
          </div>
          <div className="space-y-1">
            <Label>Population</Label>
            <Input type="number" {...register("catchment_population")} />
          </div>
          <div className="space-y-1">
            <Label>Latitude</Label>
            <Input type="number" step="any" {...register("lat")} />
            {errors.lat && <p className="text-xs text-destructive">{errors.lat.message}</p>}
          </div>
          <div className="space-y-1">
            <Label>Longitude</Label>
            <Input type="number" step="any" {...register("lon")} />
            {errors.lon && <p className="text-xs text-destructive">{errors.lon.message}</p>}
          </div>
          <div className="sm:col-span-2 flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Annuler
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isEdit ? "Enregistrer" : "Créer"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
