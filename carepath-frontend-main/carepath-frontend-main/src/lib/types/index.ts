// === Centres ===
export interface Centre {
  id: string;
  name: string;
  level: "primary" | "secondary" | "tertiary";
  specialities: string[];
  capacity_max: number;
  capacity_available: number;
  estimated_wait_minutes: number;
  lat: number;
  lon: number;
  catchment_population: number;
}

export interface CentreRaw {
  id: string;
  name: string;
  level: "primary" | "secondary" | "tertiary";
  specialities: string; // CSV string from backend
  capacity_max: number;
  capacity_available: number;
  estimated_wait_minutes: number;
  lat: number;
  lon: number;
  catchment_population: number;
}

// === References ===
export interface Reference {
  id?: string;
  source_id: string;
  dest_id: string;
  travel_minutes: number;
}

// === Recommendation ===
export interface RecommandationRequest {
  patient_id: string;
  current_centre_id: string;
  needed_speciality: string;
  severity: "low" | "medium" | "high";
}

export interface ScoreBreakdown {
  [key: string]: number | string;
}

export interface RecommandationResponse {
  destination_id: string;
  destination_name: string;
  path: string[];
  estimated_travel_minutes: number;
  estimated_wait_minutes: number;
  score: number;
  score_breakdown: ScoreBreakdown;
  explanation: string;
  rationale: string;
}

// === Indicators ===
export interface CountryIndicator {
  country_code: string;
  indicator_code: string;
  indicator_name?: string;
  year?: number;
  value?: number;
  unit?: string;
}

// === Health ===
export interface HealthResponse {
  status: string;
}

// === API Error ===
export interface ApiError {
  status: number;
  message: string;
  details?: unknown;
}
