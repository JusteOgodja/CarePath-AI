import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listCentres, deleteCentre } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Plus, Pencil, Trash2, Search } from "lucide-react";
import { TableSkeleton } from "@/components/common/LoadingSkeleton";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { CentreModal } from "./CentreModal";
import { ApiClientError } from "@/lib/api/client";
import { toast } from "sonner";
import type { Centre } from "@/lib/types";

const levelColors: Record<string, string> = {
  primary: "bg-level-primary/10 text-level-primary border-level-primary/20",
  secondary: "bg-level-secondary/10 text-level-secondary border-level-secondary/20",
  tertiary: "bg-level-tertiary/10 text-level-tertiary border-level-tertiary/20",
};

export function CentresTable() {
  const queryClient = useQueryClient();
  const [search, setSearch] = React.useState("");
  const [modalOpen, setModalOpen] = React.useState(false);
  const [editCentre, setEditCentre] = React.useState<Centre | null>(null);
  const [deleteId, setDeleteId] = React.useState<string | null>(null);

  const { data: centres = [], isLoading, error, refetch } = useQuery({
    queryKey: ["centres"],
    queryFn: listCentres,
  });

  const delMutation = useMutation({
    mutationFn: deleteCentre,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["centres"] });
      toast.success("Centre supprimé");
      setDeleteId(null);
    },
    onError: (err) => {
      if (err instanceof ApiClientError && err.status === 409) {
        toast.error("Ce centre est référencé. Supprimez d'abord les références associées.");
      } else {
        toast.error("Erreur lors de la suppression");
      }
      setDeleteId(null);
    },
  });

  const filtered = centres.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.id.toLowerCase().includes(search.toLowerCase()) ||
      c.level.toLowerCase().includes(search.toLowerCase())
  );

  if (isLoading) return <TableSkeleton cols={5} />;
  if (error) return <ErrorState message="Impossible de charger les centres" onRetry={() => refetch()} />;

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row gap-3 justify-between">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Rechercher un centre..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9 h-11"
          />
        </div>
        <Button onClick={() => { setEditCentre(null); setModalOpen(true); }} className="h-11 shadow-card" style={{ background: "var(--gradient-primary)" }}>
          <Plus className="mr-2 h-4 w-4" /> Ajouter un centre
        </Button>
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="Aucun centre trouvé" description="Ajoutez un centre pour commencer à construire votre réseau" />
      ) : (
        <div className="premium-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30">
                <TableHead className="text-2xs uppercase tracking-wider font-semibold">ID</TableHead>
                <TableHead className="text-2xs uppercase tracking-wider font-semibold">Nom</TableHead>
                <TableHead className="text-2xs uppercase tracking-wider font-semibold">Niveau</TableHead>
                <TableHead className="text-2xs uppercase tracking-wider font-semibold">Spécialités</TableHead>
                <TableHead className="text-2xs uppercase tracking-wider font-semibold">Capacité</TableHead>
                <TableHead className="w-24 text-2xs uppercase tracking-wider font-semibold">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((c) => (
                <TableRow key={c.id} className="hover:bg-muted/30 transition-colors">
                  <TableCell className="font-mono text-xs text-muted-foreground">{c.id}</TableCell>
                  <TableCell className="font-medium text-sm">{c.name}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className={`text-2xs font-semibold shadow-none ${levelColors[c.level] || ""}`}>
                      {c.level}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {c.specialities.map((s) => (
                        <Badge key={s} variant="secondary" className="text-2xs shadow-none">{s}</Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm font-semibold">{c.capacity_available}</span>
                    <span className="text-xs text-muted-foreground">/{c.capacity_max}</span>
                  </TableCell>
                  <TableCell>
                    <div className="flex gap-0.5">
                      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => { setEditCentre(c); setModalOpen(true); }}>
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setDeleteId(c.id)}>
                        <Trash2 className="h-3.5 w-3.5 text-destructive" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}

      <CentreModal open={modalOpen} onOpenChange={setModalOpen} centre={editCentre} />

      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Supprimer ce centre ?</AlertDialogTitle>
            <AlertDialogDescription>
              Cette action est irréversible. Le centre sera définitivement supprimé du réseau.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => deleteId && delMutation.mutate(deleteId)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Supprimer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
