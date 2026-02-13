from typing import Literal

from pydantic import BaseModel, Field


class RecommandationRequest(BaseModel):
    patient_id: str = Field(..., examples=["P001"])
    current_centre_id: str = Field(..., examples=["C_LOCAL_A"])
    needed_speciality: Literal["maternal", "pediatric", "general"]
    severity: Literal["low", "medium", "high"] = "medium"


class PathStep(BaseModel):
    centre_id: str
    centre_name: str
    level: str


class ScoreBreakdown(BaseModel):
    travel_minutes: float
    wait_minutes: float
    capacity_available: int
    capacity_factor_used: float
    severity: Literal["low", "medium", "high"]
    severity_weight: float
    raw_cost_travel_plus_wait: float
    final_score: float


class RecommandationResponse(BaseModel):
    patient_id: str
    destination_centre_id: str
    destination_name: str
    path: list[PathStep]
    estimated_travel_minutes: float
    estimated_wait_minutes: float
    score: float
    explanation: str
    rationale: str
    score_breakdown: ScoreBreakdown


class CentreCreate(BaseModel):
    id: str = Field(..., examples=["H_DISTRICT_2"])
    name: str = Field(..., examples=["Hopital District 2"])
    level: str = Field(..., examples=["secondary"])
    specialities: list[str] = Field(..., examples=[["general", "maternal"]])
    capacity_max: int = Field(10, ge=0, examples=[10])
    capacity_available: int = Field(..., ge=0, examples=[4])
    estimated_wait_minutes: int = Field(..., ge=0, examples=[30])
    lat: float | None = Field(None, ge=-90, le=90, examples=[-1.286389])
    lon: float | None = Field(None, ge=-180, le=180, examples=[36.817223])
    catchment_population: int = Field(0, ge=0, examples=[12000])


class CentreUpdate(BaseModel):
    name: str = Field(..., examples=["Hopital District 2"])
    level: str = Field(..., examples=["secondary"])
    specialities: list[str] = Field(..., examples=[["general", "maternal"]])
    capacity_max: int = Field(10, ge=0, examples=[10])
    capacity_available: int = Field(..., ge=0, examples=[4])
    estimated_wait_minutes: int = Field(..., ge=0, examples=[30])
    lat: float | None = Field(None, ge=-90, le=90, examples=[-1.286389])
    lon: float | None = Field(None, ge=-180, le=180, examples=[36.817223])
    catchment_population: int = Field(0, ge=0, examples=[12000])


class CentreResponse(BaseModel):
    id: str
    name: str
    level: str
    specialities: list[str]
    capacity_max: int
    capacity_available: int
    estimated_wait_minutes: int
    lat: float | None = None
    lon: float | None = None
    catchment_population: int = 0


class ReferenceCreate(BaseModel):
    source_id: str = Field(..., examples=["C_LOCAL_A"])
    dest_id: str = Field(..., examples=["H_DISTRICT_1"])
    travel_minutes: int = Field(..., gt=0, examples=[20])


class ReferenceUpdate(BaseModel):
    source_id: str = Field(..., examples=["C_LOCAL_A"])
    dest_id: str = Field(..., examples=["H_DISTRICT_1"])
    travel_minutes: int = Field(..., gt=0, examples=[20])


class ReferenceResponse(BaseModel):
    id: int
    source_id: str
    dest_id: str
    travel_minutes: int


class IndicatorResponse(BaseModel):
    country_code: str
    indicator_code: str
    indicator_name: str | None
    year: int
    value: float
    source_file: str | None
