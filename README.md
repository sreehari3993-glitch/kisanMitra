# 🌱 KrishiMitra — IoT Soil Intelligence & Precision Agriculture Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python_3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Scikit-Learn](https://img.shields.io/badge/scikit_learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-3F51B5?style=for-the-badge)](https://www.trychroma.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**KrishiMitra** is a full-stack, AI-powered precision agriculture and IoT soil health intelligence system that turns raw sensor data into precise, actionable agronomy — in the farmer's own language.

> **Team:** Anzal Rahman M · Sreehari B — **HACK'26**

---

## 🌟 Key Features

### Farmer Advisory Dashboard
- **Real-time Soil Health Gauges** — Nitrogen, Phosphorus, Potassium, pH, and Volumetric Moisture with ICAR-rated composite health index (0–100).
- **Random Forest Crop Recommendations** — Top matching crops with probability-based confidence scores across 30 categories.
- **Soil Healing Prescription Station** — Stoichiometric NPK deficit → exact DAP/Urea/MOP (kg/acre), plus pH remediation via Agricultural Lime (acidic) or Gypsum (alkaline).
- **FAO-56 Irrigation Advisory** — Hargreaves ET₀ with humidity attenuation → dual crop-coefficient Kc (initial/mid/late) → daily ETc → deficit & pump runtime.
- **Kisan AI Multilingual RAG Copilot** — Context-aware agronomic chatbot supporting English, Hindi, Malayalam, Tamil, Telugu, and Kannada, powered by ChromaDB vector retrieval and Google Gemini with offline ICAR/FAO-56 fallback.
- **Farmer Authentication** — Secure login gateway with 1-click quick demo access and session persistence.

### IoT Sensor Telemetry Station
- Standard manual probe injection interface for prototype environments (ESP32-S3 based).
- **Dual-Control Inputs** — Bidirectional sync between numeric inputs and range sliders.
- **Regional Benchmark Presets** — Palakkad Rice Paddy, Punjab Wheat Field, Maharashtra Cotton Belt, and Wayanad Plantation.
- **Live Hardware Telemetry Terminal** — Real-time hex/JSON packet console with battery %, solar MPPT, and LoRa 868 MHz / MQTT status.

### Mobile & Offline
- **Progressive Web App (PWA)** — Installable on any device via Service Worker with offline caching.
- **Android APK** — Native Android build via Capacitor (`mobile/krishimitra-app.apk`).

---

## 🏗️ System Architecture

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                      FRONTEND (HTML5 / Vanilla CSS / JS)                     │
│   ├── Farmer Advisory Dashboard (Chart.js Gauges, Recommendations, Healing)  │
│   ├── IoT Sensor Screen (Dual-Control Inputs, Telemetry Terminal)            │
│   └── PWA + Capacitor Android Shell                                          │
└──────────────────────────────────┬───────────────────────────────────────────┘
                                   │ HTTP REST JSON
                                   ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                          FASTAPI BACKEND ENGINE                              │
│   ├── /api/auth                  → JWT & Session Management                  │
│   ├── /api/telemetry             → IoT Telemetry Ingestion (ESP32-S3)        │
│   ├── /api/soil-health-card      → ICAR Soil Health Index (0-100)            │
│   ├── /api/recommend-crops       → Random Forest Classifier (30 Crops)       │
│   ├── /api/fertilizer-prescription → Stoichiometric NPK Deficit Engine       │
│   ├── /api/irrigation-advisory   → FAO-56 Hargreaves ET₀ + Kc + ETc         │
│   ├── /api/kisan-ai/chat         → Multilingual RAG (ChromaDB + Gemini)      │
│   ├── /api/kisan-ai/history      → Persistent Chat History & GDrive Sync     │
│   ├── /api/kisan-ai/resources    → Indexed Knowledge Base Metadata           │
│   └── /api/mobile/status         → Mobile Discovery & Plugin Status          │
└──────────────────┬───────────────────────────────────┬───────────────────────┘
                   ▼                                   ▼
     ┌───────────────────────────┐       ┌───────────────────────────┐
     │      MySQL DATABASE       │       │   CHROMADB VECTOR STORE   │
     │  telemetry_logs,          │       │  FAO-56 tables, ICAR      │
     │  crop_recommendations,    │       │  guidelines, fertilizer   │
     │  prescriptions            │       │  rules, pest remedies     │
     └───────────────────────────┘       └───────────────────────────┘
