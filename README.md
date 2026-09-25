# 🌱 KisanMitra (KrishiMitra) — IoT Soil Intelligence & Precision Agriculture Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python_3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Scikit-Learn](https://img.shields.io/badge/scikit_learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**KisanMitra** is a full-stack, AI-powered precision agriculture and IoT soil health intelligence system designed to optimize crop yields, eliminate fertilizer overuse, correct soil pH, and calculate dynamic crop irrigation requirements.

---

## 🌟 Key Highlights & Architecture

### 1. Dual-Interface Experience
- **`[ 👤 User ]` Farmer Advisory Dashboard:**
  - Real-time **Soil Health Gauges** for Nitrogen, Phosphorus, Potassium, Soil pH, and Volumetric Moisture.
  - **Random Forest Crop Recommendations** displaying top matching crops with confidence scores.
  - **Soil Healing Prescription Station:** Calculates exact fertilizer deficits (Urea, SSP, MOP) and mandatory soil amendments (Agricultural Lime $\text{Ca(OH)}_2$ for acidic soil, Gypsum $\text{CaSO}_4$ for alkaline soil).
  - **FAO-56 Penman-Monteith Irrigation Advisory:** Evapotranspiration ($ET_0$), crop coefficients ($K_c$), and exact pump runtime.
  - **Kisan AI Multilingual RAG Copilot:** Context-aware agronomic chatbot supporting English, Malayalam, Hindi, and Tamil powered by ChromaDB vector retrieval and Google Gemini.
  - **Farmer Authentication:** Secure login gateway with 1-click quick demo access and session persistence.

- **`[ 📡 Sensor Screen ]` IoT Prototype Telemetry Station:**
  - Standard manual probe injection interface for prototype environments where physical optical/electrochemical probes are simulated.
  - **Dual-Control Inputs:** Bidirectional synchronization between numeric input boxes and fine range sliders.
  - **Regional Benchmark Presets:** Palakkad Rice Paddy, Punjab Wheat Field, Maharashtra Cotton Belt, and Wayanad Plantation.
  - **Prominent "Test Now" Trigger:** Executes real-time telemetry transmission via node `ESP32-S3-KRISHI-01`, recalculates health scores, updates recommendations, and links directly back to the advisory view.
  - **Live Hardware Telemetry Terminal:** Real-time hex/JSON packet console displaying battery %, solar MPPT charging, and LoRa 868MHz / MQTT transmission packets.

---

## 🏗️ System Architecture

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND (HTML5 / Vanilla CSS / JS)              │
│   ├── User Advisory Interface (Chart.js Gauges, Recommendations, Healing)   │
│   └── IoT Sensor Screen (Dual-Control Inputs, LoRa/ADC Specs, "Test Now")   │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP REST JSON / WebSockets
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI BACKEND ENGINE                           │
│   ├── /api/auth              -> JWT & Session Management                    │
│   ├── /api/telemetry         -> IoT Telemetry Ingestion (ESP32-S3)          │
│   ├── /api/soil-health-card  -> NPK & pH Agronomic Rating Engine            │
│   ├── /api/recommend-crops   -> Random Forest ML Classifier (22 Crops)      │
│   ├── /api/fertilizer-prescription -> Deficit Math & Amendment Logic        │
│   ├── /api/irrigation-advisory     -> FAO-56 Penman-Monteith Equation       │
│   └── /api/kisan-ai/chat     -> Multilingual RAG with ChromaDB & Gemini     │
└───────────────────┬──────────────────────────────────┬──────────────────────┘
                    ▼                                  ▼
      ┌───────────────────────────┐      ┌───────────────────────────┐
      │     MySQL DATABASE        │      │   CHROMADB VECTOR STORE   │
      │  telemetry, recommendations│      │  agronomic literature,    │
      │  fertilizer, irrigation   │      │  FAO guidelines, manuals  │
      └───────────────────────────┘      └───────────────────────────┘
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+
- MySQL Server (8.0+)
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/sreehari3993-glitch/kisanMitra.git
cd kisanMitra
```

### 3. Create and Activate Virtual Environment
```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# macOS / Linux:
source .venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Update your database credentials:
```env
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/krishi_precision_db
GEMINI_API_KEY=YOUR_GEMINI_KEY_OPTIONAL
```

### 6. Initialize Database & Train ML Model
```bash
python init_db.py
python ml/train_model.py
```

### 7. Run the Application
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at: **`http://localhost:8000`**  
Interactive API Docs: **`http://localhost:8000/docs`**

---

## 📊 ML Model Performance
- **Algorithm:** Random Forest Classifier (22 Crop Categories)
- **Features:** Nitrogen (N), Phosphorus (P), Potassium (K), Temperature (°C), Humidity (%), Soil pH, Rainfall (mm)
- **Validation Accuracy:** `99.32%`

---

## 👨‍🌾 Default Demo Credentials
- **Lead Farmer:** Ramesh Patel (`kisan_demo`)
- **Password:** `kisan2025`

---

## 📄 License
This project is open-source and available under the [MIT License](LICENSE).
