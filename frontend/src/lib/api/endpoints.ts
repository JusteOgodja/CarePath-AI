import { apiFetch } from "./client";
import type {
  Centre,
  CentreRaw,
  Reference,
  RecommandationRequest,
  RecommandationResponse,
  CountryIndicator,
  HealthResponse,
  ReferralRequest,
  ReferralCreatePayload,
} from "@/lib/types";
import { centreFromRaw, centreToRaw } from "@/lib/mappers/centres";

// Health
export const getHealth = () => apiFetch<HealthResponse>("/health");

// Recommendation
export const recommend = (payload: RecommandationRequest) =>
  apiFetch<RecommandationResponse>("/recommander", {
    method: "POST",
    body: JSON.stringify(payload),
  });

// Centres
export const listCentres = async (): Promise<Centre[]> => {
  const raw = await apiFetch<CentreRaw[]>("/centres");
  return raw.map(centreFromRaw);
};

export const createCentre = async (centre: Centre) =>
  apiFetch<CentreRaw>("/centres", {
    method: "POST",
    body: JSON.stringify(centreToRaw(centre)),
  });

export const updateCentre = async (centre: Centre) =>
  apiFetch<CentreRaw>(`/centres/${centre.id}`, {
    method: "PUT",
    body: JSON.stringify(centreToRaw(centre)),
  });

export const deleteCentre = (id: string) =>
  apiFetch<void>(`/centres/${id}`, { method: "DELETE" });

// References
export const listReferences = () => apiFetch<Reference[]>("/references");

export const createReference = (ref: Reference) =>
  apiFetch<Reference>("/references", {
    method: "POST",
    body: JSON.stringify(ref),
  });

export const updateReference = (ref: Reference) =>
  apiFetch<Reference>(`/references/${ref.id}`, {
    method: "PUT",
    body: JSON.stringify(ref),
  });

export const deleteReference = (id: number) =>
  apiFetch<void>(`/references/${id}`, { method: "DELETE" });

// Indicators
export const listLatestIndicators = (countryCode: string) =>
  apiFetch<CountryIndicator[]>(`/indicators/latest?country_code=${encodeURIComponent(countryCode)}`);

export const listIndicators = (params: { country_code?: string; indicator_code?: string }) => {
  const searchParams = new URLSearchParams();
  if (params.country_code) searchParams.set("country_code", params.country_code);
  if (params.indicator_code) searchParams.set("indicator_code", params.indicator_code);
  const qs = searchParams.toString();
  return apiFetch<CountryIndicator[]>(`/indicators${qs ? `?${qs}` : ""}`);
};


// Referral workflow
export const listReferralRequests = (params?: { status_filter?: string; source_id?: string }) => {
  const searchParams = new URLSearchParams();
  if (params?.status_filter) searchParams.set("status_filter", params.status_filter);
  if (params?.source_id) searchParams.set("source_id", params.source_id);
  const qs = searchParams.toString();
  return apiFetch<ReferralRequest[]>(`/referrals/requests${qs ? `?${qs}` : ""}`);
};

export const createReferralRequest = (payload: ReferralCreatePayload) =>
  apiFetch<ReferralRequest>("/referrals/requests", {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const acceptReferralRequest = (requestId: number, accepted_dest_id: string, notes?: string) =>
  apiFetch<ReferralRequest>(`/referrals/requests/${requestId}/accept`, {
    method: "POST",
    body: JSON.stringify({ accepted_dest_id, notes }),
  });

export const startReferralTransfer = (requestId: number, notes?: string) =>
  apiFetch<ReferralRequest>(`/referrals/requests/${requestId}/start-transfer`, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });

export const completeReferralRequest = (
  requestId: number,
  payload: { diagnosis?: string; treatment?: string; followup?: string; notes?: string }
) =>
  apiFetch<ReferralRequest>(`/referrals/requests/${requestId}/complete`, {
    method: "POST",
    body: JSON.stringify(payload),
  });

export const rejectReferralRequest = (requestId: number, notes?: string) =>
  apiFetch<ReferralRequest>(`/referrals/requests/${requestId}/reject`, {
    method: "POST",
    body: JSON.stringify({ notes }),
  });