```

---

## 📊 ML Model Performance

| Metric | Value |
|--------|-------|
| **Algorithm** | Random Forest Classifier |
| **Estimators** | 100 trees, max_depth=20, Gini criterion |
| **Features** | N, P, K, Temperature, Humidity, pH, Rainfall (7 features) |
| **Classes** | 30 crop categories (22 Kaggle benchmark + 8 regional Indian crops + no_crop) |
| **Train/Test Split** | 80/20, stratified, random_state=42 |
| **Test Accuracy** | 99.32% |
| **Validation** | 5-fold cross-validation |

---

## 🧠 Technical Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | HTML5, Vanilla CSS (custom design system), JavaScript, Chart.js |
| **Backend** | FastAPI, Uvicorn (async), SQLAlchemy 2.0 |
| **Database** | MySQL 8.0+ (telemetry, recommendations, prescriptions) |
| **ML** | scikit-learn (Random Forest), joblib, pandas, numpy |
| **RAG** | ChromaDB (vector store), sentence-transformers (embeddings) |
| **LLM** | Google Gemini 1.5 Flash (primary), offline ICAR/FAO-56 engine (fallback) |
| **IoT** | ESP32-S3 prototype node, MQTT protocol |
| **Mobile** | Capacitor (Android APK), PWA (Service Worker) |
| **Deployment** | Vercel (frontend), Railway (backend), Docker |

---

## 📚 Knowledge Base & Research Resources

The RAG pipeline indexes agronomic literature from two directories:

| Directory | Contents |
|-----------|----------|
| `knowledge_base/` | ICAR crop guidelines, FAO-56 irrigation tables, fertilizer dosage rules, pest/deficiency remedies (Markdown) |
| `resources/` | Research papers (Nature Scientific Reports 2025, IRJIET, ETASR), crop feasibility benchmarks, FAO water balance equations (PDF/TXT) |

---

## 🚀 Quickstart Guide

### Prerequisites
- Python 3.10+
- MySQL Server 8.0+
- Git

### 1. Clone & Setup
```bash
git clone https://github.com/sreehari3993-glitch/kisanMitra.git
cd kisanMitra
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Update `.env` with your credentials:
```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/krishi_precision_db
GEMINI_API_KEY=YOUR_GEMINI_KEY_OPTIONAL
```

> **Note:** The Gemini API key is optional. Without it, the chatbot falls back to the offline ICAR/FAO-56 synthesis engine (<10 ms response time).

### 3. Initialize Database & Train ML Model
```bash
python init_db.py
python ml/train_model.py
```

### 4. Run the Application
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

| URL | Description |
|-----|-------------|
| `http://localhost:8000` | Main application |
| `http://localhost:8000/docs` | Interactive API documentation (Swagger UI) |

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

Test coverage includes:
- `test_agronomy_math.py` — NPK deficit calculations, fertilizer stoichiometry, pH remediation, soil health index
- `test_fao56_irrigation.py` — Hargreaves ET₀, crop coefficients, ETc, irrigation status evaluation
- `test_kisan_ai.py` — Language detection, query enrichment, multilingual response generation

---

## 🗂️ Project Structure

```
krishimitra/
├── backend/
│   ├── main.py              # FastAPI app, lifespan, Kisan AI endpoints
│   ├── agronomy.py           # NPK deficit, fertilizer prescription, pH remediation
│   ├── irrigation.py         # FAO-56 ET₀, Kc lookup, ETc, irrigation status
│   ├── kisan_ai.py           # Multilingual RAG chatbot (1600+ lines)
│   ├── ml_service.py         # ML model loading & inference
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── database.py           # Database engine & session management
│   ├── config.py             # Settings & environment variables
│   ├── chat_history.py       # Persistent conversation logging
│   ├── drive_sync.py         # Google Drive cloud backup
│   ├── rag/                  # Modular RAG pipeline
│   │   ├── service.py        # RAGService orchestrator
│   │   ├── vector_store.py   # ChromaDB wrapper
│   │   ├── retriever.py      # Hybrid retrieval (vector + keyword)
│   │   ├── extractor.py      # Document chunk extraction
│   │   └── config.py         # RAG paths & constants
│   └── routers/
│       ├── auth.py           # Authentication routes
│       ├── telemetry.py      # Telemetry ingestion & soil health card
│       ├── recommendations.py # Crop recommendation & fertilizer prescription
│       └── irrigation.py     # Irrigation advisory routes
├── frontend/
│   ├── index.html            # Main dashboard (dual-interface)
│   ├── login.html            # Authentication page
│   ├── app.js                # Application logic
│   ├── style.css             # Design system (4600+ lines)
│   ├── sw.js                 # Service Worker (PWA offline)
│   └── manifest.json         # PWA manifest
├── ml/
│   ├── train_model.py        # Random Forest training pipeline
│   ├── crop_rf_model.pkl     # Serialized model bundle
│   └── dataset.csv           # Training dataset
├── mobile/
│   ├── capacitor.config.json # Capacitor configuration
│   └── krishimitra-app.apk   # Android build artifact
├── knowledge_base/           # RAG source documents (Markdown)
├── resources/                # Research papers & agronomic tables (PDF/TXT)
├── tests/                    # pytest test suite
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variable template
├── Procfile                  # Railway deployment
├── docker-compose.yml        # Docker configuration
└── railway.json              # Railway deployment config
```

---

## 👨‍🌾 Default Demo Credentials
- **Lead Farmer:** Ramesh Patel (`kisan_demo`)
- **Password:** `kisan2025`

---

## 🌐 Multilingual Support

Kisan AI auto-detects the farmer's language via Unicode script range analysis and responds natively:

| Language | Script Range | Status |
|----------|-------------|--------|
| English | Latin | ✅ Supported |
| Hindi | Devanagari (U+0900–U+097F) | ✅ Supported |
| Malayalam | Malayalam (U+0D00–U+0D7F) | ✅ Supported |
| Tamil | Tamil (U+0B80–U+0BFF) | ✅ Supported |
| Telugu | Telugu (U+0C00–U+0C7F) | ✅ Supported |
| Kannada | Kannada (U+0C80–U+0CFF) | ✅ Supported |

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
