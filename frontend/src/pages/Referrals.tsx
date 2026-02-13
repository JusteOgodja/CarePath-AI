import React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  acceptReferralRequest,
  completeReferralRequest,
  createReferralRequest,
  listCentres,
  listReferralRequests,
  rejectReferralRequest,
  startReferralTransfer,
} from "@/lib/api/endpoints";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { useI18n } from "@/lib/i18n";

const statusColor: Record<string, string> = {
  pending: "bg-amber-500/10 text-amber-600 border-amber-500/20",
  accepted: "bg-blue-500/10 text-blue-600 border-blue-500/20",
  in_transit: "bg-indigo-500/10 text-indigo-600 border-indigo-500/20",
  completed: "bg-emerald-500/10 text-emerald-600 border-emerald-500/20",
  rejected: "bg-rose-500/10 text-rose-600 border-rose-500/20",
  cancelled: "bg-slate-500/10 text-slate-600 border-slate-500/20",
};

export default function ReferralsPage() {
  const { language } = useI18n();
  const isFr = language === "fr";
  const PAGE_SIZE = 10;
  const qc = useQueryClient();
  const [patientId, setPatientId] = React.useState("");
  const [sourceId, setSourceId] = React.useState("");
  const [speciality, setSpeciality] = React.useState<"maternal" | "pediatric" | "general">("maternal");
  const [severity, setSeverity] = React.useState<"low" | "medium" | "high">("medium");
  const [proposedDestId, setProposedDestId] = React.useState("");
  const [statusFilter, setStatusFilter] = React.useState("all");
  const [search, setSearch] = React.useState("");
  const [page, setPage] = React.useState(1);

  const centresQuery = useQuery({ queryKey: ["centres"], queryFn: listCentres });
  const referralsQuery = useQuery({
    queryKey: ["referral-requests", statusFilter],
    queryFn: () => listReferralRequests({ status_filter: statusFilter === "all" ? undefined : statusFilter }),
  });

  React.useEffect(() => {
    setPage(1);
  }, [statusFilter, search]);

  const filteredReferrals = React.useMemo(() => {
    const data = referralsQuery.data || [];
    const q = search.trim().toLowerCase();
    if (!q) return data;
    return data.filter((r) =>
      [String(r.id), r.patient_id, r.source_id, r.accepted_dest_id || "", r.proposed_dest_id || "", r.needed_speciality]
        .join(" ")
        .toLowerCase()
        .includes(q)
    );
  }, [referralsQuery.data, search]);

  const totalPages = Math.max(1, Math.ceil(filteredReferrals.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const paginatedReferrals = filteredReferrals.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  const counts = React.useMemo(() => {
    const all = referralsQuery.data || [];
    return {
      total: all.length,
      pending: all.filter((r) => r.status === "pending").length,
      active: all.filter((r) => r.status === "accepted" || r.status === "in_transit").length,
      completed: all.filter((r) => r.status === "completed").length,
    };
  }, [referralsQuery.data]);

  const refresh = () => qc.invalidateQueries({ queryKey: ["referral-requests"] });

  const createMutation = useMutation({
    mutationFn: createReferralRequest,
    onSuccess: () => {
      toast.success(isFr ? "Demande créée" : "Request created");
      setPatientId("");
      refresh();
    },
    onError: () => toast.error(isFr ? "Échec de création" : "Creation failed"),
  });

  const onCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!patientId || !sourceId) {
      toast.error(isFr ? "Patient et source requis" : "Patient and source are required");
      return;
    }
    createMutation.mutate({
      patient_id: patientId,
      source_id: sourceId,
      needed_speciality: speciality,
      severity,
      proposed_dest_id: proposedDestId || undefined,
    });
  };

  const action = async (fn: () => Promise<unknown>, ok: string) => {
    try {
      await fn();
      toast.success(ok);
      refresh();
    } catch {
      toast.error(isFr ? "Action échouée" : "Action failed");
    }
  };

  return (
    <div className="space-y-6 pb-20 lg:pb-0">
      <div className="page-header">
        <h1>Patient Referral Workflow</h1>
        <p>{isFr ? "Créer, accepter, transférer et clôturer les références avec feedback" : "Create, accept, transfer and complete referrals with feedback"}</p>
      </div>

      <form onSubmit={onCreate} className="premium-card p-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div className="space-y-1.5">
          <Label>Patient ID</Label>
          <Input value={patientId} onChange={(e) => setPatientId(e.target.value)} placeholder="P-001" />
        </div>

        <div className="space-y-1.5">
          <Label>{isFr ? "Centre source" : "Source center"}</Label>
          <Select value={sourceId} onValueChange={setSourceId}>
            <SelectTrigger><SelectValue placeholder={isFr ? "Sélectionner la source" : "Select source"} /></SelectTrigger>
            <SelectContent>
              {(centresQuery.data || []).map((c) => <SelectItem key={c.id} value={c.id}>{c.name} ({c.id})</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>{isFr ? "Destination proposée" : "Proposed destination"}</Label>
          <Select value={proposedDestId || "none"} onValueChange={(v) => setProposedDestId(v === "none" ? "" : v)}>
            <SelectTrigger><SelectValue placeholder={isFr ? "Optionnel" : "Optional"} /></SelectTrigger>
            <SelectContent>
              <SelectItem value="none">{isFr ? "Aucune" : "None"}</SelectItem>
              {(centresQuery.data || []).map((c) => <SelectItem key={c.id} value={c.id}>{c.name} ({c.id})</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>{isFr ? "Spécialité" : "Specialty"}</Label>
          <Select value={speciality} onValueChange={(v) => setSpeciality(v as "maternal" | "pediatric" | "general")}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="maternal">Maternal</SelectItem>
              <SelectItem value="pediatric">Pediatric</SelectItem>
              <SelectItem value="general">{isFr ? "Général" : "General"}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>{isFr ? "Sévérité" : "Severity"}</Label>
          <Select value={severity} onValueChange={(v) => setSeverity(v as "low" | "medium" | "high")}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem value="low">{isFr ? "Faible" : "Low"}</SelectItem>
              <SelectItem value="medium">{isFr ? "Moyenne" : "Medium"}</SelectItem>
              <SelectItem value="high">{isFr ? "Élevée" : "High"}</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-end">
          <Button type="submit" className="w-full" disabled={createMutation.isPending}>{isFr ? "Créer la demande" : "Create request"}</Button>
        </div>
      </form>

      <div className="premium-card p-5 overflow-auto">
        <div className="mb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <div className="kpi-card py-3 px-4"><p className="stat-label">Total</p><p className="text-xl font-bold">{counts.total}</p></div>
          <div className="kpi-card py-3 px-4"><p className="stat-label">{isFr ? "En attente" : "Pending"}</p><p className="text-xl font-bold">{counts.pending}</p></div>
          <div className="kpi-card py-3 px-4"><p className="stat-label">En cours</p><p className="text-xl font-bold">{counts.active}</p></div>
          <div className="kpi-card py-3 px-4"><p className="stat-label">Completed</p><p className="text-xl font-bold">{counts.completed}</p></div>
        </div>

        <div className="mb-4 flex flex-wrap items-end gap-3">
          <div className="space-y-1.5">
            <Label>Filtre statut</Label>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full sm:w-48"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">{isFr ? "Tous" : "All"}</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="accepted">Accepted</SelectItem>
                <SelectItem value="in_transit">In transit</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="rejected">Rejected</SelectItem>
                <SelectItem value="cancelled">Cancelled</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label>Recherche</Label>
            <Input
              className="w-full sm:w-72"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="ID, patient, source, destination..."
            />
          </div>
          <div className="text-xs text-muted-foreground sm:ml-auto">
            {filteredReferrals.length} {isFr ? "résultat(s)" : "result(s)"} - {isFr ? "page" : "page"} {safePage}/{totalPages}
          </div>
        </div>

        <div className="space-y-3 md:hidden">
          {paginatedReferrals.map((r) => (
            <div key={r.id} className="rounded-lg border border-border/60 p-3 space-y-2">
              <div className="flex items-center justify-between gap-2">
                <p className="font-mono text-xs">#{r.id} - {r.patient_id}</p>
                <Badge variant="outline" className={statusColor[r.status] || ""}>{r.status}</Badge>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <p><span className="text-muted-foreground">Source:</span> <span className="font-mono">{r.source_id}</span></p>
                <p><span className="text-muted-foreground">Dest:</span> <span className="font-mono">{r.accepted_dest_id || r.proposed_dest_id || "-"}</span></p>
                <p><span className="text-muted-foreground">Severity:</span> {r.severity}</p>
                <p><span className="text-muted-foreground">Speciality:</span> {r.needed_speciality}</p>
              </div>
              <div className="flex gap-2 flex-wrap">
                {r.status === "pending" && (
                  <>
                    <Button size="sm" variant="outline" onClick={() => {
                      const dest = r.proposed_dest_id || proposedDestId;
                      if (!dest) {
                        toast.error(isFr ? "Aucune destination disponible" : "No destination available");
                        return;
                      }
                      action(() => acceptReferralRequest(r.id, dest), isFr ? "Demande acceptée" : "Request accepted");
                    }}>{isFr ? "Accepter" : "Accept"}</Button>
                    <Button size="sm" variant="outline" onClick={() => action(() => rejectReferralRequest(r.id, "Rejected by liaison"), isFr ? "Demande rejetée" : "Request rejected")}>{isFr ? "Rejeter" : "Reject"}</Button>
                  </>
                )}
                {r.status === "accepted" && (
                  <Button size="sm" variant="outline" onClick={() => action(() => startReferralTransfer(r.id, "Patient in transfer"), isFr ? "Transfert démarré" : "Transfer started")}>{isFr ? "Démarrer" : "Start"}</Button>
                )}
                {r.status === "in_transit" && (
                  <Button size="sm" variant="outline" onClick={() => action(() => completeReferralRequest(r.id, { diagnosis: "N/A", treatment: "N/A", followup: "N/A" }), isFr ? "Référence clôturée" : "Referral completed")}>{isFr ? "Clôturer" : "Complete"}</Button>
                )}
              </div>
            </div>
          ))}
        </div>

        <div className="hidden md:block min-w-[920px]">
          <div className="grid grid-cols-8 gap-3 text-xs font-semibold text-muted-foreground uppercase">
            <div>ID</div><div>Patient</div><div>Source</div><div>Destination</div><div>Status</div><div>Severity</div><div>Speciality</div><div>Actions</div>
          </div>

          <div className="mt-3 space-y-2">
            {paginatedReferrals.map((r) => (
              <div key={r.id} className="grid grid-cols-8 gap-3 items-center rounded-lg border border-border/60 p-3">
                <div className="font-mono text-xs">#{r.id}</div>
                <div className="text-sm">{r.patient_id}</div>
                <div className="font-mono text-xs">{r.source_id}</div>
                <div className="font-mono text-xs">{r.accepted_dest_id || r.proposed_dest_id || "-"}</div>
                <div><Badge variant="outline" className={statusColor[r.status] || ""}>{r.status}</Badge></div>
                <div className="text-sm">{r.severity}</div>
                <div className="text-sm">{r.needed_speciality}</div>
                <div className="flex gap-1 flex-wrap">
                  {r.status === "pending" && (
                    <>
                      <Button size="sm" variant="outline" onClick={() => {
                        const dest = r.proposed_dest_id || proposedDestId;
                        if (!dest) {
                        toast.error(isFr ? "Aucune destination disponible" : "No destination available");
                        return;
                      }
                        action(() => acceptReferralRequest(r.id, dest), isFr ? "Demande acceptée" : "Request accepted");
                      }}>{isFr ? "Accepter" : "Accept"}</Button>
                      <Button size="sm" variant="outline" onClick={() => action(() => rejectReferralRequest(r.id, "Rejected by liaison"), isFr ? "Demande rejetée" : "Request rejected")}>{isFr ? "Rejeter" : "Reject"}</Button>
                    </>
                  )}
                  {r.status === "accepted" && (
                    <Button size="sm" variant="outline" onClick={() => action(() => startReferralTransfer(r.id, "Patient in transfer"), isFr ? "Transfert démarré" : "Transfer started")}>{isFr ? "Démarrer" : "Start"}</Button>
                  )}
                  {r.status === "in_transit" && (
                    <Button size="sm" variant="outline" onClick={() => action(() => completeReferralRequest(r.id, { diagnosis: "N/A", treatment: "N/A", followup: "N/A" }), isFr ? "Référence clôturée" : "Referral completed")}>{isFr ? "Clôturer" : "Complete"}</Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {!referralsQuery.isLoading && paginatedReferrals.length === 0 && (
          <div className="rounded-lg border border-dashed border-border/70 p-6 text-sm text-muted-foreground">
            {isFr ? "Aucune référence ne correspond au filtre courant." : "No referral matches the current filter."}
          </div>
        )}

        <div className="mt-4 flex items-center justify-end gap-2">
          <Button variant="outline" size="sm" disabled={safePage <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
            {isFr ? "Précédent" : "Previous"}
          </Button>
          <Button variant="outline" size="sm" disabled={safePage >= totalPages} onClick={() => setPage((p) => Math.min(totalPages, p + 1))}>
            {isFr ? "Suivant" : "Next"}
          </Button>
        </div>
      </div>
    </div>
  );
}
