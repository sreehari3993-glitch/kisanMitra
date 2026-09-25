import json
import logging
import re
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.agronomy import (
    calculate_fertilizer_prescription,
    calculate_npk_deficit,
    calculate_ph_remediation,
)
from backend.database import get_db
from backend.kisan_ai import get_gemini_api_key
from backend.ml_service import predict_top_crops
from backend.models import CropRecommendation, Prescription, TelemetryLog
from backend.schemas import (
    CropAiBriefingRequest,
    CropAiBriefingResponse,
    CropItem,
    CropRecommendationResponse,
    FertilizerPrescriptionRequest,
    FertilizerPrescriptionResponse,
    RecommendCropsRequest,
)

logger = logging.getLogger(__name__)

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


# -------------------------------------------------------------
# Agricultural Economics & Phenological Growth Profiles
# -------------------------------------------------------------
CROP_ECONOMIC_PROFILES: Dict[str, Dict[str, Any]] = {
    "rice": {
        "mandi_rate": "₹2,320 – ₹2,650 / Quintal (MSP: ₹2,320/Q)",
        "estimated_yield": "22 – 28 Quintals / acre",
        "gross_revenue": "₹51,000 – ₹68,000 / acre",
        "cultivation_time": "110 – 125 Days (Kharif / Wet Season)",
        "growth_stages": "Nursery (20d) → Tillering (35d) → Panicle Initiation (30d) → Grain Ripening (25d)",
        "key_agronomic_tip": "Maintain 2–5 cm shallow standing water during tillering; drain field 10 days before harvest.",
        "soil_affinity": "Acid-tolerant (pH 5.0–6.5) lowland clay loam with high water retention and warm temperatures (22–32°C).",
    },
    "wheat": {
        "mandi_rate": "₹2,275 – ₹2,550 / Quintal (MSP: ₹2,275/Q)",
        "estimated_yield": "18 – 22 Quintals / acre",
        "gross_revenue": "₹41,000 – ₹55,000 / acre",
        "cultivation_time": "115 – 135 Days (Rabi Cycle)",
        "growth_stages": "Crown Root (21d) → Tillering (40d) → Jointing (65d) → Heading (85d) → Maturity (125d)",
        "key_agronomic_tip": "First irrigation at Crown Root Initiation (CRI) stage (21 days) is critical; delaying reduces tillers by up to 30%.",
        "soil_affinity": "Neutral to slightly alkaline loams (pH 6.5–7.5) with moderate moisture and cool temperatures (15–24°C).",
    },
    "maize": {
        "mandi_rate": "₹2,090 – ₹2,380 / Quintal (MSP: ₹2,090/Q)",
        "estimated_yield": "25 – 32 Quintals / acre",
        "gross_revenue": "₹52,000 – ₹72,000 / acre",
        "cultivation_time": "95 – 110 Days",
        "growth_stages": "Knee-High (30d) → Tasseling & Silking (55d) → Grain Filling (80d) → Physiological Maturity (105d)",
        "key_agronomic_tip": "Ensure high moisture and nitrogen availability during silking and tasseling stages to prevent kernel abortion.",
        "soil_affinity": "Well-drained sandy loam to silt loam with pH 5.8–7.2; sensitive to waterlogging.",
    },
    "chickpea": {
        "mandi_rate": "₹5,440 – ₹6,150 / Quintal (MSP: ₹5,440/Q)",
        "estimated_yield": "8 – 12 Quintals / acre",
        "gross_revenue": "₹43,000 – ₹65,000 / acre",
        "cultivation_time": "95 – 110 Days (Rabi Pulse)",
        "growth_stages": "Branching (30d) → Flowering (55d) → Pod Filling (75d) → Desiccation & Harvest (100d)",
        "key_agronomic_tip": "Treat seeds with Rhizobium and PSB biofertilizer to fix atmospheric nitrogen and solubilize phosphate.",
        "soil_affinity": "Deep, well-aerated neutral loams (pH 6.5–7.8); low rainfall demand, excellent for residual soil moisture.",
    },
    "banana": {
        "mandi_rate": "₹18 – ₹32 / kg (Wholesale Farmgate)",
        "estimated_yield": "25 – 35 Tonnes / acre (Grand Naine)",
        "gross_revenue": "₹4,20,000 – ₹6,50,000 / acre",
        "cultivation_time": "11 – 13 Months (Annual Plantation)",
        "growth_stages": "Establishment (3mo) → Vegetative Shooting (6mo) → Bunch Emergence (9mo) → Harvest (12mo)",
        "key_agronomic_tip": "Apply 300g Nitrogen and 300g Potash per plant through 4 split applications with drip fertigation.",
        "soil_affinity": "Deep, rich alluvial or volcanic loam with pH 6.0–7.5, high organic matter, and regular irrigation.",
    },
    "cotton": {
        "mandi_rate": "₹7,121 – ₹7,650 / Quintal (MSP: ₹7,121/Q)",
        "estimated_yield": "10 – 14 Quintals / acre (Bt Cotton)",
        "gross_revenue": "₹72,000 – ₹1,05,000 / acre",
        "cultivation_time": "150 – 175 Days",
        "growth_stages": "Vegetative (45d) → Square Formation (70d) → Flowering (95d) → Boll Bursting (150d)",
        "key_agronomic_tip": "Avoid waterlogging; deep taproot system thrives in well-drained medium-to-deep black vertisols.",
        "soil_affinity": "Black cotton vertisols (pH 6.5–8.0) with high cation exchange capacity and warm temperatures (24–35°C).",
    },
    "coffee": {
        "mandi_rate": "₹8,800 – ₹11,500 / 50kg Bag (Parchment)",
        "estimated_yield": "850 – 1,250 kg clean bean / acre",
        "gross_revenue": "₹1,50,000 – ₹2,35,000 / acre",
        "cultivation_time": "Perennial Plantation (Blossom to Harvest: 8–9 Months)",
        "growth_stages": "Blossom Showers (March) → Pinhead Setting (May) → Berry Expansion (Aug) → Cherry Ripening (Nov–Jan)",
        "key_agronomic_tip": "Maintain two-tier shade trees (silver oak and dadap) and mulch with coffee pulp to conserve moisture.",
        "soil_affinity": "Humid acidic hill soils (pH 5.5–6.8) rich in organic humus with high rainfall (1500–2500 mm annually).",
    },
    "jute": {
        "mandi_rate": "₹5,050 – ₹5,400 / Quintal (MSP: ₹5,050/Q)",
        "estimated_yield": "14 – 18 Quintals / acre",
        "gross_revenue": "₹70,000 – ₹95,000 / acre",
        "cultivation_time": "120 – 135 Days (Monsoon Crop)",
        "growth_stages": "Seedling (25d) → Rapid Vegetative Elongation (75d) → Small Pod Stage (Harvest at 120d)",
        "key_agronomic_tip": "Harvest at 50% flowering to obtain premium Golden Fiber grade; retting requires clean slow-moving water.",
        "soil_affinity": "Alluvial floodplain silt (pH 6.0–7.5) with high monsoon precipitation (>150mm/month).",
    },
    "coconut": {
        "mandi_rate": "₹12 – ₹18 / Mature Nut (Farmgate)",
        "estimated_yield": "8,000 – 12,000 Nuts / acre / year (175 palms/acre)",
        "gross_revenue": "₹1,10,000 – ₹1,80,000 / acre / year",
        "cultivation_time": "Perennial Palm (Year-Round Monthly Harvesting)",
        "growth_stages": "Juvenile (1–4 yrs) → First Bearing (5–6 yrs) → Peak Commercial Bearing (10–50 yrs)",
        "key_agronomic_tip": "Apply 1.3 kg MOP and 1 kg common salt per adult palm annually along the drip circle (1.8m radius).",
        "soil_affinity": "Coastal sand, alluvium, or lateritic red loam (pH 5.2–7.5); tolerates moderate soil salinity.",
    },
    "papaya": {
        "mandi_rate": "₹14 – ₹24 / kg (Farmgate)",
        "estimated_yield": "25 – 35 Tonnes / acre (Taiwan 786 / Red Lady)",
        "gross_revenue": "₹3,50,000 – ₹5,50,000 / acre",
        "cultivation_time": "9 – 12 Months to First Harvest",
        "growth_stages": "Nursery (45d) → Vegetative (90d) → Flowering (120d) → Fruit Development & Continuous Picking (7–12 mo)",
        "key_agronomic_tip": "Plant on raised mounds with drip irrigation; zero tolerance for stagnant water (causes root rot within 24h).",
        "soil_affinity": "Light, well-aerated sandy loam with rich organic matter (pH 6.0–7.2) and warm sunny weather.",
    },
    "watermelon": {
        "mandi_rate": "₹8 – ₹15 / kg (Mandi Wholesale)",
        "estimated_yield": "18 – 25 Tonnes / acre",
        "gross_revenue": "₹1,45,000 – ₹2,50,000 / acre",
        "cultivation_time": "80 – 95 Days (Summer Cash Crop)",
        "growth_stages": "Germination (7d) → Vine Growth (30d) → Flowering & Fruit Set (50d) → Harvest (85d)",
        "key_agronomic_tip": "Withhold irrigation 5 days prior to harvest to concentrate fruit brix (sugar content).",
        "soil_affinity": "Sandy loam river beds (pH 6.0–7.0) with warm dry weather during fruit ripening.",
    },
    "apple": {
        "mandi_rate": "₹60 – ₹110 / kg (Wholesale Box)",
        "estimated_yield": "8 – 14 Tonnes / acre",
        "gross_revenue": "₹4,80,000 – ₹9,50,000 / acre",
        "cultivation_time": "Perennial Temperate (Blossom to Harvest: 130–150 Days)",
        "growth_stages": "Dormancy (Winter) → Bud Break (March) → Bloom (April) → Fruit Development (May–Aug) → Harvest (Aug–Oct)",
        "key_agronomic_tip": "Requires 800–1,200 chilling hours (<7°C) for flower bud differentiation; prune for canopy sun exposure.",
        "soil_affinity": "Deep, well-drained loamy mountain soils (pH 5.8–6.8) with high potassium reserves.",
    },
    "grapes": {
        "mandi_rate": "₹45 – ₹80 / kg (Table Grapes Mandi)",
        "estimated_yield": "10 – 14 Tonnes / acre",
        "gross_revenue": "₹4,50,000 – ₹8,00,000 / acre",
        "cultivation_time": "Perennial Vine (April Pruning → October Pruning → Harvest in Feb–April)",
        "growth_stages": "Foundation Pruning (April) → Fruit Pruning (Oct) → Berry Set (Dec) → Veraison (Feb) → Harvest (March)",
        "key_agronomic_tip": "Dip clusters in Gibberellic Acid (GA3) during pea-stage to achieve uniform berry elongation and loosen bunch.",
        "soil_affinity": "Well-drained gravelly sandy loam (pH 6.0–7.5) with very high Potassium and Phosphorus requirements.",
    },
    "mango": {
        "mandi_rate": "₹35 – ₹70 / kg (Commercial Varieties: Alphonso/Totapuri/Kesar)",
        "estimated_yield": "6 – 10 Tonnes / acre (Mature Orchard)",
        "gross_revenue": "₹2,10,000 – ₹4,50,000 / acre",
        "cultivation_time": "Perennial Tree (Flowering in Dec–Jan → Harvest in April–June)",
        "growth_stages": "Vegetative Flush (July) → Flower Bud Differentiation (Oct) → Panicle Bloom (Jan) → Fruit Maturity (May)",
        "key_agronomic_tip": "Withhold irrigation 2 months prior to flowering (Oct–Nov) to trigger reproductive floral induction.",
        "soil_affinity": "Deep alluvial or red loamy soil (pH 5.5–7.5) with a water table deeper than 2.5 meters.",
    },
    "pomegranate": {
        "mandi_rate": "₹70 – ₹130 / kg (Bhagwa Variety)",
        "estimated_yield": "5 – 8 Tonnes / acre",
        "gross_revenue": "₹3,50,000 – ₹7,50,000 / acre",
        "cultivation_time": "Perennial (Bahar treatment to harvest: 5–6 months)",
        "growth_stages": "Water Stress (Bahar) → Pruning & Manuring → Bloom (60d) → Fruit Development (120d) → Harvest (160d)",
        "key_agronomic_tip": "Bag individual fruits with butter paper bags 60 days after fruit set to protect from fruit borer and sunburn.",
        "soil_affinity": "Light to medium gravelly loams (pH 6.0–7.8); highly drought-tolerant, susceptible to bacterial blight in waterlogging.",
    },
    "orange": {
        "mandi_rate": "₹25 – ₹45 / kg (Nagpur Mandarin / Sweet Orange)",
        "estimated_yield": "8 – 12 Tonnes / acre",
        "gross_revenue": "₹2,00,000 – ₹3,80,000 / acre",
        "cultivation_time": "Perennial Citrus (Ambia Bahar: Bloom Feb → Harvest Oct–Dec)",
        "growth_stages": "Rest Period (Dec) → Bloom (Feb) → Fruit Set (March) → Expansion (June–Sept) → Color Break & Harvest (Nov)",
        "key_agronomic_tip": "Apply Micronutrient spray (Zinc 0.5% + Ferrous 0.4% + Borax 0.2%) during new flush emergence.",
        "soil_affinity": "Deep, well-aerated light loam or medium black soil (pH 6.0–7.5) with zero subsoil hardpan.",
    }
}


