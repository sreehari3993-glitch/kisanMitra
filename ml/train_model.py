import os
import sys
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelEncoder

ML_DIR = Path(__file__).resolve().parent
DATASET_PATH = ML_DIR / "dataset.csv"
MODEL_OUTPUT_PATH = ML_DIR / "crop_rf_model.pkl"

FEATURE_NAMES = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]

# Agronomic reference parameters (mean, std) grounded in ICAR and Nature Scientific Reports 2025
SYNTHETIC_CROP_PROFILES = {
    # 22 Benchmark Kaggle + ICAR Crops
    "rice": {"N": (80, 10), "P": (48, 8), "K": (40, 5), "temperature": (24, 2), "humidity": (82, 5), "ph": (6.4, 0.4), "rainfall": (236, 25)},
    "wheat": {"N": (100, 12), "P": (45, 6), "K": (40, 5), "temperature": (20, 2), "humidity": (55, 6), "ph": (6.8, 0.4), "rainfall": (60, 10)},
    "maize": {"N": (78, 10), "P": (48, 8), "K": (20, 4), "temperature": (22, 3), "humidity": (65, 8), "ph": (6.2, 0.5), "rainfall": (65, 12)},
    "chickpea": {"N": (40, 6), "P": (68, 7), "K": (80, 6), "temperature": (19, 2), "humidity": (17, 3), "ph": (7.3, 0.4), "rainfall": (80, 10)},
    "kidneybeans": {"N": (21, 5), "P": (67, 6), "K": (20, 3), "temperature": (20, 3), "humidity": (22, 4), "ph": (5.7, 0.3), "rainfall": (106, 15)},
    "pigeonpeas": {"N": (21, 5), "P": (68, 7), "K": (20, 4), "temperature": (28, 3), "humidity": (48, 6), "ph": (5.7, 0.4), "rainfall": (150, 20)},
    "mothbeans": {"N": (21, 5), "P": (48, 5), "K": (20, 3), "temperature": (28, 2), "humidity": (53, 5), "ph": (6.8, 0.4), "rainfall": (51, 8)},
    "mungbean": {"N": (21, 4), "P": (47, 5), "K": (20, 3), "temperature": (28, 2), "humidity": (85, 4), "ph": (6.7, 0.4), "rainfall": (48, 7)},
    "blackgram": {"N": (40, 6), "P": (67, 6), "K": (19, 3), "temperature": (30, 2), "humidity": (65, 5), "ph": (7.1, 0.3), "rainfall": (68, 9)},
    "lentil": {"N": (19, 4), "P": (68, 6), "K": (19, 3), "temperature": (25, 3), "humidity": (65, 6), "ph": (6.9, 0.4), "rainfall": (46, 6)},
    "pomegranate": {"N": (19, 4), "P": (19, 4), "K": (40, 5), "temperature": (22, 3), "humidity": (90, 4), "ph": (6.4, 0.4), "rainfall": (108, 12)},
    "banana": {"N": (100, 8), "P": (82, 7), "K": (50, 5), "temperature": (27, 2), "humidity": (80, 5), "ph": (6.0, 0.4), "rainfall": (105, 15)},
    "mango": {"N": (20, 4), "P": (27, 5), "K": (30, 4), "temperature": (31, 2), "humidity": (50, 6), "ph": (5.8, 0.4), "rainfall": (95, 12)},
    "grapes": {"N": (23, 4), "P": (133, 10), "K": (201, 10), "temperature": (24, 3), "humidity": (82, 4), "ph": (6.0, 0.3), "rainfall": (70, 8)},
    "watermelon": {"N": (99, 9), "P": (17, 3), "K": (50, 5), "temperature": (26, 2), "humidity": (85, 4), "ph": (6.5, 0.3), "rainfall": (51, 8)},
    "muskmelon": {"N": (100, 8), "P": (18, 3), "K": (50, 4), "temperature": (29, 2), "humidity": (92, 3), "ph": (6.4, 0.3), "rainfall": (25, 4)},
    "apple": {"N": (21, 4), "P": (134, 9), "K": (200, 10), "temperature": (23, 2), "humidity": (92, 3), "ph": (5.9, 0.3), "rainfall": (113, 12)},
    "orange": {"N": (20, 4), "P": (16, 3), "K": (10, 2), "temperature": (23, 3), "humidity": (92, 3), "ph": (7.0, 0.3), "rainfall": (110, 12)},
    "papaya": {"N": (50, 7), "P": (59, 6), "K": (50, 5), "temperature": (34, 2), "humidity": (92, 3), "ph": (6.7, 0.3), "rainfall": (143, 15)},
    "coconut": {"N": (22, 4), "P": (17, 3), "K": (31, 4), "temperature": (27, 2), "humidity": (95, 2), "ph": (6.0, 0.3), "rainfall": (176, 18)},
    "cotton": {"N": (118, 10), "P": (46, 5), "K": (19, 3), "temperature": (24, 2), "humidity": (80, 4), "ph": (6.8, 0.3), "rainfall": (80, 10)},
    "jute": {"N": (78, 8), "P": (46, 5), "K": (40, 4), "temperature": (25, 2), "humidity": (80, 4), "ph": (6.7, 0.3), "rainfall": (175, 18)},
    "coffee": {"N": (101, 9), "P": (29, 4), "K": (30, 4), "temperature": (26, 2), "humidity": (58, 5), "ph": (6.8, 0.4), "rainfall": (158, 16)},
    # Additional Regional Crops from Western Maharashtra & IRJIET Research Papers
    "bajra": {"N": (65, 8), "P": (30, 5), "K": (25, 4), "temperature": (30, 3), "humidity": (50, 6), "ph": (7.2, 0.4), "rainfall": (50, 8)},
    "jowar": {"N": (70, 8), "P": (35, 5), "K": (30, 4), "temperature": (29, 2), "humidity": (52, 6), "ph": (7.0, 0.4), "rainfall": (60, 10)},
    "groundnut": {"N": (25, 4), "P": (50, 6), "K": (25, 4), "temperature": (28, 2), "humidity": (60, 5), "ph": (6.5, 0.4), "rainfall": (75, 10)},
    "onion": {"N": (110, 10), "P": (50, 6), "K": (60, 6), "temperature": (22, 2), "humidity": (65, 5), "ph": (6.6, 0.3), "rainfall": (70, 8)},
    "tomato": {"N": (90, 8), "P": (60, 6), "K": (70, 6), "temperature": (24, 2), "humidity": (68, 5), "ph": (6.5, 0.3), "rainfall": (80, 10)},
    "sugarcane": {"N": (135, 12), "P": (60, 7), "K": (70, 6), "temperature": (30, 2), "humidity": (78, 4), "ph": (7.0, 0.3), "rainfall": (200, 20)},
}


