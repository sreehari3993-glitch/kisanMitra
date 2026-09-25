from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.irrigation import (
    calculate_et0,
    calculate_etc,
    evaluate_irrigation_status,
    get_crop_coefficient,
)
from backend.models import TelemetryLog
from backend.schemas import IrrigationAdvisoryResponse

router = APIRouter()


@router.get(
    "/irrigation-advisory",
    response_model=IrrigationAdvisoryResponse,
    summary="Compute FAO-56 irrigation recommendation and pump runtime",
)
def get_irrigation_advisory(
    telemetry_id: int = Query(..., description="ID of the telemetry log"),
    crop: str = Query(..., description="Crop name (e.g. Rice, Wheat, Cotton, Maize)"),
    growth_stage: str = Query(..., description="Growth stage: initial, mid, or late"),
    emitter_rate_mm_per_hr: float = Query(
        4.0, ge=0.1, description="Drip/sprinkler emitter application rate in mm/hr"
    ),
    raw_threshold: float = Query(
        22.0, ge=0.0, le=100.0, description="Readily Available Water moisture threshold %"
    ),
    field_capacity: float = Query(
        32.0, ge=0.0, le=100.0, description="Soil Field Capacity moisture %"
    ),
    db: Session = Depends(get_db),
):
    """Calculates reference evapotranspiration (ET0) via Hargreaves method, fetches the FAO-56

    crop coefficient (Kc), determines crop evapotranspiration (ETc), and computes pump runtime.
    """
    telemetry = (
        db.query(TelemetryLog).filter(TelemetryLog.id == telemetry_id).first()
    )
    if not telemetry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry record with id {telemetry_id} not found.",
        )

    # Validate crop and growth stage with FAO-56 lookup
    try:
        kc = get_crop_coefficient(crop_name=crop, growth_stage=growth_stage)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Reference evapotranspiration ET0
    et0 = calculate_et0(
        temp_c=telemetry.temperature,
        humidity_pct=telemetry.humidity,
    )

    # Crop evapotranspiration ETc
    etc = calculate_etc(et0=et0, kc=kc)

    # Evaluate moisture threshold and pump runtime
    status_eval = evaluate_irrigation_status(
        current_moisture=telemetry.moisture,
        raw_threshold=raw_threshold,
        field_capacity=field_capacity,
        etc=etc,
        emitter_rate_mm_per_hr=emitter_rate_mm_per_hr,
    )

    return IrrigationAdvisoryResponse(
        telemetry_id=telemetry.id,
        crop=crop,
        growth_stage=growth_stage,
        kc=kc,
        et0_mm_per_day=et0,
        etc_mm_per_day=etc,
        current_moisture=telemetry.moisture,
        raw_threshold=raw_threshold,
        field_capacity=field_capacity,
        status=str(status_eval["status"]),
        deficit_mm=float(status_eval["deficit_mm"]),
        pump_runtime_hours=float(status_eval["pump_runtime_hours"]),
    )
