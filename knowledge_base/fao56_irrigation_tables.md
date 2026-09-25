# FAO-56 Irrigation & Water Balance Reference Tables

This reference document synthesizes the Food and Agriculture Organization (FAO) Irrigation and Drainage Paper No. 56 ("Crop Evapotranspiration — Guidelines for Computing Crop Water Requirements") single crop coefficient methodology and daily root-zone water balance dynamics.

---

## 1. FAO-56 Crop Coefficients ($K_c$) by Phenological Stage

The crop coefficient ($K_c$) integrates crop height, albedo, canopy resistance, and soil evaporation. Evapotranspiration under non-stressed conditions ($ET_c$) is computed as:
$$ET_c = K_c \times ET_0$$

Below are published FAO-56 benchmark $K_c$ values across growth stages under typical sub-humid to semi-arid climates:

| Crop Category | Crop Name | $K_{c\text{, initial}}$ | $K_{c\text{, mid-season}}$ | $K_{c\text{, late/end}}$ | Typical Root Depth ($Z_r$, m) | Depletion Fraction ($p$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Cereals** | Rice (Paddy) | 1.05 | 1.20 | 0.90 | 0.5 – 1.0 | 0.20 |
| | Wheat | 0.35 | 1.15 | 0.40 | 1.0 – 1.5 | 0.55 |
| | Maize | 0.30 | 1.20 | 0.60 | 1.0 – 1.7 | 0.55 |
| **Pulses** | Chickpea | 0.40 | 1.00 | 0.35 | 0.6 – 1.0 | 0.50 |
| | Kidneybeans | 0.40 | 1.15 | 0.35 | 0.5 – 0.8 | 0.45 |
| | Pigeonpeas | 0.40 | 1.05 | 0.50 | 1.0 – 1.8 | 0.60 |
| | Mothbeans | 0.35 | 1.00 | 0.35 | 0.6 – 1.0 | 0.65 |
| | Mungbean / Blackgram | 0.40 | 1.05 | 0.35 | 0.6 – 0.9 | 0.50 |
| | Lentil | 0.40 | 1.10 | 0.30 | 0.6 – 0.8 | 0.50 |
| **Fiber & Cash** | Cotton | 0.35 | 1.20 | 0.60 | 1.0 – 1.7 | 0.65 |
| | Jute | 0.40 | 1.15 | 0.75 | 0.7 – 1.0 | 0.35 |
| | Coffee | 0.90 | 0.95 | 0.95 | 1.2 – 1.8 | 0.50 |
| **Fruits & Orchard** | Banana | 1.00 | 1.20 | 1.10 | 0.5 – 0.9 | 0.35 |
| | Mango | 0.60 | 0.80 | 0.70 | 1.5 – 2.5 | 0.50 |
| | Grapes | 0.30 | 0.85 | 0.45 | 1.0 – 2.0 | 0.45 |
| | Watermelon | 0.40 | 1.00 | 0.75 | 0.8 – 1.5 | 0.40 |
| | Muskmelon | 0.40 | 1.00 | 0.75 | 0.8 – 1.5 | 0.40 |
| | Apple | 0.45 | 0.95 | 0.70 | 1.0 – 2.0 | 0.50 |
| | Orange / Citrus | 0.70 | 0.65 | 0.70 | 0.8 – 1.5 | 0.50 |
| | Papaya | 0.50 | 1.00 | 0.85 | 0.6 – 1.0 | 0.40 |
| | Coconut | 0.80 | 1.00 | 0.90 | 1.0 – 2.0 | 0.50 |
| | Pomegranate | 0.50 | 0.75 | 0.60 | 1.0 – 1.8 | 0.55 |

---

## 2. Reference Evapotranspiration ($ET_0$): The Hargreaves Method

While standard FAO-56 Penman-Monteith requires net radiation, wind speed at 2 m, and relative humidity psychrometry, IoT agricultural field nodes usually collect ambient temperature and relative humidity.

The **Hargreaves-Samani (1985)** empirical equation provides a robust, field-tested alternative:
$$ET_{0\text{, base}} = 0.0023 \times R_a \times (T_{\text{mean}} + 17.8) \times \sqrt{T_{\text{max}} - T_{\text{min}}}$$

- **$R_a$ (Extraterrestrial Radiation)**: Evaluated at 15.0 mm/day equivalent for tropical/sub-tropical Indian latitudes (15°N – 25°N).
- **Temperature Range ($TD$)**: Diurnal temperature variation ($T_{\text{max}} - T_{\text{min}}$) defaults to 10.0°C.
- **Humidity Attenuation Factor**: To adjust for reduced atmospheric vapor pressure deficit in humid climates:
$$\text{Factor}_{\text{humidity}} = \max\left(0.10, 1.0 - \frac{\text{Humidity}_{\%}}{200}\right)$$
$$ET_0 = ET_{0\text{, base}} \times \text{Factor}_{\text{humidity}}$$

---

## 3. Daily Soil Water Balance in the Root Zone

The root zone is treated as a finite reservoir where water content fluctuates between Field Capacity ($\theta_{\text{FC}}$) and Permanent Wilting Point ($\theta_{\text{WP}}$).

The daily root zone depletion ($D_{r,i}$) is expressed as:
$$D_{r,i} = D_{r,i-1} - (P_i - RO_i) - I_i - CR_i + ET_{c,i} + DP_i$$

Where:
- $D_{r,i}$: Root zone depletion at the end of day $i$ [mm]
- $D_{r,i-1}$: Depletion from previous day [mm]
- $P_i$: Gross precipitation [mm]
- $RO_i$: Surface runoff [mm]
- $I_i$: Net infiltrated irrigation depth [mm]
- $CR_i$: Capillary rise from shallow groundwater table (assumed 0 when water table > 1 m) [mm]
- $ET_{c,i}$: Actual crop evapotranspiration on day $i$ [mm]
- $DP_i$: Deep percolation loss out of the root zone when water content exceeds field capacity [mm]

### Depletion Bounds:
$$0 \le D_{r,i} \le \text{TAW}$$
$$\text{TAW} = 1000 \times (\theta_{\text{FC}} - \theta_{\text{WP}}) \times Z_r$$
$$\text{RAW} = p \times \text{TAW}$$

---

## 4. Operational Thresholds & Pump Runtime Determination

KrishiMitra evaluates telemetry readings against root zone thresholds:

1. **`CRITICAL_IRRIGATE`**:
   - **Trigger**: $\text{Current Soil Moisture} \le \text{RAW Threshold}$ (typically 22.0% volumetric water content).
   - **Action**: Replenish moisture back to Field Capacity (typically 32.0%).
   - **Deficit**:
     $$\text{Deficit}_{\text{mm}} = \text{Field Capacity} - \text{Current Moisture}$$
   - **Pump Runtime Calculation**:
     $$\text{Runtime}_{\text{hours}} = \frac{\text{Deficit}_{\text{mm}}}{\text{Emitter Rate}_{\text{mm/hr}}}$$

2. **`MONITOR`**:
   - **Trigger**: $\text{Current Moisture} > \text{RAW}$, but $(\text{Current Moisture} - ET_c) \le \text{RAW}$.
   - **Interpretation**: Water content will fall into the stress zone within the next 24 hours. Pre-irrigation scheduling is recommended.

3. **`OPTIMAL`**:
   - **Trigger**: $(\text{Current Moisture} - ET_c) > \text{RAW}$.
   - **Interpretation**: Root zone possesses sufficient available moisture. Pump remains off.
