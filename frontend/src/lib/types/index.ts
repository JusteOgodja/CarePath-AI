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
  routing_policy?: "heuristic" | "auto" | "rl";
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
  policy_used?: "heuristic" | "rl";
  fallback_reason?: string | null;
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
  database?: string;
  schema_revision?: string | null;
  time_utc?: string;
}

// === API Error ===
export interface ApiError {
  status: number;
  message: string;
  details?: unknown;
}


export type ReferralStatus = "pending" | "accepted" | "in_transit" | "completed" | "rejected" | "cancelled";

export interface ReferralRequest {
  id: number;
  patient_id: string;
  source_id: string;
  needed_speciality: "maternal" | "pediatric" | "general";
  severity: "low" | "medium" | "high";
  proposed_dest_id?: string | null;
  accepted_dest_id?: string | null;
  status: ReferralStatus;
  notes?: string | null;
  feedback_diagnosis?: string | null;
  feedback_treatment?: string | null;
  feedback_followup?: string | null;
  created_by?: string | null;
  created_at: string;
  updated_at: string;
  closed_at?: string | null;
}

export interface ReferralCreatePayload {
  patient_id: string;
  source_id: string;
  needed_speciality: "maternal" | "pediatric" | "general";
  severity: "low" | "medium" | "high";
  proposed_dest_id?: string;
  notes?: string;
}
