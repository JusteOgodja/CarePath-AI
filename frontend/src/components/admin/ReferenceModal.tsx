import React from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createReference, updateReference, listCentres } from "@/lib/api/endpoints";
import {
  Dialog, DialogContent, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import type { Reference } from "@/lib/types";

const schema = z.object({
  source_id: z.string().min(1, "Source requise"),
  dest_id: z.string().min(1, "Destination requise"),
  travel_minutes: z.coerce.number().min(1, "> 0"),
}).refine((d) => d.source_id !== d.dest_id, {
  message: "Source et destination doivent être différentes",
  path: ["dest_id"],
});

type FormData = z.infer<typeof schema>;

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  reference: Reference | null;
}

export function ReferenceModal({ open, onOpenChange, reference }: Props) {
  const queryClient = useQueryClient();
  const isEdit = !!reference;

  const { data: centres = [] } = useQuery({ queryKey: ["centres"], queryFn: listCentres });

  const { register, handleSubmit, control, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: reference || { source_id: "", dest_id: "", travel_minutes: 0 },
  });

  React.useEffect(() => {
    if (open) reset(reference || { source_id: "", dest_id: "", travel_minutes: 0 });
  }, [open, reference, reset]);

  const mutation = useMutation({
    mutationFn: (data: Reference) => (isEdit ? updateReference(data) : createReference(data)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["references"] });
      toast.success(isEdit ? "Référence mise à jour" : "Référence créée");
      onOpenChange(false);
    },
    onError: () => toast.error("Erreur"),
  });

  const onSubmit = (data: FormData) => {
    mutation.mutate({ ...data, id: reference?.id } as Reference);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Modifier la référence" : "Nouvelle référence"}</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit(onSubmit)} className="grid gap-4">
          <div className="space-y-1">
            <Label>Source</Label>
            <Controller
              name="source_id"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} value={field.value}>
                  <SelectTrigger><SelectValue placeholder="Source" /></SelectTrigger>
                  <SelectContent>
                    {centres.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.name} ({c.id})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.source_id && <p className="text-xs text-destructive">{errors.source_id.message}</p>}
          </div>
          <div className="space-y-1">
            <Label>Destination</Label>
            <Controller
              name="dest_id"
              control={control}
              render={({ field }) => (
                <Select onValueChange={field.onChange} value={field.value}>
                  <SelectTrigger><SelectValue placeholder="Destination" /></SelectTrigger>
                  <SelectContent>
                    {centres.map((c) => (
                      <SelectItem key={c.id} value={c.id}>{c.name} ({c.id})</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            />
            {errors.dest_id && <p className="text-xs text-destructive">{errors.dest_id.message}</p>}
          </div>
          <div className="space-y-1">
            <Label>Temps de trajet (min)</Label>
            <Input type="number" {...register("travel_minutes")} />
            {errors.travel_minutes && <p className="text-xs text-destructive">{errors.travel_minutes.message}</p>}
          </div>
          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>Annuler</Button>
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
