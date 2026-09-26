from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.agronomy import calculate_soil_health_index
from backend.database import get_db
from backend.models import TelemetryLog
from backend.schemas import (
    NutrientMetric,
    SoilHealthCardResponse,
    TelemetryCreate,
    TelemetryResponse,
)

router = APIRouter()


@router.post(
    "/telemetry",
    response_model=TelemetryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record incoming sensor telemetry",
)
def create_telemetry(payload: TelemetryCreate, db: Session = Depends(get_db)):
    """Persists a TelemetryLog row.

    Synchronous def route allows Starlette to execute database queries in the threadpool
    without blocking the async event loop.
    """
    telemetry_entry = TelemetryLog(
        machine_id=payload.machine_id,
        n=payload.n,
        p=payload.p,
        k=payload.k,
        ph=payload.ph,
        moisture=payload.moisture,
        temperature=payload.temperature,
        humidity=payload.humidity,
        rainfall=payload.rainfall,
    )
    db.add(telemetry_entry)
    db.commit()
    db.refresh(telemetry_entry)
    return telemetry_entry


@router.get(
    "/soil-health-card",
    response_model=SoilHealthCardResponse,
    summary="Compute soil health card and overall quality index",
)
def get_soil_health_card(
    telemetry_id: int = Query(..., description="ID of the telemetry log to evaluate"),
    db: Session = Depends(get_db),
):
    """Fetches a TelemetryLog record, evaluates individual nutrient statuses against

    standard agronomic benchmarks, and generates a composite 0-100 soil health index.
    """
    row = db.query(TelemetryLog).filter(TelemetryLog.id == telemetry_id).first()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry record with id {telemetry_id} not found.",
        )

    # 1. Nitrogen (N)
    if row.n < 50.0:
        n_status = "Low"
        n_score = max(0.0, (row.n / 50.0) * 100.0)
    elif row.n <= 100.0:
        n_status = "Adequate"
        n_score = 100.0
    else:
        n_status = "High"
        n_score = max(0.0, 100.0 - (row.n - 100.0) * 1.2)

    # 2. Phosphorus (P)
    if row.p < 30.0:
        p_status = "Low"
        p_score = max(0.0, (row.p / 30.0) * 100.0)
    elif row.p <= 60.0:
        p_status = "Adequate"
        p_score = 100.0
    else:
        p_status = "High"
        p_score = max(0.0, 100.0 - (row.p - 60.0) * 1.5)

    # 3. Potassium (K)
    if row.k < 40.0:
        k_status = "Low"
        k_score = max(0.0, (row.k / 40.0) * 100.0)
    elif row.k <= 80.0:
        k_status = "Adequate"
        k_score = 100.0
    else:
        k_status = "High"
        k_score = max(0.0, 100.0 - (row.k - 80.0) * 1.2)

    # 4. pH
    if row.ph < 6.0:
        ph_status = "Acidic"
        ph_score = max(0.0, 100.0 - (6.0 - row.ph) * 35.0)
    elif row.ph <= 7.5:
        ph_status = "Optimal"
        ph_score = 100.0
    else:
        ph_status = "Alkaline"
        ph_score = max(0.0, 100.0 - (row.ph - 7.5) * 35.0)

    # 5. Moisture
    if row.moisture < 20.0:
        moisture_status = "Low"
        moisture_score = max(0.0, (row.moisture / 20.0) * 100.0)
    elif row.moisture <= 35.0:
        moisture_status = "Adequate"
        moisture_score = 100.0
    else:
        moisture_status = "High"
        moisture_score = max(0.0, 100.0 - (row.moisture - 35.0) * 2.0)

    # Weighted composite index from unified agronomy intelligence engine
    health_index = calculate_soil_health_index(
        n=row.n, p=row.p, k=row.k, ph=row.ph, moisture=row.moisture
    )

    if health_index >= 80.0:
        rating = "Excellent"
    elif health_index >= 65.0:
        rating = "Good"
    elif health_index >= 50.0:
        rating = "Moderate"
    else:
        rating = "Poor"

    metrics: Dict[str, NutrientMetric] = {
        "nitrogen": NutrientMetric(
            name="Nitrogen (N)",
            value=round(row.n, 1),
            unit="kg/ha",
            status=n_status,
            optimal_range="50.0 - 100.0 kg/ha",
        ),
        "phosphorus": NutrientMetric(
            name="Phosphorus (P)",
            value=round(row.p, 1),
            unit="kg/ha",
            status=p_status,
            optimal_range="30.0 - 60.0 kg/ha",
        ),
        "potassium": NutrientMetric(
            name="Potassium (K)",
            value=round(row.k, 1),
            unit="kg/ha",
            status=k_status,
            optimal_range="40.0 - 80.0 kg/ha",
        ),
        "ph": NutrientMetric(
            name="Soil pH",
            value=round(row.ph, 2),
            unit="pH",
            status=ph_status,
            optimal_range="6.00 - 7.50",
        ),
        "moisture": NutrientMetric(
            name="Moisture",
            value=round(row.moisture, 1),
            unit="%",
            status=moisture_status,
            optimal_range="20.0 - 35.0 %",
        ),
    }

    return SoilHealthCardResponse(
        telemetry_id=row.id,
        machine_id=row.machine_id,
        timestamp=row.timestamp,
        soil_health_index=health_index,
        rating=rating,
        metrics=metrics,
    )
