"""Pure-Python Agronomic Intelligence Engine for KrishiMitra.

Handles stoichiometric NPK deficit calculations, commercial fertilizer unit
conversion (Urea, DAP, MOP), and pH remediation via lime or gypsum.
Zero external dependencies, zero DB calls, zero API calls.
"""
from typing import Dict


def calculate_npk_deficit(
    n_current: float,
    p_current: float,
    k_current: float,
    n_optimal: float,
    p_optimal: float,
    k_optimal: float,
) -> Dict[str, float]:
    """Calculates the elemental N, P, and K deficit (kg/ha or kg/acre).

    Returns:
        dict: {"n_deficit": float, "p_deficit": float, "k_deficit": float}
        If current nutrient exceeds or equals optimal, deficit is 0.0.
    """
    return {
        "n_deficit": max(0.0, float(n_optimal - n_current)),
        "p_deficit": max(0.0, float(p_optimal - p_current)),
        "k_deficit": max(0.0, float(k_optimal - k_current)),
    }


def calculate_fertilizer_prescription(
    n_deficit: float,
    p_deficit: float,
    k_deficit: float,
) -> Dict[str, float]:
    """Calculates commercial fertilizer quantities (kg/acre) from NPK deficits.

    Stoichiometry:
    1. DAP (Diammonium Phosphate) provides 46% P2O5 and 18% elemental N:
       dap_kg = p_deficit / 0.46
    2. Nitrogen provided by DAP is deducted from N deficit:
       net_n_deficit = max(0, n_deficit - (dap_kg * 0.18))
    3. Urea provides 46% elemental N:
       urea_kg = net_n_deficit / 0.46
    4. MOP (Muriate of Potash) provides 60% K2O:
       mop_kg = k_deficit / 0.60

    Returns:
        dict: {"dap_kg": float, "urea_kg": float, "mop_kg": float}
        All values rounded to 2 decimal places.
    """
    dap_kg = float(p_deficit) / 0.46 if p_deficit > 0 else 0.0
    net_n_deficit = max(0.0, float(n_deficit) - (dap_kg * 0.18))
    urea_kg = net_n_deficit / 0.46 if net_n_deficit > 0 else 0.0
    mop_kg = float(k_deficit) / 0.60 if k_deficit > 0 else 0.0

    return {
        "dap_kg": round(dap_kg, 2),
        "urea_kg": round(urea_kg, 2),
        "mop_kg": round(mop_kg, 2),
    }


def calculate_ph_remediation(ph: float) -> Dict[str, float]:
    """Calculates soil amendment requirements based on soil pH.

    Rules:
    - Acidic soil (ph < 6.0): Agricultural lime needed to raise pH toward 6.5.
      lime_kg = (6.5 - ph) * 250
    - Alkaline soil (ph > 7.5): Agricultural gypsum needed to lower pH toward 7.0.
      gypsum_kg = (ph - 7.0) * 300
    - Optimal soil (6.0 <= ph <= 7.5): No amendment needed (both 0.0).

    Returns:
        dict: {"lime_kg": float, "gypsum_kg": float} rounded to 2 decimal places.
    """
    ph_val = float(ph)
    lime_kg = 0.0
    gypsum_kg = 0.0

    if ph_val < 6.0:
        lime_kg = (6.5 - ph_val) * 250.0
    elif ph_val > 7.5:
        gypsum_kg = (ph_val - 7.0) * 300.0

    return {
        "lime_kg": round(lime_kg, 2),
        "gypsum_kg": round(gypsum_kg, 2),
    }
