"""Unit tests for KrishiMitra Agronomic Intelligence Engine.

Validates NPK deficits, stoichiometric fertilizer dosing (DAP, Urea, MOP),
and pH remediation arithmetic against hand-calculated baselines.
"""
try:
    import pytest
except ImportError:
    pytest = None
from backend.agronomy import (
    calculate_fertilizer_prescription,
    calculate_npk_deficit,
    calculate_ph_remediation,
)


def test_baseline_case_1_standard_npk_deficit():
    """Baseline Case 1: Standard moderate N, P, and K deficit with acidic soil.

    Manual Arithmetic:
    Current: N=50, P=30, K=40
    Optimal: N=100, P=50, K=80
    - N Deficit = 100 - 50 = 50.0 kg/acre
    - P Deficit = 50 - 30 = 20.0 kg/acre
    - K Deficit = 80 - 40 = 40.0 kg/acre

    Fertilizer Prescription:
    - DAP (46% P2O5, 18% N):
      dap_kg = 20.0 / 0.46 = 43.47826... -> 43.48 kg
    - Nitrogen supplied by DAP:
      43.47826... * 0.18 = 7.82608... kg
    - Net N Deficit:
      50.0 - 7.82608... = 42.17391... kg
    - Urea (46% N):
      urea_kg = 42.17391... / 0.46 = 91.6824... -> 91.68 kg
    - MOP (60% K2O):
      mop_kg = 40.0 / 0.60 = 66.6666... -> 66.67 kg

    pH Remediation (pH = 5.2):
    - Acidic (5.2 < 6.0): lime_kg = (6.5 - 5.2) * 250 = 1.3 * 250 = 325.0 kg
    - gypsum_kg = 0.0 kg
    """
    # 1. Deficit check
    deficit = calculate_npk_deficit(
        n_current=50, p_current=30, k_current=40,
        n_optimal=100, p_optimal=50, k_optimal=80
    )
    assert deficit == {"n_deficit": 50.0, "p_deficit": 20.0, "k_deficit": 40.0}

    # 2. Fertilizer check
    fert = calculate_fertilizer_prescription(
        n_deficit=deficit["n_deficit"],
        p_deficit=deficit["p_deficit"],
        k_deficit=deficit["k_deficit"],
    )
    # Manual: dap = 43.48, urea = 91.68, mop = 66.67
    assert fert["dap_kg"] == 43.48
    assert fert["urea_kg"] == 91.68
    assert fert["mop_kg"] == 66.67

    # 3. pH check
    ph_res = calculate_ph_remediation(5.2)
    # Manual: lime = (6.5 - 5.2) * 250 = 325.0, gypsum = 0.0
    assert ph_res == {"lime_kg": 325.0, "gypsum_kg": 0.0}


def test_baseline_case_2_alkaline_soil_large_nitrogen():
    """Baseline Case 2: Alkaline soil with high Nitrogen and Potassium requirement.

    Manual Arithmetic:
    Current: N=40, P=20, K=30
    Optimal: N=120, P=66, K=90
    - N Deficit = 120 - 40 = 80.0 kg/acre
    - P Deficit = 66 - 20 = 46.0 kg/acre
    - K Deficit = 90 - 30 = 60.0 kg/acre

    Fertilizer Prescription:
    - DAP (46% P2O5, 18% N):
      dap_kg = 46.0 / 0.46 = 100.0 kg
    - Nitrogen supplied by DAP:
      100.0 * 0.18 = 18.0 kg
    - Net N Deficit:
      80.0 - 18.0 = 62.0 kg
    - Urea (46% N):
      urea_kg = 62.0 / 0.46 = 134.7826... -> 134.78 kg
    - MOP (60% K2O):
      mop_kg = 60.0 / 0.60 = 100.0 kg

    pH Remediation (pH = 8.2):
    - Alkaline (8.2 > 7.5): gypsum_kg = (8.2 - 7.0) * 300 = 1.2 * 300 = 360.0 kg
    - lime_kg = 0.0 kg
    """
    deficit = calculate_npk_deficit(
        n_current=40, p_current=20, k_current=30,
        n_optimal=120, p_optimal=66, k_optimal=90
    )
    assert deficit == {"n_deficit": 80.0, "p_deficit": 46.0, "k_deficit": 60.0}

    fert = calculate_fertilizer_prescription(
        n_deficit=80.0, p_deficit=46.0, k_deficit=60.0
    )
    # Manual: dap = 100.0, urea = 134.78, mop = 100.0
    assert fert["dap_kg"] == 100.0
    assert fert["urea_kg"] == 134.78
    assert fert["mop_kg"] == 100.0

    ph_res = calculate_ph_remediation(8.2)
    # Manual: lime = 0.0, gypsum = 360.0
    assert ph_res == {"lime_kg": 0.0, "gypsum_kg": 360.0}