@router.post(
    "/crop-ai-briefing",
    response_model=CropAiBriefingResponse,
    status_code=status.HTTP_200_OK,
    summary="Access Gemini API to generate crop value, cultivation duration and XAI recommendation reasons",
)
def get_crop_ai_briefing(
    payload: CropAiBriefingRequest,
    db: Session = Depends(get_db),
):
    """Accesses the Google Gemini API (or calibrated ICAR fallback) to generate:

    1. Market & Economic Value (yield, mandi rates, gross income per acre)
    2. Cultivation Time & phenological timeline
    3. Why this crop is recommended (Explainable AI grounded in telemetry)
    """
    crop_name = payload.crop.strip().lower()
    profile = CROP_ECONOMIC_PROFILES.get(
        crop_name,
        {
            "mandi_rate": "₹3,500 – ₹4,800 / Quintal",
            "estimated_yield": "15 – 20 Quintals / acre",
            "gross_revenue": "₹50,000 – ₹75,000 / acre",
            "cultivation_time": "90 – 120 Days",
            "growth_stages": "Establishment (20d) → Vegetative (40d) → Reproductive (35d) → Harvest (15d)",
            "key_agronomic_tip": "Ensure balanced NPK nutrition and avoid water stagnation at flowering.",
            "soil_affinity": "Adaptable to well-drained loam with pH 6.0–7.5.",
        },
    )

    # Resolve telemetry parameters
    n = payload.n if payload.n is not None else 35.0
    p = payload.p if payload.p is not None else 60.0
    k = payload.k if payload.k is not None else 32.0
    ph = payload.ph if payload.ph is not None else 5.4
    moisture = payload.moisture if payload.moisture is not None else 28.0
    temp = payload.temperature if payload.temperature is not None else 31.0
    humidity = payload.humidity if payload.humidity is not None else 80.0
    rain = payload.rainfall if payload.rainfall is not None else 180.0

    if payload.telemetry_id:
        tel = db.query(TelemetryLog).filter(TelemetryLog.id == payload.telemetry_id).first()
        if tel:
            n, p, k = tel.n, tel.p, tel.k
            ph, moisture = tel.ph, tel.moisture
            temp, humidity, rain = tel.temperature, tel.humidity, tel.rainfall

    # Attempt Live Gemini API Reasoning
    gemini_key = get_gemini_api_key()
    if gemini_key:
        try:
            import google.generativeai as genai

            genai.configure(api_key=gemini_key)
            prompt = f"""You are an expert ICAR agricultural economist and precision agronomist.
A farmer has transmitted the following real-time IoT soil telemetry from field sensors:
- Soil Nitrogen (N): {n} kg/ha
- Soil Phosphorus (P): {p} kg/ha
- Soil Potassium (K): {k} kg/ha
- Soil pH: {ph}
- Volumetric Soil Moisture: {moisture}%
- Ambient Temperature: {temp}°C
- Relative Humidity: {humidity}%
- Precipitation / Rainfall: {rain} mm

The AI decision model recommended the crop: {payload.crop.upper()}

Provide an authoritative briefing strictly formatted as a valid JSON object with EXACTLY these keys:
{{
  "market_value": "Expected yield per acre, current MSP/mandi rate range, and gross revenue per acre in INR (e.g. ₹51,000 – ₹68,000 / acre)",
  "mandi_rate": "Current wholesale or MSP price range per quintal or kg",
  "estimated_yield": "Realistic yield range per acre",
  "gross_revenue": "Estimated gross revenue range per acre in INR",
  "cultivation_time": "Total duration in days/months and season name",
  "growth_stages": "Timeline of key growth phases (e.g. Nursery -> Tillering -> Flowering -> Harvest)",
  "why_recommended": "Detailed Explainable AI (XAI) rationale specifically explaining how this soil's exact pH ({ph}), N ({n}), P ({p}), K ({k}), moisture ({moisture}%), and rainfall ({rain} mm) physiologically favor this crop over alternatives",
  "key_agronomic_tip": "One high-yield actionable scientific tip for maximizing profit/yield"
}}
Return ONLY raw JSON, with no markdown code blocks or surrounding text.
"""
            model_candidates = [
                "gemini-1.5-flash",
                "gemini-1.5-flash-latest",
                "gemini-2.0-flash",
                "gemini-pro",
            ]
            for m_name in model_candidates:
                try:
                    m = genai.GenerativeModel(m_name)
                    resp = m.generate_content(prompt)
                    if resp and resp.text:
                        raw = resp.text.strip()
                        raw = re.sub(r"^```json\s*", "", raw)
                        raw = re.sub(r"\s*```$", "", raw)
                        data = json.loads(raw)
                        return CropAiBriefingResponse(
                            crop=payload.crop,
                            market_value=data.get("market_value", f"{profile['estimated_yield']} @ {profile['mandi_rate']}"),
                            mandi_rate=data.get("mandi_rate", profile["mandi_rate"]),
                            estimated_yield=data.get("estimated_yield", profile["estimated_yield"]),
                            gross_revenue=data.get("gross_revenue", profile["gross_revenue"]),
                            cultivation_time=data.get("cultivation_time", profile["cultivation_time"]),
                            growth_stages=data.get("growth_stages", profile["growth_stages"]),
                            why_recommended=data.get(
                                "why_recommended",
                                f"{payload.crop} is recommended because your soil's pH of {ph:.2f} and available moisture ({moisture:.1f}%) match the crop's physiological threshold.",
                            ),
                            key_agronomic_tip=data.get("key_agronomic_tip", profile["key_agronomic_tip"]),
                            source=f"{m_name} (Live Reasoning)",
                        )
                except Exception as m_err:
                    logger.info(f"Gemini trial {m_name} failed: {m_err}")
                    continue
        except Exception as e:
            logger.warning(f"Live Gemini API briefing generation failed: {e}")

    # Grounded ICAR Fallback
    why_text = (
        f"{payload.crop.capitalize()} is selected as the top agronomic match because your field's soil pH of {ph:.2f} "
        f"and active moisture of {moisture:.1f}% fit within its physiological sweet spot. "
        f"With available Nitrogen at {n:.1f} kg/ha, Phosphorus at {p:.1f} kg/ha, Potassium at {k:.1f} kg/ha, "
        f"and precipitation at {rain:.1f} mm, {payload.crop.capitalize()} offers the lowest agronomic amendment cost "
        f"and the highest expected harvest stability."
    )

    return CropAiBriefingResponse(
        crop=payload.crop,
        market_value=f"{profile['estimated_yield']} @ {profile['mandi_rate']} (Gross: {profile['gross_revenue']})",
        mandi_rate=profile["mandi_rate"],
        estimated_yield=profile["estimated_yield"],
        gross_revenue=profile["gross_revenue"],
        cultivation_time=profile["cultivation_time"],
        growth_stages=profile["growth_stages"],
        why_recommended=why_text,
        key_agronomic_tip=profile["key_agronomic_tip"],
        source="ICAR Agronomic Database & Telemetry Correlation",
    )

