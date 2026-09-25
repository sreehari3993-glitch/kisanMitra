from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.agronomy import (
    calculate_fertilizer_prescription,
    calculate_npk_deficit,
    calculate_ph_remediation,
)
from backend.database import get_db
from backend.ml_service import predict_top_crops
from backend.models import CropRecommendation, Prescription, TelemetryLog
from backend.schemas import (
    CropItem,
    CropRecommendationResponse,
    FertilizerPrescriptionRequest,
    FertilizerPrescriptionResponse,
    RecommendCropsRequest,
)

router = APIRouter()

# Standard agronomic reference targets (kg/ha) for crops
CROP_OPTIMAL_NPK: Dict[str, Dict[str, float]] = {
    "rice": {"n": 80.0, "p": 48.0, "k": 40.0},
    "maize": {"n": 78.0, "p": 48.0, "k": 20.0},
    "chickpea": {"n": 40.0, "p": 68.0, "k": 80.0},
    "kidneybeans": {"n": 21.0, "p": 67.0, "k": 20.0},
    "pigeonpeas": {"n": 21.0, "p": 68.0, "k": 20.0},
    "mothbeans": {"n": 21.0, "p": 48.0, "k": 20.0},
    "mungbean": {"n": 21.0, "p": 47.0, "k": 20.0},
    "blackgram": {"n": 40.0, "p": 67.0, "k": 19.0},
    "lentil": {"n": 19.0, "p": 68.0, "k": 19.0},
    "pomegranate": {"n": 19.0, "p": 19.0, "k": 40.0},
    "banana": {"n": 100.0, "p": 82.0, "k": 50.0},
    "mango": {"n": 20.0, "p": 27.0, "k": 30.0},
    "grapes": {"n": 23.0, "p": 133.0, "k": 201.0},
    "watermelon": {"n": 99.0, "p": 17.0, "k": 50.0},
    "muskmelon": {"n": 100.0, "p": 18.0, "k": 50.0},
    "apple": {"n": 21.0, "p": 134.0, "k": 200.0},
    "orange": {"n": 20.0, "p": 16.0, "k": 10.0},
    "papaya": {"n": 50.0, "p": 59.0, "k": 50.0},
    "coconut": {"n": 22.0, "p": 17.0, "k": 31.0},
    "cotton": {"n": 118.0, "p": 46.0, "k": 19.0},
    "jute": {"n": 78.0, "p": 46.0, "k": 40.0},
    "coffee": {"n": 101.0, "p": 29.0, "k": 30.0},
    "wheat": {"n": 120.0, "p": 60.0, "k": 40.0},
}


@router.post(
    "/recommend-crops",
    response_model=CropRecommendationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Predict top 3 recommended crops from telemetry",
)
def recommend_crops(payload: RecommendCropsRequest, db: Session = Depends(get_db)):
    """Loads the telemetry reading, invokes the Random Forest classifier to obtain the top-3

    recommended crops, and records the recommendation with secondary crops stored as JSON.
    """
    telemetry = (
        db.query(TelemetryLog).filter(TelemetryLog.id == payload.telemetry_id).first()
    )
    if not telemetry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Telemetry record with id {payload.telemetry_id} not found.",
        )

    try:
        recommendations = predict_top_crops(
            n=telemetry.n,
            p=telemetry.p,
            k=telemetry.k,
            ph=telemetry.ph,
            temp=telemetry.temperature,
            humidity=telemetry.humidity,
            rainfall=telemetry.rainfall,
            top_k=3,
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    top_crop = recommendations[0]["crop"]
    confidence = recommendations[0]["confidence"]
    secondary_crops = recommendations[1:]

    crop_rec = CropRecommendation(
        telemetry_id=telemetry.id,
        top_crop=top_crop,
        confidence=confidence,
        secondary_crops=secondary_crops,
    )
    db.add(crop_rec)
    db.commit()
    db.refresh(crop_rec)

    # Format response
    secondary_items = [
        CropItem(crop=item["crop"], confidence=item["confidence"])
        for item in secondary_crops
    ]

    return CropRecommendationResponse(
        recommendation_id=crop_rec.id,
        telemetry_id=crop_rec.telemetry_id,
        top_crop=crop_rec.top_crop,
        confidence=crop_rec.confidence,
        secondary_crops=secondary_items,
        created_at=crop_rec.created_at,
    )


@router.post(
    "/fertilizer-prescription",
    response_model=FertilizerPrescriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate stoichiometric fertilizer prescription for chosen crop",
)
def generate_fertilizer_prescription(
    payload: FertilizerPrescriptionRequest, db: Session = Depends(get_db)
):
    """Calculates fertilizer requirements (Urea, DAP, MOP) and soil remediation amendments

    (lime or gypsum) for the selected crop based on telemetry nutrient deficits.
    """
    rec = (
        db.query(CropRecommendation)
        .filter(CropRecommendation.id == payload.recommendation_id)
        .first()
    )
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation with id {payload.recommendation_id} not found.",
        )

    telemetry = (
        db.query(TelemetryLog).filter(TelemetryLog.id == rec.telemetry_id).first()
    )
    if not telemetry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Associated telemetry record with id {rec.telemetry_id} not found.",
        )

    # Look up optimal NPK for selected crop
    crop_name = payload.selected_crop.lower().strip()
    optimal = CROP_OPTIMAL_NPK.get(crop_name, {"n": 80.0, "p": 40.0, "k": 40.0})

    # Deficit calculation
    deficit = calculate_npk_deficit(
        n_current=telemetry.n,
        p_current=telemetry.p,
        k_current=telemetry.k,
        n_optimal=optimal["n"],
        p_optimal=optimal["p"],
        k_optimal=optimal["k"],
    )

    # Fertilizer prescription
    fert = calculate_fertilizer_prescription(
        n_deficit=deficit["n_deficit"],
        p_deficit=deficit["p_deficit"],
        k_deficit=deficit["k_deficit"],
    )

    # pH remediation
    remed = calculate_ph_remediation(telemetry.ph)

    # Persist Prescription row
    prescription = Prescription(
        recommendation_id=rec.id,
        urea_kg=fert["urea_kg"],
        dap_kg=fert["dap_kg"],
        mop_kg=fert["mop_kg"],
        lime_kg=remed["lime_kg"],
        gypsum_kg=remed["gypsum_kg"],
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    return FertilizerPrescriptionResponse(
        prescription_id=prescription.id,
        recommendation_id=prescription.recommendation_id,
        selected_crop=payload.selected_crop,
        urea_kg=prescription.urea_kg,
        dap_kg=prescription.dap_kg,
        mop_kg=prescription.mop_kg,
        lime_kg=prescription.lime_kg,
        gypsum_kg=prescription.gypsum_kg,
        created_at=prescription.created_at,
    )