def generate_synthetic_dataset(output_path: Path, samples_per_crop: int = 100) -> pd.DataFrame:
    """Generates synthetic dataset matching the Kaggle and Nature 2025 benchmark schema."""
    rng = np.random.default_rng(seed=42)
    rows = []

    for crop, params in SYNTHETIC_CROP_PROFILES.items():
        for _ in range(samples_per_crop):
            row = {
                "N": max(0.0, float(rng.normal(params["N"][0], params["N"][1]))),
                "P": max(0.0, float(rng.normal(params["P"][0], params["P"][1]))),
                "K": max(0.0, float(rng.normal(params["K"][0], params["K"][1]))),
                "temperature": float(rng.normal(params["temperature"][0], params["temperature"][1])),
                "humidity": min(100.0, max(0.0, float(rng.normal(params["humidity"][0], params["humidity"][1])))),
                "ph": min(14.0, max(0.0, float(rng.normal(params["ph"][0], params["ph"][1])))),
                "rainfall": max(0.0, float(rng.normal(params["rainfall"][0], params["rainfall"][1]))),
                "label": crop,
            }
            rows.append(row)

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    return df


def train() -> None:
    """Trains the Random Forest Crop Recommendation model and serializes it.
    
    Hyperparameters follow the Nature Scientific Reports (2025) baseline:
    n_estimators=100, max_depth=20, min_samples_split=2, criterion='gini', random_state=42.
    """
    if not DATASET_PATH.exists():
        print(
            "\n[NOTICE] Building dataset grounded in uploaded papers and ICAR benchmarks...\n"
        )
        df = generate_synthetic_dataset(DATASET_PATH, samples_per_crop=100)
    else:
        print(f"Loading dataset from {DATASET_PATH}...")
        df = pd.read_csv(DATASET_PATH)

    # Validate columns
    missing_cols = set(FEATURE_NAMES + ["label"]) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    # Feature matrix and target
    X = df[FEATURE_NAMES]
    y = df["label"].astype(str)

    # Encode crop labels
    label_encoder = LabelEncoder()
    y_encoded = label_encoder.fit_transform(y)

    # 80/20 train/test split with fixed random_state=42
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.20, random_state=42, stratify=y_encoded
    )

    print(f"Dataset shape: {df.shape} (Features: {len(FEATURE_NAMES)}, Classes: {len(label_encoder.classes_)})")
    print(f"Train size: {X_train.shape[0]} | Test size: {X_test.shape[0]}")

    # Train Random Forest Classifier with Nature 2025 hyperparameters
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        min_samples_split=2,
        criterion="gini",
        random_state=42,
    )
    rf_model.fit(X_train, y_train)

    # Evaluation
    y_pred = rf_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")

    # 5-fold cross-validation mean score
    cv_scores = cross_val_score(rf_model, X, y_encoded, cv=5, scoring="accuracy")
    cv_mean = cv_scores.mean()

    print("\n--- Model Evaluation Results ---")
    print(f"Accuracy:                     {accuracy * 100:.2f}%")
    print(f"Macro F1 Score:               {macro_f1:.4f}")
    print(f"5-Fold Cross-Validation Mean: {cv_mean * 100:.2f}%\n")

    # Serialize model bundle using joblib
    bundle = {
        "model": rf_model,
        "label_encoder": label_encoder,
        "feature_names": FEATURE_NAMES,
    }
    joblib.dump(bundle, MODEL_OUTPUT_PATH)
    print(f"Successfully serialized model bundle to: {MODEL_OUTPUT_PATH}")


if __name__ == "__main__":
    train()
