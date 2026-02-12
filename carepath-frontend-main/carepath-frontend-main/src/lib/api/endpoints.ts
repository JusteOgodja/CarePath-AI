import { apiFetch } from "./client";
import type {
  Centre,
  CentreRaw,
  Reference,
  RecommandationRequest,
  RecommandationResponse,
  CountryIndicator,
  HealthResponse,
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

export const deleteReference = (id: string) =>
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
