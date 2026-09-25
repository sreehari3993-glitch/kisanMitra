from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
import numpy as np
import pandas as pd

# Module-level model bundle cache
_model_bundle: Optional[Dict[str, Any]] = None


def load_model(model_path: Optional[str | Path] = None) -> None:
    """Loads the serialized Random Forest model bundle into memory.

    Must be called exactly once during the FastAPI lifespan startup event — never per-request.
    """
    global _model_bundle
    if model_path is None:
        base_dir = Path(__file__).resolve().parent.parent
        model_path = base_dir / "ml" / "crop_rf_model.pkl"
    else:
        model_path = Path(model_path)

    if not model_path.exists():
        print(f"ML Service: Model artifact not found at '{model_path}'. Auto-training Random Forest model...")
        try:
            import subprocess
            import sys
            base_dir = Path(__file__).resolve().parent.parent
            train_script = base_dir / "ml" / "train_model.py"
            subprocess.run([sys.executable, str(train_script)], check=True, cwd=str(base_dir))
        except Exception as err:
            raise FileNotFoundError(
                f"Model artifact not found and auto-train failed: {err}. "
                "Please train the model manually by running: python ml/train_model.py"
            )

    _model_bundle = joblib.load(model_path)
    print(f"ML Service: Crop recommendation model successfully loaded from {model_path}")


def predict_top_crops(
    n: float,
    p: float,
    k: float,
    ph: float,
    temp: float,
    humidity: float,
    rainfall: float,
    top_k: int = 3,
) -> List[Dict[str, Any]]:
    """Predicts top_k crops given soil and climatic parameters.

    Returns:
        list[dict]: Sorted by probability descending:
            [{"crop": str, "confidence": float (0-100, 2 decimal places)}, ...]

    Raises:
        RuntimeError: If called before load_model() has executed.
    """
    global _model_bundle
    if _model_bundle is None:
        raise RuntimeError(
            "ML model has not been loaded. Call load_model() first during application startup."
        )

    model = _model_bundle["model"]
    label_encoder = _model_bundle["label_encoder"]
    feature_names = _model_bundle.get(
        "feature_names", ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    )

    # Feature mapping based on standard Kaggle crop dataset schema
    raw_inputs = {
        "N": float(n),
        "P": float(p),
        "K": float(k),
        "temperature": float(temp),
        "humidity": float(humidity),
        "ph": float(ph),
        "rainfall": float(rainfall),
    }

    # Build single-row DataFrame with the exact feature order the model was trained on
    ordered_values = [[raw_inputs[feat] for feat in feature_names]]
    input_df = pd.DataFrame(ordered_values, columns=feature_names)

    # Compute prediction probabilities
    probabilities = model.predict_proba(input_df)[0]

    # Sort indices by probability descending and pick top_k
    top_indices = np.argsort(probabilities)[::-1][:top_k]

    results: List[Dict[str, Any]] = []
    for idx in top_indices:
        crop_name = label_encoder.inverse_transform([idx])[0]
        confidence = round(float(probabilities[idx] * 100), 2)
        results.append({
            "crop": str(crop_name),
            "confidence": confidence,
        })

    return results
