import React from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { listReferences, listCentres, deleteReference } from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import {
  AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent,
  AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Plus, Pencil, Trash2, Search } from "lucide-react";
import { TableSkeleton } from "@/components/common/LoadingSkeleton";
import { ErrorState } from "@/components/common/ErrorState";
import { EmptyState } from "@/components/common/EmptyState";
import { ReferenceModal } from "./ReferenceModal";
import { toast } from "sonner";
import type { Reference } from "@/lib/types";

export function ReferencesTable() {
  const queryClient = useQueryClient();
  const [search, setSearch] = React.useState("");
  const [modalOpen, setModalOpen] = React.useState(false);
  const [editRef, setEditRef] = React.useState<Reference | null>(null);
  const [deleteId, setDeleteId] = React.useState<number | null>(null);

  const { data: refs = [], isLoading, error, refetch } = useQuery({
    queryKey: ["references"],
    queryFn: listReferences,
  });

  useQuery({ queryKey: ["centres"], queryFn: listCentres });

  const delMutation = useMutation({
    mutationFn: deleteReference,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["references"] });
      toast.success("Référence supprimée");
      setDeleteId(null);
    },
    onError: () => { toast.error("Erreur lors de la suppression"); setDeleteId(null); },
  });

  const filtered = refs.filter(
    (r) =>
      r.source_id.toLowerCase().includes(search.toLowerCase()) ||
      r.dest_id.toLowerCase().includes(search.toLowerCase())
  );

  if (isLoading) return <TableSkeleton cols={4} />;
  if (error) return <ErrorState message="Impossible de charger les références" onRetry={() => refetch()} />;

  return (
    <div className="space-y-5">
      <div className="flex flex-col sm:flex-row gap-3 justify-between">
        <div className="relative max-w-sm flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input placeholder="Filtrer par source/dest..." value={search} onChange={(e) => setSearch(e.target.value)} className="pl-9 h-11" />
        </div>
        <Button onClick={() => { setEditRef(null); setModalOpen(true); }} className="h-11 shadow-card" style={{ background: "var(--gradient-primary)" }}>
          <Plus className="mr-2 h-4 w-4" /> Ajouter une référence
        </Button>
      </div>

      {filtered.length === 0 ? (
        <EmptyState title="Aucune référence" description="Ajoutez une route de référence entre centres" />
      ) : (
        <div className="premium-card overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/30">
                <TableHead className="text-2xs uppercase tracking-wider font-semibold">Source</TableHead>
                <TableHead className="text-2xs uppercase tracking-wider font-semibold">Destination</TableHead>
                <TableHead className="text-2xs uppercase tracking-wider font-semibold">Temps (min)</TableHead>
                <TableHead className="w-24 text-2xs uppercase tracking-wider font-semibold">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((r, i) => (
                <TableRow key={r.id || i} className="hover:bg-muted/30 transition-colors">
                  <TableCell className="font-mono text-xs">{r.source_id}</TableCell>
                  <TableCell className="font-mono text-xs">{r.dest_id}</TableCell>
                  <TableCell className="text-sm font-semibold">{r.travel_minutes}</TableCell>
                  <TableCell>
                    <div className="flex gap-0.5">
                      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => { setEditRef(r); setModalOpen(true); }}>
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => setDeleteId(r.id ?? null)}>
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

      <ReferenceModal open={modalOpen} onOpenChange={setModalOpen} reference={editRef} />

      <AlertDialog open={!!deleteId} onOpenChange={() => setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Supprimer cette référence ?</AlertDialogTitle>
            <AlertDialogDescription>Cette action est irréversible.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Annuler</AlertDialogCancel>
            <AlertDialogAction onClick={() => deleteId && delMutation.mutate(deleteId)} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Supprimer
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
