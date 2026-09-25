"""Unit tests for KrishiMitra Irrigation Advisory Engine.

Validates Hargreaves ET0 reference evapotranspiration, FAO-56 crop coefficients,
crop evapotranspiration (ETc), and moisture threshold / pump runtime evaluations.
"""
try:
    import pytest
except ImportError:
    import contextlib

    class _PytestMock:
        @staticmethod
        @contextlib.contextmanager
        def raises(expected_exception, match=None):
            try:
                yield
            except expected_exception as e:
                if match and match not in str(e):
                    raise AssertionError(f"Expected match '{match}' not in '{e}'")
            else:
                raise AssertionError(f"Expected exception {expected_exception} was not raised")

    pytest = _PytestMock()
from backend.irrigation import (
    calculate_et0,
    calculate_etc,
    evaluate_irrigation_status,
    get_crop_coefficient,
)


def test_baseline_case_1_critical_irrigate():
    """Baseline Case 1: Moisture breaches RAW threshold triggering critical pump cycle.

    Manual Arithmetic:
    Crop: Rice (mid stage) -> Kc = 1.20

    ET0 Calculation:
    - temp_c = 28.0, humidity_pct = 60.0, solar_rad = 15.0, temp_range = 10.0
    - temp_term = 28.0 + 17.8 = 45.8
    - td_term = sqrt(10.0) = 3.16227766
    - base_et0 = 0.0023 * 15.0 * 45.8 * 3.16227766 = 4.996719...
    - humidity_factor = 1.0 - (60.0 / 200.0) = 0.70
    - et0 = round(4.996719... * 0.70, 2) = round(3.4977, 2) = 3.50 mm/day

    ETc Calculation:
    - etc = round(3.50 * 1.20, 2) = 4.20 mm/day

    Irrigation Status:
    - current_moisture = 18.0 mm
    - raw_threshold = 22.0 mm
    - field_capacity = 32.0 mm
    - emitter_rate = 4.0 mm/hr
    - Since current_moisture (18.0) <= raw_threshold (22.0) -> "CRITICAL_IRRIGATE"
    - Deficit = 32.0 - 18.0 = 14.0 mm
    - Pump runtime = 14.0 / 4.0 = 3.50 hours
    """
    kc = get_crop_coefficient("Rice", "mid")
    assert kc == 1.20

    et0 = calculate_et0(temp_c=28.0, humidity_pct=60.0, solar_radiation_mm_day=15.0, temp_range=10.0)
    assert et0 == 3.50

    etc = calculate_etc(et0, kc)
    assert etc == 4.20

    status_eval = evaluate_irrigation_status(
        current_moisture=18.0,
        raw_threshold=22.0,
        field_capacity=32.0,
        etc=etc,
        emitter_rate_mm_per_hr=4.0,
    )
    assert status_eval["status"] == "CRITICAL_IRRIGATE"
    assert status_eval["deficit_mm"] == 14.0
    assert status_eval["pump_runtime_hours"] == 3.50


def test_baseline_case_2_monitor_near_term_depletion():
    """Baseline Case 2: Current moisture is above RAW, but ETc will breach RAW within 24h.

    Manual Arithmetic:
    Crop: Wheat (mid stage) -> Kc = 1.15

    ET0 Calculation:
    - temp_c = 22.0, humidity_pct = 40.0, solar_rad = 15.0, temp_range = 10.0
    - temp_term = 22.0 + 17.8 = 39.8
    - td_term = sqrt(10.0) = 3.16227766
    - base_et0 = 0.0023 * 15.0 * 39.8 * 3.16227766 = 4.34216...
    - humidity_factor = 1.0 - (40.0 / 200.0) = 0.80
    - et0 = round(4.34216... * 0.80, 2) = round(3.4737, 2) = 3.47 mm/day

    ETc Calculation:
    - etc = round(3.47 * 1.15, 2) = round(3.9905, 2) = 3.99 mm/day

    Irrigation Status:
    - current_moisture = 24.0 mm
    - raw_threshold = 22.0 mm
    - field_capacity = 32.0 mm
    - emitter_rate = 4.0 mm/hr
    - Check 1: current_moisture (24.0) > raw_threshold (22.0) [not critical yet]
    - Check 2: (current_moisture - etc) = 24.0 - 3.99 = 20.01 mm <= raw_threshold (22.0) -> "MONITOR"
    - Deficit = 32.0 - 24.0 = 8.0 mm
    - Pump runtime = 0.0 hours (monitoring stage)
    """
    kc = get_crop_coefficient("Wheat", "mid")
    assert kc == 1.15

    et0 = calculate_et0(temp_c=22.0, humidity_pct=40.0, solar_radiation_mm_day=15.0, temp_range=10.0)
    assert et0 == 3.47

    etc = calculate_etc(et0, kc)
    assert etc == 3.99

    status_eval = evaluate_irrigation_status(
        current_moisture=24.0,
        raw_threshold=22.0,
        field_capacity=32.0,
        etc=etc,
        emitter_rate_mm_per_hr=4.0,
    )
    assert status_eval["status"] == "MONITOR"
    assert status_eval["deficit_mm"] == 8.0
    assert status_eval["pump_runtime_hours"] == 0.0


