// === Centres ===
export interface Centre {
  id: string;
  name: string;
  level: string;
  specialities: string[];
  capacity_max: number;
  capacity_available: number;
  estimated_wait_minutes: number;
  lat?: number | null;
  lon?: number | null;
  catchment_population?: number;
}

export interface CentreRaw {
  id: string;
  name: string;
  level: string;
  specialities: string | string[]; // CSV string or array from backend
  capacity_max?: number;
  capacity_available: number;
  estimated_wait_minutes: number;
  lat?: number | null;
  lon?: number | null;
  catchment_population?: number;
}

// === References ===
export interface Reference {
  id?: number;
  source_id: string;
  dest_id: string;
  travel_minutes: number;
}

// === Recommendation ===
export interface RecommandationRequest {
  patient_id: string;
  current_centre_id: string;
  needed_speciality: "maternal" | "pediatric" | "general";
  severity: "low" | "medium" | "high";
}

export interface ScoreBreakdown {
  [key: string]: number | string;
}

export interface RecommandationResponse {
  patient_id: string;
  destination_centre_id: string;
  destination_name: string;
  path: PathStep[];
  estimated_travel_minutes: number;
  estimated_wait_minutes: number;
  score: number;
  explanation: string;
  rationale: string;
  score_breakdown: ScoreBreakdown;
}

export interface PathStep {
  centre_id: string;
  centre_name: string;
  level: string;
}

export interface ScoreBreakdown {
  travel_minutes: number;
  wait_minutes: number;
  capacity_available: number;
  capacity_factor_used: number;
  severity: "low" | "medium" | "high";
  severity_weight: number;
  raw_cost_travel_plus_wait: number;
  final_score: number;
}

// === Indicators ===
export interface CountryIndicator {
  country_code: string;
  indicator_code: string;
  indicator_name: string | null;
  year: number;
  value: number;
  source_file: string | null;
  unit?: string | null;
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
