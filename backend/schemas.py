from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------
# Telemetry & Soil Health Schemas
# ---------------------------------------------------------
class TelemetryCreate(BaseModel):
    """Payload for logging new telemetry readings."""
    machine_id: str = Field(..., max_length=64, description="Unique machine/sensor identifier")
    n: float = Field(..., description="Soil Nitrogen level (mg/kg or kg/ha)")
    p: float = Field(..., description="Soil Phosphorus level (mg/kg or kg/ha)")
    k: float = Field(..., description="Soil Potassium level (mg/kg or kg/ha)")
    ph: float = Field(..., ge=0.0, le=14.0, description="Soil pH value")
    moisture: float = Field(..., ge=0.0, le=100.0, description="Volumetric soil moisture percentage")
    temperature: float = Field(..., description="Ambient temperature in Celsius")
    humidity: float = Field(..., ge=0.0, le=100.0, description="Relative humidity percentage")
    rainfall: float = Field(..., ge=0.0, description="Rainfall in mm")


class TelemetryResponse(BaseModel):
    """Response returned upon persisting telemetry."""
    id: int
    machine_id: str
    timestamp: datetime
    n: float
    p: float
    k: float
    ph: float
    moisture: float
    temperature: float
    humidity: float
    rainfall: float

    model_config = ConfigDict(from_attributes=True)


class NutrientMetric(BaseModel):
    name: str
    value: float
    unit: str
    status: str  # "Low", "Adequate", "High", "Acidic", "Optimal", "Alkaline"
    optimal_range: str


class SoilHealthCardResponse(BaseModel):
    """Soil health card summary with individual metrics and composite index."""
    telemetry_id: int
    machine_id: str
    timestamp: datetime
    soil_health_index: float  # 0 to 100
    rating: str  # "Poor", "Moderate", "Good", "Excellent"
    metrics: Dict[str, NutrientMetric]


# ---------------------------------------------------------
# Crop Recommendation Schemas
# ---------------------------------------------------------
class RecommendCropsRequest(BaseModel):
    telemetry_id: int = Field(..., description="Foreign key ID of the telemetry log to evaluate")


class CropItem(BaseModel):
    crop: str
    confidence: float  # 0 - 100 percentage


class CropRecommendationResponse(BaseModel):
    recommendation_id: int
    telemetry_id: int
    top_crop: str
    confidence: float
    secondary_crops: List[CropItem]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Fertilizer Prescription Schemas
# ---------------------------------------------------------
class FertilizerPrescriptionRequest(BaseModel):
    recommendation_id: int = Field(..., description="Crop recommendation ID")
    selected_crop: str = Field(..., description="Crop chosen by the farmer")


class FertilizerPrescriptionResponse(BaseModel):
    prescription_id: int
    recommendation_id: int
    selected_crop: str
    urea_kg: float
    dap_kg: float
    mop_kg: float
    lime_kg: float
    gypsum_kg: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------
# Irrigation Advisory Schemas
# ---------------------------------------------------------
class IrrigationAdvisoryResponse(BaseModel):
    telemetry_id: int
    crop: str
    growth_stage: str
    kc: float
    et0_mm_per_day: float
    etc_mm_per_day: float
    current_moisture: float
    raw_threshold: float
    field_capacity: float
    status: str  # "CRITICAL_IRRIGATE" | "MONITOR" | "OPTIMAL"
    deficit_mm: float
    pump_runtime_hours: float


# ---------------------------------------------------------
# Kisan AI Copilot Schemas
# ---------------------------------------------------------
class KisanAIChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Farmer query or question")
    telemetry_id: Optional[int] = Field(None, description="Active telemetry log ID for real-time context")


class KisanAIChatResponse(BaseModel):
    answer: str
    language: str
    source: str  # "gemini" | "ollama" | "offline-kb"
    gdrive_folder: str
    gdrive_resources_folder: str = (
        "https://drive.google.com/drive/folders/1LdRwAKBybFYsijbMmOd2EdLRDqISTpI6?usp=drive_link"
    )

