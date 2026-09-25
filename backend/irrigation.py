"""Pure-Python Irrigation Advisory Engine for KrishiMitra.

Implements FAO-56 water balance modeling, Hargreaves reference evapotranspiration (ET0),
growth-stage crop coefficients (Kc), crop evapotranspiration (ETc), and moisture threshold evaluation.
Zero external dependencies, zero DB calls, zero API calls.
"""
from typing import Dict

# FAO-56 published crop coefficients (Kc) by growth stage (Initial, Mid, Late)
FAO56_CROP_COEFFICIENTS: Dict[str, Dict[str, float]] = {
    "rice": {"initial": 1.05, "mid": 1.20, "late": 0.90},
    "wheat": {"initial": 0.35, "mid": 1.15, "late": 0.40},
    "cotton": {"initial": 0.35, "mid": 1.20, "late": 0.60},
    "maize": {"initial": 0.30, "mid": 1.20, "late": 0.60},
    "chickpea": {"initial": 0.40, "mid": 1.00, "late": 0.35},
    "kidneybeans": {"initial": 0.40, "mid": 1.15, "late": 0.35},
    "pigeonpeas": {"initial": 0.40, "mid": 1.05, "late": 0.50},
    "mothbeans": {"initial": 0.35, "mid": 1.00, "late": 0.35},
    "mungbean": {"initial": 0.40, "mid": 1.05, "late": 0.35},
    "blackgram": {"initial": 0.40, "mid": 1.05, "late": 0.35},
    "lentil": {"initial": 0.40, "mid": 1.10, "late": 0.30},
    "pomegranate": {"initial": 0.50, "mid": 0.75, "late": 0.60},
    "banana": {"initial": 1.00, "mid": 1.20, "late": 1.10},
    "mango": {"initial": 0.60, "mid": 0.80, "late": 0.70},
    "grapes": {"initial": 0.30, "mid": 0.85, "late": 0.45},
    "watermelon": {"initial": 0.40, "mid": 1.00, "late": 0.75},
    "muskmelon": {"initial": 0.40, "mid": 1.00, "late": 0.75},
    "apple": {"initial": 0.45, "mid": 0.95, "late": 0.70},
    "orange": {"initial": 0.70, "mid": 0.65, "late": 0.70},
    "papaya": {"initial": 0.50, "mid": 1.00, "late": 0.85},
    "coconut": {"initial": 0.80, "mid": 1.00, "late": 0.90},
    "jute": {"initial": 0.40, "mid": 1.15, "late": 0.75},
    "coffee": {"initial": 0.90, "mid": 0.95, "late": 0.95},
}


def calculate_et0(
    temp_c: float,
    humidity_pct: float,
    solar_radiation_mm_day: float = 15.0,
    temp_range: float = 10.0,
) -> float:
    """Calculates reference evapotranspiration (ET0 in mm/day) via the Hargreaves method.

    Simplification note for Hackathon Scope:
    Standard FAO-56 Penman-Monteith requires net radiation, wind speed at 2m height, and psychrometric
    calculations requiring barometer/vapor pressure sensors rarely present on entry-level IoT sensor nodes.
    The Hargreaves-Samani model computes ET0 using mean temperature and extraterrestrial radiation (Ra):
        ET0_base = 0.0023 * Ra * (temp_c + 17.8) * sqrt(temp_range)
    where Ra defaults to 15.0 mm/day (representative for Indian sub-tropical latitudes 15-25 deg N)
    and diurnal temperature range defaults to 10.0 deg C.
    An atmospheric humidity attenuation factor (1.0 - humidity_pct / 200.0) is applied to scale ET0,
    as humid ambient air reduces vapor pressure deficit and transpiration.
    """
    temp_term = max(0.0, float(temp_c) + 17.8)
    td_term = max(0.0, float(temp_range)) ** 0.5
    base_et0 = 0.0023 * float(solar_radiation_mm_day) * temp_term * td_term

    # Attenuation factor: relative humidity reduces evaporative demand
    humidity_factor = max(0.1, 1.0 - (float(humidity_pct) / 200.0))
    et0 = base_et0 * humidity_factor
    return round(et0, 2)


def get_crop_coefficient(crop_name: str, growth_stage: str) -> float:
    """Looks up standard FAO-56 published crop coefficient (Kc).

    Args:
        crop_name: e.g. "Rice", "Wheat", "Cotton", "Maize" (case-insensitive)
        growth_stage: "initial", "mid", or "late" (case-insensitive)

    Returns:
        float: Crop coefficient Kc.

    Raises:
        ValueError: If crop or growth stage is not found in FAO-56 table.
    """
    crop_key = crop_name.lower().strip()
    stage_key = growth_stage.lower().strip()

    if crop_key not in FAO56_CROP_COEFFICIENTS:
        valid_crops = ", ".join(FAO56_CROP_COEFFICIENTS.keys())
        raise ValueError(f"Crop '{crop_name}' not in FAO-56 lookup table. Available: {valid_crops}")

    stages = FAO56_CROP_COEFFICIENTS[crop_key]
    if stage_key not in stages:
        valid_stages = ", ".join(stages.keys())
        raise ValueError(
            f"Stage '{growth_stage}' invalid for crop '{crop_name}'. Available: {valid_stages}"
        )

    return stages[stage_key]


def calculate_etc(et0: float, kc: float) -> float:
    """Calculates crop evapotranspiration ETc (mm/day) = ET0 * Kc."""
    return round(float(et0) * float(kc), 2)


def evaluate_irrigation_status(
    current_moisture: float,
    raw_threshold: float,
    field_capacity: float,
    etc: float,
    emitter_rate_mm_per_hr: float,
) -> Dict[str, float | str]:
    """Evaluates soil moisture status against Readily Available Water (RAW) thresholds.

    Threshold Logic:
    - CRITICAL_IRRIGATE: current_moisture <= raw_threshold.
      Soil water has dropped below allowable depletion.
      Water deficit (mm) = field_capacity - current_moisture.
      Pump runtime (hours) = deficit / emitter_rate_mm_per_hr.
    - MONITOR: current_moisture > raw_threshold, but (current_moisture - etc) <= raw_threshold.
      Moisture is currently adequate, but crop evapotranspiration will breach RAW within 24 hours.
      Pump runtime = 0.0.
    - OPTIMAL: current_moisture > raw_threshold and (current_moisture - etc) > raw_threshold.
      Soil moisture is comfortably above depletion threshold.
      Pump runtime = 0.0.

    Returns:
        dict: {
            "status": "CRITICAL_IRRIGATE" | "MONITOR" | "OPTIMAL",
            "deficit_mm": float,
            "pump_runtime_hours": float,
            "current_moisture": float,
            "raw_threshold": float,
            "field_capacity": float
        }
    """
    moisture = float(current_moisture)
    raw = float(raw_threshold)
    fc = float(field_capacity)
    daily_etc = float(etc)
    rate = float(emitter_rate_mm_per_hr)

    deficit = max(0.0, fc - moisture)

    if moisture <= raw:
        status = "CRITICAL_IRRIGATE"
        pump_runtime = round(deficit / rate, 2) if rate > 0 else 0.0
    elif (moisture - daily_etc) <= raw:
        status = "MONITOR"
        pump_runtime = 0.0
    else:
        status = "OPTIMAL"
        pump_runtime = 0.0

    return {
        "status": status,
        "deficit_mm": round(deficit, 2),
        "pump_runtime_hours": pump_runtime,
        "current_moisture": round(moisture, 2),
        "raw_threshold": round(raw, 2),
        "field_capacity": round(fc, 2),
    }
