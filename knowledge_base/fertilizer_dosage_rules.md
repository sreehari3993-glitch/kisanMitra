# Stoichiometric Fertilizer Dosage & Soil Amendment Principles

This guide details the scientific stoichiometry and operational rules governing commercial fertilizer dosing (DAP, Urea, Muriate of Potash) and pH remediation (Agricultural Lime and Gypsum) utilized by KrishiMitra.

---

## 1. Principles of Elemental Deficit Calculation

Precision fertilizer management begins by measuring available soil macronutrients (Nitrogen $N$, Phosphorus $P$, and Potassium $K$) via calibrated IoT sensors or laboratory soil tests. These current nutrient concentrations are compared directly against the crop-specific optimal agronomic targets:

1. **Nitrogen Deficit ($N_{\text{deficit}}$)**:
   $$N_{\text{deficit}} = \max(0, N_{\text{optimal}} - N_{\text{current}})$$
2. **Phosphorus Deficit ($P_{\text{deficit}}$)**:
   $$P_{\text{deficit}} = \max(0, P_{\text{optimal}} - P_{\text{current}})$$
3. **Potassium Deficit ($K_{\text{deficit}}$)**:
   $$K_{\text{deficit}} = \max(0, K_{\text{optimal}} - K_{\text{current}})$$

When current soil nutrient reserves exceed or meet the crop's requirements, the calculated deficit is clamped to zero, preventing excessive synthetic fertilizer application, nitrate leaching, and groundwater eutrophication.

---

## 2. Stoichiometric Conversion to Commercial Fertilizers

Commercial chemical fertilizers supply nutrients in specific chemical ratios rather than elemental forms. KrishiMitra implements a strict multi-nutrient stoichiometric allocation:

### Step 1: Diammonium Phosphate (DAP) Allocation
Diammonium Phosphate ($(\text{NH}_4)_2\text{HPO}_4$) is the primary source of phosphorus. High-grade commercial DAP contains **46% Phosphate ($\text{P}_2\text{O}_5$)** and **18% ammoniacal Nitrogen ($N$)**.

Because phosphorus is immobile in soil and essential for early root morphology, the entire phosphorus deficit must be satisfied through DAP:
$$\text{DAP}_{\text{kg}} = \frac{P_{\text{deficit}}}{0.46}$$

### Step 2: Net Nitrogen Deficit Deduction
Applying DAP inadvertently supplies nitrogen to the root zone at a rate of 18 kg of elemental $N$ per 100 kg of DAP. Failing to deduct this co-supplied nitrogen leads to severe nitrogen over-fertilization, excessive vegetative growth, lodging, and increased pest susceptibility.

The net remaining nitrogen deficit is calculated as:
$$\text{Net } N_{\text{deficit}} = \max\left(0, N_{\text{deficit}} - (\text{DAP}_{\text{kg}} \times 0.18)\right)$$

If DAP supplies more nitrogen than the crop's total deficit, the net nitrogen deficit is capped at zero, and no additional Urea is recommended.

### Step 3: Urea Allocation
Commercial Urea ($\text{CO(NH}_2)_2$) contains **46% elemental Nitrogen**. The remaining net nitrogen deficit is satisfied exclusively via Urea:
$$\text{Urea}_{\text{kg}} = \frac{\text{Net } N_{\text{deficit}}}{0.46}$$

### Step 4: Muriate of Potash (MOP) Allocation
Potassium regulates stomatal conductance, osmotic pressure, and starch synthesis. Commercial Muriate of Potash ($\text{KCl}$) contains **60% Potash ($\text{K}_2\text{O}$)**:
$$\text{MOP}_{\text{kg}} = \frac{K_{\text{deficit}}}{0.60}$$

---

## 3. Soil pH Remediation & Chemical Amendments

Soil pH directly controls the bioavailability of macro- and micronutrients. Outside the optimal range ($6.0 \le \text{pH} \le 7.5$), nutrients become chemically locked: phosphorus precipitates as insoluble aluminum/iron phosphates in acidic soils, and as calcium phosphates in alkaline soils.

### Case A: Acidic Soil Remediation ($\text{pH} < 6.0$)
In soils with $\text{pH} < 6.0$, aluminum ($Al^{3+}$) and manganese ($Mn^{2+}$) toxicity inhibits root elongation. Agricultural Lime ($\text{CaCO}_3$) neutralizes active acidity and supplies calcium ions.
- **Remediation Target**: Target $\text{pH} = 6.5$.
- **Buffer Coefficient**: 250 kg lime per acre per unit pH deficit.
$$\text{Lime}_{\text{kg/acre}} = (6.5 - \text{pH}) \times 250$$

### Case B: Alkaline & Sodic Soil Remediation ($\text{pH} > 7.5$)
In alkaline soils with $\text{pH} > 7.5$, excess sodium ($Na^+$) causes soil dispersion, poor permeability, and surface crusting. Agricultural Gypsum ($\text{CaSO}_4 \cdot 2\text{H}_2\text{O}$) replaces exchangeable sodium with calcium, forming soluble sodium sulfate that leaches away with irrigation.
- **Remediation Target**: Target $\text{pH} = 7.0$.
- **Amendment Coefficient**: 300 kg gypsum per acre per unit excess pH.
$$\text{Gypsum}_{\text{kg/acre}} = (\text{pH} - 7.0) \times 300$$

### Case C: Optimal Range ($6.0 \le \text{pH} \le 7.5$)
No chemical soil amendments are needed. Both lime and gypsum dosages are set to **0 kg/acre**.

---

## 4. Best Practices for Field Application

1. **Basal Application**: Apply all DAP and MOP, along with 25% of the prescribed Urea, at sowing or transplanting.
2. **Topdressing Splits**: Split the remaining 75% of Urea into two equal doses applied during active tillering/vegetative growth and panicle initiation/flowering.
3. **Soil Moisture Prerequisite**: Never apply urea or chemical fertilizers on dry soil; always broadcast or band fertilizers when soil moisture is at least 18%–25%, followed by light irrigation.