def test_baseline_case_3_optimal_moisture():
    """Baseline Case 3: Soil moisture is optimal and securely above RAW threshold.

    Manual Arithmetic:
    Crop: Cotton (late stage) -> Kc = 0.60

    ET0 Calculation:
    - temp_c = 25.0, humidity_pct = 50.0, solar_rad = 15.0, temp_range = 10.0
    - temp_term = 25.0 + 17.8 = 42.8
    - td_term = sqrt(10.0) = 3.16227766
    - base_et0 = 0.0023 * 15.0 * 42.8 * 3.16227766 = 4.66941...
    - humidity_factor = 1.0 - (50.0 / 200.0) = 0.75
    - et0 = round(4.66941... * 0.75, 2) = round(3.502, 2) = 3.50 mm/day

    ETc Calculation:
    - etc = round(3.50 * 0.60, 2) = 2.10 mm/day

    Irrigation Status:
    - current_moisture = 30.0 mm
    - raw_threshold = 22.0 mm
    - field_capacity = 32.0 mm
    - emitter_rate = 4.0 mm/hr
    - Check 1: 30.0 > 22.0
    - Check 2: 30.0 - 2.10 = 27.90 mm > 22.0 -> "OPTIMAL"
    - Deficit = 32.0 - 30.0 = 2.0 mm
    - Pump runtime = 0.0 hours
    """
    kc = get_crop_coefficient("Cotton", "late")
    assert kc == 0.60

    et0 = calculate_et0(temp_c=25.0, humidity_pct=50.0, solar_radiation_mm_day=15.0, temp_range=10.0)
    assert et0 == 3.50

    etc = calculate_etc(et0, kc)
    assert etc == 2.10

    status_eval = evaluate_irrigation_status(
        current_moisture=30.0,
        raw_threshold=22.0,
        field_capacity=32.0,
        etc=etc,
        emitter_rate_mm_per_hr=4.0,
    )
    assert status_eval["status"] == "OPTIMAL"
    assert status_eval["deficit_mm"] == 2.0
    assert status_eval["pump_runtime_hours"] == 0.0


def test_edge_cases_zero_deficit_and_exact_raw_boundary():
    """Edge Cases: Field capacity reached (zero deficit), exact RAW boundary, and invalid crop."""
    # 1. Soil at or exceeding field capacity (zero deficit)
    fc_status = evaluate_irrigation_status(
        current_moisture=35.0,
        raw_threshold=25.0,
        field_capacity=35.0,
        etc=3.0,
        emitter_rate_mm_per_hr=5.0,
    )
    assert fc_status["status"] == "OPTIMAL"
    assert fc_status["deficit_mm"] == 0.0
    assert fc_status["pump_runtime_hours"] == 0.0

    # 2. Moisture exactly at RAW boundary (22.0 == 22.0 -> triggers CRITICAL_IRRIGATE)
    boundary_status = evaluate_irrigation_status(
        current_moisture=22.0,
        raw_threshold=22.0,
        field_capacity=32.0,
        etc=4.0,
        emitter_rate_mm_per_hr=5.0,
    )
    assert boundary_status["status"] == "CRITICAL_IRRIGATE"
    # Deficit = 32.0 - 22.0 = 10.0 mm
    assert boundary_status["deficit_mm"] == 10.0
    # Pump runtime = 10.0 / 5.0 = 2.00 hours
    assert boundary_status["pump_runtime_hours"] == 2.00

    # 3. Invalid crop name or growth stage raises ValueError
    with pytest.raises(ValueError, match="not in FAO-56"):
        get_crop_coefficient("Dragonfruit", "mid")

    with pytest.raises(ValueError, match="invalid for crop"):
        get_crop_coefficient("Rice", "post-harvest")