def test_baseline_case_3_dap_nitrogen_oversupply_suppresses_urea():
    """Baseline Case 3: P deficit satisfies total N deficit (Urea clips to 0.0).

    Manual Arithmetic:
    Current: N=75, P=20, K=50
    Optimal: N=85, P=66, K=80
    - N Deficit = 85 - 75 = 10.0 kg/acre
    - P Deficit = 66 - 20 = 46.0 kg/acre
    - K Deficit = 80 - 50 = 30.0 kg/acre

    Fertilizer Prescription:
    - dap_kg = 46.0 / 0.46 = 100.0 kg
    - N supplied by DAP = 100.0 * 0.18 = 18.0 kg
    - Net N Deficit = max(0, 10.0 - 18.0) = 0.0 kg (DAP supplies more N than needed)
    - urea_kg = 0.0 / 0.46 = 0.0 kg
    - mop_kg = 30.0 / 0.60 = 50.0 kg

    pH Remediation (pH = 6.8):
    - Optimal (6.0 <= 6.8 <= 7.5): lime_kg = 0.0, gypsum_kg = 0.0
    """
    deficit = calculate_npk_deficit(
        n_current=75, p_current=20, k_current=50,
        n_optimal=85, p_optimal=66, k_optimal=80
    )
    assert deficit == {"n_deficit": 10.0, "p_deficit": 46.0, "k_deficit": 30.0}

    fert = calculate_fertilizer_prescription(
        n_deficit=10.0, p_deficit=46.0, k_deficit=30.0
    )
    # Manual: dap = 100.0, urea = 0.0, mop = 50.0
    assert fert["dap_kg"] == 100.0
    assert fert["urea_kg"] == 0.0
    assert fert["mop_kg"] == 50.0

    ph_res = calculate_ph_remediation(6.8)
    assert ph_res == {"lime_kg": 0.0, "gypsum_kg": 0.0}


def test_edge_cases_zero_deficit_and_ph_boundaries():
    """Edge Cases: Zero deficit / nutrient excess, and exact pH boundary points 6.0 and 7.5.

    Manual Arithmetic:
    Current: N=120, P=80, K=90
    Optimal: N=100, P=60, K=70
    - N Deficit = max(0, 100 - 120) = 0.0
    - P Deficit = max(0, 60 - 80) = 0.0
    - K Deficit = max(0, 70 - 90) = 0.0

    Fertilizer Prescription:
    - dap_kg = 0.0, urea_kg = 0.0, mop_kg = 0.0

    pH Boundaries:
    - At pH = 6.0: Not strictly < 6.0 and not > 7.5 -> lime_kg = 0.0, gypsum_kg = 0.0
    - At pH = 7.5: Not strictly < 6.0 and not > 7.5 -> lime_kg = 0.0, gypsum_kg = 0.0
    """
    # Nutrient excess returns 0.0 deficit
    deficit = calculate_npk_deficit(
        n_current=120, p_current=80, k_current=90,
        n_optimal=100, p_optimal=60, k_optimal=70
    )
    assert deficit == {"n_deficit": 0.0, "p_deficit": 0.0, "k_deficit": 0.0}

    fert = calculate_fertilizer_prescription(0.0, 0.0, 0.0)
    assert fert == {"dap_kg": 0.0, "urea_kg": 0.0, "mop_kg": 0.0}

    # Boundary tests for pH
    ph_boundary_low = calculate_ph_remediation(6.0)
    assert ph_boundary_low == {"lime_kg": 0.0, "gypsum_kg": 0.0}

    ph_boundary_high = calculate_ph_remediation(7.5)
    assert ph_boundary_high == {"lime_kg": 0.0, "gypsum_kg": 0.0}
