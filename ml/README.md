# KrishiMitra ML Crop Recommendation Engine

This module trains and provides inference for the AI-powered crop recommendation system using a **Random Forest Classifier (100 estimators)**.

---

## Dataset Specifications

The model expects the standard **Kaggle 22-Crop Benchmark Dataset** (*Crop Recommendation Dataset* by Atharva Ingle).

### File Placement & Filename
Place your real Kaggle CSV file directly at:
```text
ml/dataset.csv
```

### Expected Schema
The CSV must contain **8 columns** in comma-separated format:

| Column Name | Description | Example Range |
| :--- | :--- | :--- |
| `N` | Ratio of Nitrogen content in soil | 0 – 140 kg/ha |
| `P` | Ratio of Phosphorous content in soil | 5 – 145 kg/ha |
| `K` | Ratio of Potassium content in soil | 5 – 205 kg/ha |
| `temperature` | Temperature in degrees Celsius | 8.8 – 43.7 °C |
| `humidity` | Relative humidity in % | 14.2 – 99.9 % |
| `ph` | pH value of the soil | 3.5 – 9.9 |
| `rainfall` | Rainfall in mm | 20.2 – 298.6 mm |
| `label` | Target crop name (string) | e.g., `rice`, `maize`, `coffee` |

### Expected Classes (22 Crops)
The standard benchmark dataset contains 100 samples per crop (2,200 rows total):
`apple`, `banana`, `blackgram`, `chickpea`, `coconut`, `coffee`, `cotton`, `grapes`, `jute`, `kidneybeans`, `lentil`, `maize`, `mango`, `mothbeans`, `mungbean`, `muskmelon`, `orange`, `papaya`, `pigeonpeas`, `pomegranate`, `rice`, `watermelon`.

---

## Synthetic Fallback

If `ml/dataset.csv` is not present when you execute `train_model.py`, the script will:
1. Print a warning indicating the synthetic mode is active.
2. Generate a synthetic dataset of **2,200 rows** across all **22 crops** using verified agronomic distributions.
3. Automatically save it to `ml/dataset.csv`.

> [!WARNING]
> Synthetic data provides a functional baseline for testing, but **you must swap in the real Kaggle dataset before the final demo presentation** to ensure real-world benchmark accuracy (~99.1%).

---

## Training / Retraining the Model

Run the training pipeline from the `krishimitra` directory:

```bash
cd krishimitra
python ml/train_model.py
```

### Output Artifacts
The training script produces:
- `ml/crop_rf_model.pkl`: A serialized `joblib` bundle containing:
  - `model`: Trained `RandomForestClassifier`
  - `label_encoder`: Fitted `LabelEncoder` instance
  - `feature_names`: `["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]`

Evaluation metrics (Accuracy, Macro F1, and 5-Fold Cross Validation Mean) will be printed in your terminal.

---

## Integration with FastAPI Backend

Inference is served by [backend/ml_service.py](file:///c:/Users/sreeh/OneDrive/Desktop/HACKATHON.MAIN/krishimitra/backend/ml_service.py):
- **Lifecycle Loading**: The model is loaded once into memory via `load_model()` inside FastAPI's startup lifespan event (zero per-request disk I/O).
- **Prediction**: `predict_top_crops(n, p, k, ph, temp, humidity, rainfall, top_k=3)` constructs the aligned feature matrix, executes `predict_proba`, and returns ranked recommendations with percentage confidence.
