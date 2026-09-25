# 📚 KrishiMitra Agronomic Research Library & RAG Resource Store

This directory contains the foundational agronomic papers, FAO-56 irrigation manuals, crop coefficient tables, and soil nutrient studies powering the **KrishiMitra Kisan AI Copilot** and precision recommendation engines.

## ☁️ Google Drive Cloud Resource Folder
- **Direct Link**: [Agricultural Research & Guidelines Resource Library](https://drive.google.com/drive/folders/1LdRwAKBybFYsijbMmOd2EdLRDqISTpI6?usp=drive_link)
- **Folder ID**: `1LdRwAKBybFYsijbMmOd2EdLRDqISTpI6`

---

## 📄 Actively Indexed Documents & Research Papers

1. **`s41598-025-26910-4.pdf`** (*Nature Scientific Reports, 2025*):
   - *Interpretable deep learning models for independent fertilizer and crop recommendation* (Stella Mary Venkateswara & Jayashree Padmanaban).
   - Random Forest & TabNet architectures, SMOTE class balancing, Western Maharashtra 22-crop benchmarks (96.21% crop accuracy, 95.24% fertilizer classification accuracy).
   - Hyperparameter baselines: `n_estimators=100`, `max_depth=20`, `criterion='gini'`.

2. **`vtse2078+(1)_compressed.pdf`** (*VFAST Transactions on Software Engineering, 2025*):
   - *Advancing Agriculture with IoT and a Smart Fertilizer Recommendation System* (Asim Irfan et al.).
   - IoT sensor node circuit with NPK sensor, DS18B20 temperature, and capacitive soil moisture.
   - Sona Urea, Sona DAP, and FFC SOP commercial bag per acre conversion models (Table 3 & Table 4).

3. **`IRJIET-INSPIRE250231745453188.pdf`** (*IRJIET, 2025*):
   - *Crop Recommendation System Using Machine Learning and IoT for Precision Farming* (Uday Kumar Kori et al.).
   - Comparison of Decision Tree (90%), SVM (97%), Logistic Regression (95%), and Random Forest (99% benchmark accuracy).

4. **`ETASR-BSRLRT-Mandya-LoRa.pdf`** (*ETASR, 2026*):
   - *IoT-Driven Soil Nutrient Measurement Using LoRa and Broken-Stick Regression Techniques* (C. V. Pallavi & S. Usha).
   - V.C. Farm (Mandya, Karnataka) 7-in-1 NPK sensor deployment via SX1278 LoRa and Node-RED.
   - Table II standard fertility thresholds: Nitrogen (Low <125, Med 125-250, High >250), Phosphorus (<10, 10-25, >25), Potassium (<63, 63-150, >150), pH (Acidic <6.5, Neutral 6.5-7.5, Alkaline >7.5).

5. **`TABLE.txt`**:
   - FAO-56 published crop coefficient ($K_c$) tables for vegetables: Broccoli, Cabbage, Garlic, Onions, Spinach, Tomato, Cucumber, Watermelon, Cantaloupe, with initial, mid-season, end-season $K_c$, and maximum crop heights.

6. **`WATER BALANCE.txt`**:
   - FAO-56 root-zone daily water balance equations ($D_{r,i} = D_{r,i-1} - (P-RO)_i - I_i - CR_i + ET_{c,i} + DP_i$), $0 \le D_{r,i} \le \text{TAW}$, initial depletion $D_{r,i-1}$, and Readily Available Water ($\text{RAW}$).

7. **`fao56_irrigation_tables.md`**:
   - Reference table of FAO-56 single-crop coefficients across growth stages.

---

## 🔄 Dynamic Ingestion for Future Files

Any new file (PDF, TXT, MD, CSV) placed into this `resources/` folder in the future is **automatically discovered, parsed, chunked, and indexed** into the Kisan AI RAG semantic search corpus on application startup or when calling `rag_service.ingest_knowledge_base()`.
