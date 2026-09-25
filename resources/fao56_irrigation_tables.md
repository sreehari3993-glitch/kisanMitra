# FAO-56 Reference Evapotranspiration (ET0) — Penman-Monteith Method

## Background

In May 1990, FAO convened a panel of irrigation, drainage, and meteorology experts — working with the International Commission on Irrigation and Drainage and the World Meteorological Organization — to review how crop water requirements were being calculated. The panel recommended adopting the Penman-Monteith combination equation as the standard method for estimating reference evapotranspiration, replacing the earlier FAO Penman method with one that better matches real-world crop water use data.

## Reference Crop Definition

ET0 is calculated for a hypothetical reference crop, not a real one, so that evapotranspiration values are comparable across locations and time periods. The reference crop is defined as a uniform, actively growing, well-watered grass surface with these fixed properties:

- Crop height: h = 0.12 m
- Bulk surface resistance: rs = 70 s/m
- Albedo (reflection coefficient): 0.23 — so reflected shortwave radiation = 0.23 × Rs
- Aerodynamic resistance: ra = 208 / u2 (s/m), where u2 is wind speed at 2 m height
- Standard weather-measurement reference height: 2 m

## FAO Penman-Monteith Equation (Equation 6)

```
              0.408 Δ (Rn − G) + γ · (900 / (T + 273)) · u2 · (es − ea)
ET0  =  ─────────────────────────────────────────────────────────────
                        Δ + γ · (1 + 0.34 · u2)
```

Variable definitions:

| Symbol | Meaning | Unit |
|---|---|---|
| ET0 | Reference evapotranspiration | mm/day |
| Rn | Net radiation at the crop surface | MJ m⁻² day⁻¹ |
| G | Soil heat flux density | MJ m⁻² day⁻¹ |
| T | Mean daily air temperature at 2 m height | °C |
| u2 | Wind speed at 2 m height | m/s |
| es | Saturation vapour pressure | kPa |
| ea | Actual vapour pressure | kPa |
| es − ea | Saturation vapour pressure deficit | kPa |
| Δ | Slope of the saturation vapour pressure curve | kPa/°C |
| γ | Psychrometric constant | kPa/°C |

## Purpose of ET0

ET0 serves as a common reference point: evapotranspiration measured in different seasons or regions can be compared against it, and it's the baseline used to derive the water use of any specific crop (ETc) via a crop coefficient (Kc): **ETc = Kc × ET0**.

The equation is a physically-based approximation, not a perfect predictor — measurement/formulation simplifications mean it can deviate somewhat from true grass ET0 under ideal instrumented conditions. Even so, the Expert Consultation adopted the Penman-Monteith definition of grass ET0 as the standard baseline for deriving crop coefficients.

## Data Requirements

**Location** — Altitude (m) and latitude (degrees, converted to radians) are needed to adjust weather parameters for local average atmospheric pressure and to compute extraterrestrial radiation (Ra) and daylight hours (N).

**Temperature** — Daily maximum and minimum air temperature (°C) are preferred. Using only the daily mean temperature can still work, but tends to slightly underestimate ET0, because the relationship between temperature and saturation vapour pressure is non-linear.

**Humidity** — Daily actual vapour pressure, ea (kPa), is required. Where not directly available, it can be derived from max/min relative humidity, psychrometric wet/dry-bulb data, or dewpoint temperature.

**Radiation** — Daily net radiation (MJ m⁻² day⁻¹) is required. Where not directly measured, it can be derived from measured shortwave radiation (pyranometer) or from daily sunshine-hour duration.

**Wind speed** — Daily average wind speed (m/s) at 2 m height is required. Wind speed measured at other heights must be converted to the 2 m standard before use.

## Derivation Constants (for reference)

With the standardized measurement height (zm = zh = 2 m) and reference crop height (h = 0.12 m):

- ra = 208 / u2  [s/m]
- rs = 70  [s/m]
- (1 + rs/ra) = (1 + 0.34 · u2)

Radiation-to-water-depth conversion (using latent heat of vaporization λ = 2.45 MJ/kg):

```
Radiation [mm/day] ≈ Radiation [MJ m⁻² day⁻¹] / 2.45 = 0.408 × Radiation [MJ m⁻² day⁻¹]
```

Aerodynamic term constant (R = specific gas constant = 0.287 kJ kg⁻¹ K⁻¹; virtual temperature Tkv = 1.01(T + 273)):

```
cp·ρa / ra  =  86400 × [ γ(0.622)λ / (1.01(T+273)(0.287)(208)) ] × u2    [MJ m⁻² °C⁻¹ day⁻¹]
```

Dividing by λ (= 2.45) gives the familiar constant used in Equation 6:

```
≈ γ × (900 / (T + 273)) × u2    [mm °C⁻¹ day⁻¹]
```

(Sign convention: this term uses a positive value in the northern hemisphere and a negative value in the southern hemisphere for the related declination/radiation calculations in Chapter 3 of FAO-56.)

## Crop Coefficient (Kc) Workflow

Deriving ETc from ET0 follows this process:

1. **Calculate reference ET0** using the Penman-Monteith equation above.
2. **Select crop growth-stage lengths** (initial, development, mid-season, late-season) — from FAO-56 Table 11, verified/supplemented with local data.
3. **Choose a crop-coefficient approach:**

   **A. Single crop coefficient (Kc)** — simpler, aggregates soil evaporation and crop transpiration into one factor:
   - Select Kc values for the initial, mid-season, and end-season stages (FAO-56 Table 12).
   - Adjust Kc-initial for soil-surface wetting frequency (irrigation/rainfall pattern).
   - Adjust Kc-mid and Kc-end for local climatic conditions (wind speed, humidity).
   - Construct the Kc curve across the full growing season.

   **B. Dual crop coefficient (Kcb + Ke)** — separates basal crop transpiration from soil evaporation, more precise but more data-intensive:
   - Select basal coefficient values Kcb-initial, Kcb-mid, Kcb-end (FAO-56 Table 17).
   - Adjust Kcb-mid and Kcb-end for local climatic conditions.
   - Construct the Kcb curve.
   - Determine daily Ke values for surface evaporation.
   - Combine: Kc = Kcb + Ke.

4. **Final step (both approaches converge here):**

```
ETc = Kc × ET0
```

## Note for KrishiMitra implementation

The specific Kc values per growth stage (FAO-56 Tables 12 and 17) aren't included in the source pages captured here — pull per-crop Kc values (e.g., Rice, Wheat, Cotton, initial/mid/late stages) from the full FAO-56 tables before finalizing `irrigation.py`'s lookup dictionary, or use the placeholder standard values already drafted for the Phase 3 prompt as a starting point.
