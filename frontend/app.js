/**
 * KrishiMitra — Frontend Application Logic
 * Single-Page, Mobile-First, High-Contrast Precision Agriculture Dashboard
 */

// Global state
let currentTelemetryId = null;
let currentRecommendationId = null;
let currentSelectedCrop = null;
const gaugeCharts = {};

// Static crop metadata for growth duration and water requirements
const CROP_METADATA = {
  rice: { duration: "110–140 days", water: "High (1100–1400 mm)", type: "Kharif Grain" },
  wheat: { duration: "120–150 days", water: "Medium (450–650 mm)", type: "Rabi Cereal" },
  cotton: { duration: "150–180 days", water: "Medium-High (700–1100 mm)", type: "Fiber Crop" },
  maize: { duration: "90–110 days", water: "Medium (500–800 mm)", type: "Cereal / Fodder" },
  chickpea: { duration: "95–115 days", water: "Low (250–350 mm)", type: "Rabi Pulse" },
  kidneybeans: { duration: "90–120 days", water: "Low-Med (350–500 mm)", type: "Legume" },
  pigeonpeas: { duration: "140–180 days", water: "Medium (600–750 mm)", type: "Pulse" },
  mothbeans: { duration: "75–90 days", water: "Very Low (200–300 mm)", type: "Arid Pulse" },
  mungbean: { duration: "60–75 days", water: "Low (300–400 mm)", type: "Short Pulse" },
  blackgram: { duration: "70–90 days", water: "Low (350–450 mm)", type: "Pulse" },
  lentil: { duration: "110–130 days", water: "Low (250–350 mm)", type: "Rabi Pulse" },
  pomegranate: { duration: "Perennial", water: "Low-Med (500–700 mm)", type: "Fruit" },
  banana: { duration: "300–365 days", water: "Very High (1500–2200 mm)", type: "Tropical Fruit" },
  mango: { duration: "Perennial", water: "Medium (750–1000 mm)", type: "Orchard" },
  grapes: { duration: "Perennial", water: "Low-Med (400–600 mm)", type: "Vineyard" },
  watermelon: { duration: "80–100 days", water: "Medium (400–600 mm)", type: "Cucurbit" },
  muskmelon: { duration: "75–90 days", water: "Medium (350–500 mm)", type: "Cucurbit" },
  apple: { duration: "Perennial", water: "Medium (800–1000 mm)", type: "Temperate Fruit" },
  orange: { duration: "Perennial", water: "Med-High (900–1200 mm)", type: "Citrus" },
  papaya: { duration: "240–300 days", water: "High (1200–1500 mm)", type: "Fruit" },
  coconut: { duration: "Perennial", water: "High (1300–2000 mm)", type: "Plantation" },
  jute: { duration: "120–150 days", water: "High (1200–1500 mm)", type: "Fiber Crop" },
  coffee: { duration: "Perennial", water: "High (1500–2000 mm)", type: "Plantation" },
};

// Preset configurations
const PRESETS = {
  palakkad: {
    n: 35,
    p: 60,
    k: 32,
    ph: 5.4,
    moisture: 28,
    temp: 31,
    humidity: 80,
    rainfall: 180,
  },
  punjab: {
    n: 115,
    p: 50,
    k: 45,
    ph: 7.8,
    moisture: 18,
    temp: 22,
    humidity: 45,
    rainfall: 40,
  },
  maharashtra: {
    n: 65,
    p: 38,
    k: 42,
    ph: 7.1,
    moisture: 15,
    temp: 33,
    humidity: 40,
    rainfall: 35,
  },
  wayanad: {
    n: 80,
    p: 25,
    k: 90,
    ph: 5.8,
    moisture: 38,
    temp: 23,
    humidity: 85,
    rainfall: 210,
  },
};

// -------------------------------------------------------------
// Utility Functions
// -------------------------------------------------------------
function debounce(func, wait = 300) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

function getStatusColor(status) {
  const s = (status || "").toLowerCase();
  if (s.includes("adequate") || s.includes("optimal") || s.includes("good") || s.includes("excellent")) {
    return "#10b981"; // Emerald green
  }
  if (s.includes("monitor") || s.includes("moderate") || s.includes("high") || s.includes("acidic") || s.includes("alkaline")) {
    return "#f59e0b"; // Amber / Yellow
  }
  return "#ef4444"; // Red for Low / Critical / Poor
}

function updateLoadingState(isLoading) {
  const cards = document.querySelectorAll(
    "#section-soil-health, #section-crop-recommendations, #section-fertilizer, #section-irrigation"
  );
  cards.forEach((card) => {
    if (isLoading) card.classList.add("loading");
    else card.classList.remove("loading");
  });

  const syncTag = document.getElementById("sync-status-indicator");
  if (syncTag) {
    syncTag.textContent = isLoading ? "⏳ Processing Telemetry..." : "⚡ Auto-sync on release";
  }
}

// -------------------------------------------------------------
// Chart.js Gauge Rendering
// -------------------------------------------------------------
function renderGauge(canvasId, value, maxVal, status) {
  const ctx = document.getElementById(canvasId);
  if (!ctx) return;

  const color = getStatusColor(status);
  const clampedVal = Math.min(maxVal, Math.max(0, value));
  const remaining = Math.max(0, maxVal - clampedVal);

  if (gaugeCharts[canvasId]) {
    gaugeCharts[canvasId].data.datasets[0].data = [clampedVal, remaining];
    gaugeCharts[canvasId].data.datasets[0].backgroundColor = [color, "rgba(255, 255, 255, 0.08)"];
    gaugeCharts[canvasId].update();
  } else {
    gaugeCharts[canvasId] = new Chart(ctx, {
      type: "doughnut",
      data: {
        datasets: [
          {
            data: [clampedVal, remaining],
            backgroundColor: [color, "rgba(255, 255, 255, 0.08)"],
            borderWidth: 0,
            circumference: 180,
            rotation: 270,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "75%",
        plugins: {
          tooltip: { enabled: false },
        },
        animation: {
          duration: 500,
        },
      },
    });
  }
}

// -------------------------------------------------------------
// UI Section Renderers
// -------------------------------------------------------------
function renderSoilHealthCard(data) {
  document.getElementById("health-index-val").textContent = `${Math.round(data.soil_health_index)}`;
  const ratingEl = document.getElementById("health-rating-val");
  ratingEl.textContent = data.rating;
  ratingEl.style.color = getStatusColor(data.rating);

  const metrics = data.metrics;

  // 1. Nitrogen
  document.getElementById("val-n").textContent = metrics.nitrogen.value;
  const statusN = document.getElementById("status-n");
  statusN.textContent = metrics.nitrogen.status;
  statusN.className = `status-pill-badge status-${metrics.nitrogen.status.toLowerCase()}`;
  renderGauge("chart-n", metrics.nitrogen.value, 140, metrics.nitrogen.status);

  // 2. Phosphorus
  document.getElementById("val-p").textContent = metrics.phosphorus.value;
  const statusP = document.getElementById("status-p");
  statusP.textContent = metrics.phosphorus.status;
  statusP.className = `status-pill-badge status-${metrics.phosphorus.status.toLowerCase()}`;
  renderGauge("chart-p", metrics.phosphorus.value, 145, metrics.phosphorus.status);

  // 3. Potassium
  document.getElementById("val-k").textContent = metrics.potassium.value;
  const statusK = document.getElementById("status-k");
  statusK.textContent = metrics.potassium.status;
  statusK.className = `status-pill-badge status-${metrics.potassium.status.toLowerCase()}`;
  renderGauge("chart-k", metrics.potassium.value, 205, metrics.potassium.status);

  // 4. pH
  document.getElementById("val-ph").textContent = metrics.ph.value;
  const statusPH = document.getElementById("status-ph");
  statusPH.textContent = metrics.ph.status;
  statusPH.className = `status-pill-badge status-${metrics.ph.status.toLowerCase()}`;
  renderGauge("chart-ph", metrics.ph.value, 9.0, metrics.ph.status);

  // 5. Moisture
  document.getElementById("val-moisture").textContent = metrics.moisture.value;
  const statusMoist = document.getElementById("status-moisture");
  statusMoist.textContent = metrics.moisture.status;
  statusMoist.className = `status-pill-badge status-${metrics.moisture.status.toLowerCase()}`;
  renderGauge("chart-moisture", metrics.moisture.value, 90, metrics.moisture.status);
}

function renderCropRecommendations(data) {
  const container = document.getElementById("crop-cards-container");
  container.innerHTML = "";

  const allCrops = [
    { crop: data.top_crop, confidence: data.confidence },
    ...data.secondary_crops,
  ];

  allCrops.forEach((item, index) => {
    const cropKey = item.crop.toLowerCase();
    const meta = CROP_METADATA[cropKey] || {
      duration: "90–120 days",
      water: "Medium (500–700 mm)",
      type: "Field Crop",
    };

    const isTopChoice = index === 0;
    const isSelected = item.crop.toLowerCase() === currentSelectedCrop?.toLowerCase();

    const card = document.createElement("div");
    card.className = `crop-card ${isSelected ? "active-crop" : ""}`;
    card.onclick = () => selectCropForPrescription(item.crop);

    card.innerHTML = `
      <div>
        <div class="crop-card-top">
          <span class="crop-rank-tag">${isTopChoice ? "★ Rank 1 Top Match" : `Rank ${index + 1}`}</span>
          <span class="crop-confidence-badge">${item.confidence.toFixed(1)}%</span>
        </div>
        <h3 class="crop-name">${item.crop}</h3>
        <p class="crop-type-sub">${meta.type}</p>
      </div>
      <div class="crop-specs-list">
        <div class="crop-spec-item">
          <span class="spec-label">Growth Duration</span>
          <span class="spec-val">${meta.duration}</span>
        </div>
        <div class="crop-spec-item">
          <span class="spec-label">Water Needs</span>
          <span class="spec-val">${meta.water}</span>
        </div>
      </div>
    `;

    container.appendChild(card);
  });
}

// Cached recommendation data for reactive target crop evaluation
let lastRecData = null;

function renderTargetCropGapAnalysis(recData) {
  if (recData) lastRecData = recData;
  if (!lastRecData) return;

  const topCrop = lastRecData.top_crop || "Rice";
  const topConfidence = lastRecData.confidence || 90;
  
  // Tested crop selected in sensor screen or fallback to topCrop
  const testedKey = selectedTargetCrop ? selectedTargetCrop.toLowerCase() : topCrop.toLowerCase();
  const benchmark = CROP_BENCHMARKS[testedKey] || {
    name: testedKey.charAt(0).toUpperCase() + testedKey.slice(1),
    optimal_n: 80, min_n: 60, max_n: 100,
    optimal_p: 45, min_p: 30, max_p: 60,
    optimal_k: 40, min_k: 30, max_k: 50,
    min_ph: 6.0, max_ph: 7.2, opt_ph: 6.5,
    min_moisture: 30, max_moisture: 60, opt_moisture: 45,
    min_temp: 20, max_temp: 32, opt_temp: 26,
    min_humidity: 50, max_humidity: 85, opt_humidity: 70,
    optimal_rainfall: 120,
    advice_acidic: "Apply agricultural lime 3 weeks before planting.",
    advice_alkaline: "Incorporate gypsum and organic compost."
  };

  const testedName = benchmark.name;
  const isMatch = testedKey === topCrop.toLowerCase();

  // Read current sensor input values
  const n = parseFloat(document.getElementById("num-n")?.value || document.getElementById("slider-n")?.value || 35);
  const p = parseFloat(document.getElementById("num-p")?.value || document.getElementById("slider-p")?.value || 60);
  const k = parseFloat(document.getElementById("num-k")?.value || document.getElementById("slider-k")?.value || 32);
  const ph = parseFloat(document.getElementById("num-ph")?.value || document.getElementById("slider-ph")?.value || 5.4);
  const moisture = parseFloat(document.getElementById("num-moisture")?.value || document.getElementById("slider-moisture")?.value || 28);
  const temp = parseFloat(document.getElementById("num-temp")?.value || document.getElementById("slider-temp")?.value || 31);
  const humidity = parseFloat(document.getElementById("num-humidity")?.value || document.getElementById("slider-humidity")?.value || 80);
  const rain = parseFloat(document.getElementById("num-rainfall")?.value || document.getElementById("slider-rainfall")?.value || currentRainfall || 180);

  // Compute Suitability Score (0 - 100)
  // 1. pH Score (25 max)
  let phScore = 0;
  let phStatus = "ok";
  if (ph >= benchmark.min_ph && ph <= benchmark.max_ph) {
    phScore = 25;
    phStatus = "ok";
  } else {
    const diff = ph < benchmark.min_ph ? benchmark.min_ph - ph : ph - benchmark.max_ph;
    if (diff <= 0.6) { phScore = 15; phStatus = "warn"; }
    else { phScore = 5; phStatus = "bad"; }
  }

  // 2. NPK Score (35 max)
  const nDiff = Math.round(n - benchmark.optimal_n);
  const pDiff = Math.round(p - benchmark.optimal_p);
  const kDiff = Math.round(k - benchmark.optimal_k);
  let npkScore = 0;
  npkScore += (n >= benchmark.min_n && n <= benchmark.max_n) ? 12 : Math.max(2, 12 - Math.abs(nDiff) * 0.15);
  npkScore += (p >= benchmark.min_p && p <= benchmark.max_p) ? 12 : Math.max(2, 12 - Math.abs(pDiff) * 0.18);
  npkScore += (k >= benchmark.min_k && k <= benchmark.max_k) ? 11 : Math.max(2, 11 - Math.abs(kDiff) * 0.16);

  // 3. Moisture Score (20 max)
  let moistScore = 0;
  let moistStatus = "ok";
  if (moisture >= benchmark.min_moisture && moisture <= benchmark.max_moisture) {
    moistScore = 20;
    moistStatus = "ok";
  } else {
    const mDiff = moisture < benchmark.min_moisture ? benchmark.min_moisture - moisture : moisture - benchmark.max_moisture;
    if (mDiff <= 12) { moistScore = 12; moistStatus = "warn"; }
    else { moistScore = 5; moistStatus = "bad"; }
  }

  // 4. Climate Score (20 max)
  let climScore = 0;
  if (temp >= benchmark.min_temp && temp <= benchmark.max_temp) climScore += 10;
  else climScore += 4;
  if (humidity >= benchmark.min_humidity && humidity <= benchmark.max_humidity) climScore += 10;
  else climScore += 4;

  const totalScore = Math.min(100, Math.round(phScore + npkScore + moistScore + climScore));

  // Populate Header & Rank
  const headerRankPill = document.getElementById("gap-header-rank-pill");
  if (headerRankPill) headerRankPill.textContent = `Top Rank: ${topCrop} (${topConfidence.toFixed(1)}%)`;

  const topRankNameEl = document.getElementById("gap-top-rank-name");
  if (topRankNameEl) topRankNameEl.textContent = topCrop;

  const topRankScoreEl = document.getElementById("gap-top-rank-score");
  if (topRankScoreEl) topRankScoreEl.textContent = `${topConfidence.toFixed(1)}% AI Compatibility`;

  const testedNameEl = document.getElementById("gap-tested-crop-name");
  if (testedNameEl) testedNameEl.textContent = testedName;

  const testedScoreEl = document.getElementById("gap-tested-score-badge");
  if (testedScoreEl) {
    testedScoreEl.textContent = `${totalScore}% Compatibility`;
    testedScoreEl.className = `col-score-badge ${totalScore >= 75 ? "status-high" : totalScore >= 52 ? "status-moderate" : "status-low"}`;
  }

  const testedDescEl = document.getElementById("gap-tested-status-desc");
  if (testedDescEl) {
    if (isMatch) {
      testedDescEl.textContent = `Identical to #1 AI recommendation; naturally thriving under current soil state.`;
    } else if (totalScore >= 75) {
      testedDescEl.textContent = `Highly suitable crop for this soil. Only minor basal fertilization required.`;
    } else if (totalScore >= 52) {
      testedDescEl.textContent = `Conditionally viable; requires targeted soil amendments (NPK / pH correction).`;
    } else {
      testedDescEl.textContent = `High risk / sub-optimal without comprehensive multi-stage soil reclamation.`;
    }
  }

  // Populate Soil Health Card for Selected Crop
  const healthCard = document.getElementById("gap-soil-health-card");
  const healthIcon = document.getElementById("gap-health-icon");
  const healthTitle = document.getElementById("gap-health-title");
  const healthSummary = document.getElementById("gap-health-summary");

  if (healthCard && healthTitle && healthSummary) {
    if (isMatch || totalScore >= 75) {
      healthCard.className = "gap-soil-health-card optimal";
      healthIcon.textContent = "🟢";
      healthTitle.textContent = `Soil Health Assessment for ${testedName}: Optimal Zone (${totalScore}/100)`;
      healthSummary.innerHTML = `Current soil parameters (pH ${ph.toFixed(2)}, N: ${n}, P: ${p}, K: ${k} kg/ha) are <strong>well-balanced for ${testedName}</strong> root establishment and yield potential.`;
    } else if (totalScore >= 52) {
      healthCard.className = "gap-soil-health-card";
      healthIcon.textContent = "🟡";
      healthTitle.textContent = `Soil Health Assessment for ${testedName}: Conditionally Viable (${totalScore}/100)`;
      healthSummary.innerHTML = `Soil exhibits <strong>moderate agronomic friction</strong> for ${testedName}. Primary limiting factors: ${ph < benchmark.min_ph ? 'soil acidity (pH ' + ph.toFixed(2) + ')' : ph > benchmark.max_ph ? 'soil alkalinity' : ''}${nDiff < -15 ? ', Nitrogen deficiency (' + nDiff + ' kg/ha)' : ''}.`;
    } else {
      healthCard.className = "gap-soil-health-card hostile";
      healthIcon.textContent = "🔴";
      healthTitle.textContent = `Soil Health Assessment for ${testedName}: Hostile / Stress Zone (${totalScore}/100)`;
      healthSummary.innerHTML = `Current soil chemistry presents <strong>severe growth inhibitors</strong> for ${testedName}. Planting without prior pH correction and basal fertilization will cause root failure or severe chlorosis.`;
    }
  }

  // Populate "Why is Selected Crop Not Optimal for Current Soil?"
  const whyCropName = document.getElementById("gap-why-crop-name");
  if (whyCropName) whyCropName.textContent = testedName;

  const factorsContainer = document.getElementById("gap-factors-container");
  if (factorsContainer) {
    let factorsHtml = "";

    // Factor 1: Soil pH Diagnosis
    let phDiag = "";
    if (ph < benchmark.min_ph) {
      phDiag = `Soil pH ${ph.toFixed(2)} is too acidic for ${testedName} (Requires ${benchmark.min_ph} - ${benchmark.max_ph}). High acidity mobilizes toxic Aluminum/Iron ions and locks Phosphate ions into insoluble compounds.`;
    } else if (ph > benchmark.max_ph) {
      phDiag = `Soil pH ${ph.toFixed(2)} is too alkaline for ${testedName} (Requires ${benchmark.min_ph} - ${benchmark.max_ph}). Alkaline conditions induce Zinc and Iron chlorosis.`;
    } else {
      phDiag = `Soil pH ${ph.toFixed(2)} is ideal for ${testedName}, providing optimal bioavailability for macro and micronutrients.`;
    }
    factorsHtml += `
      <div class="gap-factor-card ${phStatus}">
        <div class="gap-factor-title">
          <span>🧪 Soil pH Variance</span>
          <span class="gap-factor-val ${phStatus}">pH ${ph.toFixed(2)} (Opt: ${benchmark.min_ph}-${benchmark.max_ph})</span>
        </div>
        <p class="gap-factor-desc">${phDiag}</p>
      </div>
    `;

    // Factor 2: Nitrogen Gap Diagnosis
    let nStatus = "ok";
    let nDiag = "";
    if (nDiff < -15) {
      nStatus = "bad";
      nDiag = `Nitrogen deficit of ${nDiff} kg/ha (Current: ${n} vs Target: ${benchmark.optimal_n} kg/ha). Stunts vegetative tillering, causes leaf chlorosis, and restricts protein synthesis.`;
    } else if (nDiff > 25) {
      nStatus = "warn";
      nDiag = `Nitrogen excess of +${nDiff} kg/ha above target. Can cause vegetative overgrowth, crop lodging, and increased vulnerability to fungal blast pathogens.`;
    } else {
      nDiag = `Available Nitrogen (${n} kg/ha) matches ${testedName}'s nutritional requirement (${benchmark.optimal_n} kg/ha).`;
    }
    factorsHtml += `
      <div class="gap-factor-card ${nStatus}">
        <div class="gap-factor-title">
          <span>🌿 Nitrogen (N) Uptake Gap</span>
          <span class="gap-factor-val ${nStatus}">${nDiff >= 0 ? '+' + nDiff : nDiff} kg/ha</span>
        </div>
        <p class="gap-factor-desc">${nDiag}</p>
      </div>
    `;

    // Factor 3: P & K Nutrient Balance
    let pkStatus = (pDiff < -10 || kDiff < -12) ? "warn" : "ok";
    let pkDiag = "";
    if (pDiff < -10 && kDiff < -12) {
      pkDiag = `Double deficit in Phosphorus (${pDiff} kg/ha) and Potassium (${kDiff} kg/ha). Limits early root ramification and post-flowering fruit/grain filling.`;
    } else if (pDiff < -10) {
      pkDiag = `Phosphorus is deficient by ${pDiff} kg/ha. Causes poor root depth, thin stalks, and delayed maturity.`;
    } else if (kDiff < -12) {
      pkDiag = `Potassium is deficient by ${kDiff} kg/ha. Reduces drought tolerance, disease resistance, and fruit/grain weight.`;
    } else {
      pkDiag = `Phosphorus (${p} kg/ha) and Potassium (${k} kg/ha) are sufficient for initial establishment.`;
    }
    factorsHtml += `
      <div class="gap-factor-card ${pkStatus}">
        <div class="gap-factor-title">
          <span>🌾 P &amp; K Nutrient Reserve</span>
          <span class="gap-factor-val ${pkStatus}">P: ${pDiff >= 0 ? '+' + pDiff : pDiff} | K: ${kDiff >= 0 ? '+' + kDiff : kDiff}</span>
        </div>
        <p class="gap-factor-desc">${pkDiag}</p>
      </div>
    `;

    // Factor 4: Moisture & Ambient Climate
    let climDiag = "";
    if (moisture < benchmark.min_moisture) {
      climDiag = `Soil moisture (${moisture}%) is below the ${benchmark.min_moisture}% hydro-threshold for ${testedName}. Evapotranspiration will induce water stress and stomatal closure.`;
    } else if (moisture > benchmark.max_moisture) {
      climDiag = `Soil moisture (${moisture}%) exceeds the ${benchmark.max_moisture}% saturation limit. Risk of poor root aeration and collar rot.`;
    } else {
      climDiag = `Moisture (${moisture}%) and ambient temperature (${temp}°C) are within the biological growth envelope.`;
    }
    factorsHtml += `
      <div class="gap-factor-card ${moistStatus}">
        <div class="gap-factor-title">
          <span>💧 Moisture &amp; Water Balance</span>
          <span class="gap-factor-val ${moistStatus}">${moisture}% (Ideal: ${benchmark.min_moisture}-${benchmark.max_moisture}%)</span>
        </div>
        <p class="gap-factor-desc">${climDiag}</p>
      </div>
    `;

    factorsContainer.innerHTML = factorsHtml;
  }

  // Populate "Recommended Actions to Make Soil Optimal"
  const actionCropName = document.getElementById("gap-action-crop-name");
  if (actionCropName) actionCropName.textContent = testedName;

  const actionsContainer = document.getElementById("gap-actions-container");
  if (actionsContainer) {
    let actionsHtml = "";

    // Action 1: pH Amendment
    if (ph < benchmark.min_ph) {
      const limeNeeded = Math.round(Math.max(400, (benchmark.opt_ph - ph) * 1200));
      actionsHtml += `
        <div class="gap-action-item">
          <div class="gap-action-step-num">1</div>
          <div class="gap-action-content">
            <div class="gap-action-head">🧪 Correct Soil Acidity via Liming</div>
            <p class="gap-action-text">Broadcast <strong>${limeNeeded} kg/acre of Agricultural Lime (CaCO₃)</strong> or Dolomite evenly across field plots 3 weeks prior to sowing. Harrow into the top 15 cm soil layer to neutralize free H⁺ and Al³⁺ ions.</p>
          </div>
        </div>
      `;
    } else if (ph > benchmark.max_ph) {
      const gypsumNeeded = Math.round(Math.max(300, (ph - benchmark.opt_ph) * 1000));
      actionsHtml += `
        <div class="gap-action-item">
          <div class="gap-action-step-num">1</div>
          <div class="gap-action-content">
            <div class="gap-action-head">🧪 Remediate Alkaline Hardpan with Gypsum</div>
            <p class="gap-action-text">Apply <strong>${gypsumNeeded} kg/acre Agricultural Gypsum (CaSO₄·2H₂O)</strong> with heavy pre-plant leaching to displace exchangeable sodium and lower pH toward neutral.</p>
          </div>
        </div>
      `;
    } else {
      actionsHtml += `
        <div class="gap-action-item">
          <div class="gap-action-step-num">1</div>
          <div class="gap-action-content">
            <div class="gap-action-head">✅ Soil pH is Optimal</div>
            <p class="gap-action-text">Soil reaction (pH ${ph.toFixed(2)}) is in the physiological sweet spot (${benchmark.min_ph} - ${benchmark.max_ph}) for ${testedName}. No chemical amendment needed.</p>
          </div>
        </div>
      `;
    }

    // Action 2: Fertilizer Split Dosage
    const ureaDose = nDiff < 0 ? Math.round(Math.abs(nDiff) * 2.17) : 25;
    const dapDose = pDiff < 0 ? Math.round(Math.abs(pDiff) * 2.17) : 15;
    const mopDose = kDiff < 0 ? Math.round(Math.abs(kDiff) * 1.67) : 20;

    actionsHtml += `
      <div class="gap-action-item">
        <div class="gap-action-step-num">2</div>
        <div class="gap-action-content">
          <div class="gap-action-head">🌾 Stoichiometric Fertilizer Compensation</div>
          <p class="gap-action-text">
            Incorporate <strong>${dapDose} kg/acre DAP</strong> as basal placement at seed depth. Top-dress <strong>${ureaDose} kg/acre Urea</strong> in 2–3 calibrated splits (at 21 and 45 days after emergence) and <strong>${mopDose} kg/acre MOP</strong> during canopy expansion to satisfy the ${testedName} uptake curve.
          </p>
        </div>
      </div>
    `;

    // Action 3: Moisture & Organic Reclamation
    const moistureAdvice = moisture < benchmark.min_moisture
      ? `Schedule a <strong>${Math.round((benchmark.opt_moisture - moisture) * 1.8)} mm depth irrigation</strong> via drip/furrow to elevate root zone moisture to ${benchmark.opt_moisture}%.`
      : moisture > benchmark.max_moisture
      ? `Establish <strong>lateral drainage furrows</strong> to shed surface pooling and prevent root hypoxia.`
      : `Maintain current irrigation schedule; moisture level (${moisture}%) aligns with FAO-56 crop transpiration demand.`;

    actionsHtml += `
      <div class="gap-action-item">
        <div class="gap-action-step-num">3</div>
        <div class="gap-action-content">
          <div class="gap-action-head">💧 Hydrological &amp; Organic Management</div>
          <p class="gap-action-text">${moistureAdvice} Blend in <strong>3–4 tonnes/acre well-rotted Farm Yard Manure (FYM)</strong> to enhance cation exchange capacity (CEC) and microbiological microbial activity.</p>
        </div>
      </div>
    `;

    actionsContainer.innerHTML = actionsHtml;
  }

  // Populate Button Labels & Event Listeners
  const btnGapCropName = document.getElementById("gap-btn-crop-name");
  if (btnGapCropName) btnGapCropName.textContent = testedName;

  const btnGapTopCropName = document.getElementById("gap-btn-top-crop-name");
  if (btnGapTopCropName) btnGapTopCropName.textContent = topCrop;

  const btnApplyPrescription = document.getElementById("btn-gap-apply-prescription");
  if (btnApplyPrescription) {
    btnApplyPrescription.onclick = () => {
      selectCropForPrescription(testedName);
      document.getElementById("section-fertilizer")?.scrollIntoView({ behavior: "smooth", block: "start" });
    };
  }

  const btnSwitchTopCrop = document.getElementById("btn-gap-switch-top-crop");
  if (btnSwitchTopCrop) {
    btnSwitchTopCrop.onclick = () => {
      selectCropForPrescription(topCrop);
      document.getElementById("section-crop-recommendations")?.scrollIntoView({ behavior: "smooth", block: "start" });
    };
  }

  const btnGotoSensor = document.getElementById("btn-gap-goto-sensor");
  if (btnGotoSensor) {
    btnGotoSensor.onclick = () => {
      document.getElementById("tab-btn-sensor")?.click();
      window.scrollTo({ top: 0, behavior: "smooth" });
    };
  }
}

function renderFertilizerTable(data) {
  document.getElementById("prescription-crop-badge").textContent = `Prescription for: ${data.selected_crop}`;
  document.getElementById("fertilizer-subtitle").textContent =
    `Nutrient deficit & commercial amendments for ${data.selected_crop} per acre`;

  const tbody = document.getElementById("fertilizer-table-body");
  tbody.innerHTML = "";

  const items = [
    {
      name: "Urea",
      composition: "46% Nitrogen (N)",
      dose: `${data.urea_kg.toFixed(2)} kg/acre`,
      purpose: "Fulfills primary vegetative Nitrogen requirement",
    },
    {
      name: "DAP (Diammonium Phosphate)",
      composition: "18% N, 46% P2O5",
      dose: `${data.dap_kg.toFixed(2)} kg/acre`,
      purpose: "Root development & early energy transfer",
    },
    {
      name: "MOP (Muriate of Potash)",
      composition: "60% Potassium (K2O)",
      dose: `${data.mop_kg.toFixed(2)} kg/acre`,
      purpose: "Disease resistance, water regulation & grain filling",
    },
  ];

  // Optional soil amendment
  if (data.lime_kg > 0) {
    items.push({
      name: "Agricultural Lime (CaCO3)",
      composition: "Calcium Carbonate",
      dose: `${data.lime_kg.toFixed(2)} kg/acre`,
      purpose: "Acidic soil remediation — raises pH toward 6.5",
    });
  } else if (data.gypsum_kg > 0) {
    items.push({
      name: "Agricultural Gypsum (CaSO4·2H2O)",
      composition: "Calcium Sulfate",
      dose: `${data.gypsum_kg.toFixed(2)} kg/acre`,
      purpose: "Alkaline soil remediation — lowers pH toward 7.0",
    });
  }

  items.forEach((item) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td class="fert-name">${item.name}</td>
      <td>${item.composition}</td>
      <td class="fert-dose">${item.dose}</td>
      <td style="color: var(--text-muted); font-size: 0.8rem;">${item.purpose}</td>
    `;
    tbody.appendChild(row);
  });
}

function renderIrrigationBanner(data) {
  const banner = document.getElementById("irrigation-banner");
  const icon = document.getElementById("irrigation-icon");
  const title = document.getElementById("irrigation-status-text");
  const desc = document.getElementById("irrigation-description");
  const pumpChip = document.getElementById("pump-runtime-chip");

  banner.className = "irrigation-banner";

  if (data.status === "CRITICAL_IRRIGATE") {
    banner.classList.add("critical");
    icon.textContent = "🔴";
    title.textContent = `CRITICAL IRRIGATE — Soil Water Below RAW Threshold (${data.raw_threshold}%)`;
    desc.textContent =
      `Soil moisture (${data.current_moisture}%) is deficient by ${data.deficit_mm} mm. ` +
      `Initiate irrigation immediately to avoid crop water stress.`;
    pumpChip.style.display = "inline-flex";
    document.getElementById("val-runtime").textContent = `${data.pump_runtime_hours.toFixed(2)}`;
  } else if (data.status === "MONITOR") {
    banner.classList.add("monitor");
    icon.textContent = "🟡";
    title.textContent = `MONITOR — Depletion Projected Within 24 Hours`;
    desc.textContent =
      `Soil moisture is currently ${data.current_moisture}%. With daily ETc at ${data.etc_mm_per_day} mm, ` +
      `moisture will breach the RAW threshold within the daily cycle. Prepare pumps.`;
    pumpChip.style.display = "none";
  } else {
    banner.classList.add("optimal");
    icon.textContent = "🟢";
    title.textContent = `OPTIMAL — Soil Moisture Sufficient`;
    desc.textContent =
      `Soil moisture (${data.current_moisture}%) is well above allowable depletion. No immediate irrigation required.`;
    pumpChip.style.display = "none";
  }

  document.getElementById("val-et0").textContent = data.et0_mm_per_day.toFixed(2);
  document.getElementById("val-kc").textContent = data.kc.toFixed(2);
  document.getElementById("val-etc").textContent = data.etc_mm_per_day.toFixed(2);
  document.getElementById("val-raw").textContent = data.raw_threshold.toFixed(1);
}

// -------------------------------------------------------------
// Current telemetry values
let currentRainfall = 180.0;

// -------------------------------------------------------------
// Orchestrated Telemetry Pipeline
// -------------------------------------------------------------
async function executeTelemetryPipeline() {
  updateLoadingState(true);

  const rainVal = parseFloat(
    document.getElementById("slider-rainfall")?.value ||
    document.getElementById("num-rainfall")?.value ||
    currentRainfall ||
    180
  );
  currentRainfall = rainVal;

  const payload = {
    machine_id: "ESP32-S3-KRISHI-01",
    n: parseFloat(document.getElementById("slider-n")?.value || document.getElementById("num-n")?.value || 35),
    p: parseFloat(document.getElementById("slider-p")?.value || document.getElementById("num-p")?.value || 60),
    k: parseFloat(document.getElementById("slider-k")?.value || document.getElementById("num-k")?.value || 32),
    ph: parseFloat(document.getElementById("slider-ph")?.value || document.getElementById("num-ph")?.value || 5.4),
    moisture: parseFloat(document.getElementById("slider-moisture")?.value || document.getElementById("num-moisture")?.value || 28),
    temperature: parseFloat(document.getElementById("slider-temp")?.value || document.getElementById("num-temp")?.value || 31),
    humidity: parseFloat(document.getElementById("slider-humidity")?.value || document.getElementById("num-humidity")?.value || 80),
    rainfall: rainVal,
  };

  try {
    // 1. Post Telemetry
    const telRes = await fetch("/api/telemetry", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!telRes.ok) {
      throw new Error(`Telemetry API error: ${telRes.statusText}`);
    }
    const telemetry = await telRes.json();
    currentTelemetryId = telemetry.id;

    // Update live telemetry context banner in Kisan AI section
    const ctxSummary = document.getElementById("ctx-telemetry-summary");
    if (ctxSummary) {
      ctxSummary.innerHTML = `<strong>N:</strong> ${payload.n} | <strong>P:</strong> ${payload.p} | <strong>K:</strong> ${payload.k} kg/ha &nbsp;•&nbsp; <strong>pH:</strong> ${payload.ph} &nbsp;•&nbsp; <strong>Moisture:</strong> ${payload.moisture}% &nbsp;•&nbsp; <span style="color: var(--primary-light)">Record #${currentTelemetryId}</span>`;
    }

    // Update connection indicator to connected
    const statusText = document.getElementById("system-status-text");
    if (statusText) {
      statusText.textContent = "Connected: MySQL & AI Engine";
      statusText.style.color = "var(--primary-light)";
    }
    const indicator = document.getElementById("live-indicator");
    if (indicator) {
      indicator.style.background = "var(--primary)";
      indicator.style.boxShadow = "0 0 10px var(--primary)";
    }

    // 2. Fetch Soil Health Card & Recommendations in parallel
    const [healthRes, recRes] = await Promise.all([
      fetch(`/api/soil-health-card?telemetry_id=${currentTelemetryId}`),
      fetch("/api/recommend-crops", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ telemetry_id: currentTelemetryId }),
      }),
    ]);

    if (healthRes.ok) {
      const healthData = await healthRes.json();
      renderSoilHealthCard(healthData);
    }

    if (recRes.ok) {
      const recData = await recRes.json();
      currentRecommendationId = recData.recommendation_id;
      // If user selected a specific target crop, prioritize it for prescription & irrigation
      if (selectedTargetCrop && CROP_BENCHMARKS[selectedTargetCrop]) {
        currentSelectedCrop = selectedTargetCrop;
      } else {
        currentSelectedCrop = recData.top_crop;
      }
      renderCropRecommendations(recData);

      // 3. Compute Fertilizer Prescription & Irrigation for the selected crop
      await updateCropDependentAdvisories(currentRecommendationId, currentSelectedCrop);

      // Render Target Crop Gap & Feasibility Intelligence on User Interface
      if (typeof renderTargetCropGapAnalysis === "function") {
        renderTargetCropGapAnalysis(recData);
      }

      // Refresh crop suitability badge with updated telemetry
      if (typeof evaluateTargetCropSuitability === "function") {
        evaluateTargetCropSuitability();
      }
    } else {
      const cropContainer = document.getElementById("crop-cards-container");
      if (cropContainer) {
        cropContainer.innerHTML =
          '<div class="loading-placeholder" style="color: var(--status-yellow);">' +
          '⚠️ Crop recommendation model not loaded.<br>Run <code>python ml/train_model.py</code> in the terminal to initialize the Random Forest model.</div>';
      }
    }
  } catch (err) {
    console.error("Pipeline error:", err);
    const statusText = document.getElementById("system-status-text");
    if (statusText) {
      statusText.textContent = "Backend/DB Offline — Ensure Uvicorn & MySQL are running";
      statusText.style.color = "#ef4444";
    }
    const indicator = document.getElementById("live-indicator");
    if (indicator) {
      indicator.style.background = "#ef4444";
      indicator.style.boxShadow = "0 0 10px #ef4444";
    }
  } finally {
    updateLoadingState(false);
  }
}

async function updateCropDependentAdvisories(recommendationId, cropName) {
  try {
    const [fertRes, irriRes] = await Promise.all([
      fetch("/api/fertilizer-prescription", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recommendation_id: recommendationId,
          selected_crop: cropName,
        }),
      }),
      fetch(
        `/api/irrigation-advisory?telemetry_id=${currentTelemetryId}&crop=${encodeURIComponent(
          cropName
        )}&growth_stage=mid`
      ),
    ]);

    if (fertRes.ok) {
      const fertData = await fertRes.json();
      renderFertilizerTable(fertData);
    }

    if (irriRes.ok) {
      const irriData = await irriRes.json();
      renderIrrigationBanner(irriData);
    }
  } catch (err) {
    console.error("Advisory error:", err);
  }
}

async function selectCropForPrescription(cropName) {
  currentSelectedCrop = cropName;

  // Highlight active crop card
  document.querySelectorAll(".crop-card").forEach((card) => {
    const nameEl = card.querySelector(".crop-name");
    if (nameEl && nameEl.textContent.trim().toLowerCase() === cropName.toLowerCase()) {
      card.classList.add("active-crop");
    } else {
      card.classList.remove("active-crop");
    }
  });

  if (currentRecommendationId) {
    updateLoadingState(true);
    await updateCropDependentAdvisories(currentRecommendationId, cropName);
    updateLoadingState(false);
  }
}

// -------------------------------------------------------------
// Gemini AI Agronomic Intelligence (Removed from UI)
// -------------------------------------------------------------
async function fetchAndRenderCropAiBriefing(cropName, telemetryId) {
  // Section removed from user interface as requested
  return;
}


// -------------------------------------------------------------
// Slider & Dual-Control Preset Listeners
// -------------------------------------------------------------
const debouncedPipeline = debounce(executeTelemetryPipeline, 350);

function updatePhChip(phVal) {
  const chip = document.getElementById("ph-state-chip");
  if (!chip) return;
  const ph = parseFloat(phVal);
  if (isNaN(ph)) return;

  if (ph < 6.0) {
    chip.textContent = `Condition: Acidic (pH ${ph.toFixed(2)}) • Agricultural Lime Ca(OH)₂ Needed`;
    chip.style.color = "#f87171";
  } else if (ph > 7.5) {
    chip.textContent = `Condition: Alkaline (pH ${ph.toFixed(2)}) • Gypsum CaSO₄ Needed`;
    chip.style.color = "#60a5fa";
  } else {
    chip.textContent = `Condition: Optimal Neutral (pH ${ph.toFixed(2)}) • Temp Compensated: 25°C`;
    chip.style.color = "#34d399";
  }
}

function bindDualControl(sliderId, numId, labelId, suffix = "", onUpdateCallback = null) {
  const slider = document.getElementById(sliderId);
  const numInput = document.getElementById(numId);
  const label = document.getElementById(labelId);

  // Sync Slider -> Number Input
  if (slider) {
    slider.addEventListener("input", () => {
      const val = slider.value;
      if (numInput && numInput.value !== val) {
        numInput.value = val;
      }
      if (label) {
        label.textContent = `${val} ${suffix}`.trim();
      }
      if (typeof onUpdateCallback === "function") {
        onUpdateCallback(val);
      }
      if (typeof updateRawTelemetryOutput === "function") {
        updateRawTelemetryOutput();
      }
      if (typeof evaluateTargetCropSuitability === "function") {
        evaluateTargetCropSuitability();
      }
      if (typeof renderTargetCropGapAnalysis === "function" && lastRecData) {
        renderTargetCropGapAnalysis(lastRecData);
      }
    });

    slider.addEventListener("change", () => {
      debouncedPipeline();
    });
  }

  // Sync Number Input -> Slider
  if (numInput) {
    numInput.addEventListener("input", () => {
      const raw = parseFloat(numInput.value);
      if (isNaN(raw)) return;

      if (slider) {
        slider.value = numInput.value;
      }
      if (label) {
        label.textContent = `${numInput.value} ${suffix}`.trim();
      }
      if (typeof onUpdateCallback === "function") {
        onUpdateCallback(numInput.value);
      }
      if (typeof updateRawTelemetryOutput === "function") {
        updateRawTelemetryOutput();
      }
      if (typeof evaluateTargetCropSuitability === "function") {
        evaluateTargetCropSuitability();
      }
      if (typeof renderTargetCropGapAnalysis === "function" && lastRecData) {
        renderTargetCropGapAnalysis(lastRecData);
      }
    });

    numInput.addEventListener("change", () => {
      debouncedPipeline();
    });
  }
}

// Backwards-compatible bindSlider
function bindSlider(sliderId, labelId, suffix = "") {
  const numId = sliderId.replace("slider-", "num-");
  const callback = sliderId === "slider-ph" ? updatePhChip : null;
  bindDualControl(sliderId, numId, labelId, suffix, callback);
}

function applyPreset(preset) {
  currentRainfall = preset.rainfall || 120.0;

  const setPair = (sliderId, numId, lblId, val, suffix) => {
    const s = document.getElementById(sliderId);
    const n = document.getElementById(numId);
    const l = document.getElementById(lblId);
    if (s) s.value = val;
    if (n) n.value = val;
    if (l) l.textContent = `${val} ${suffix}`.trim();
  };

  setPair("slider-n", "num-n", "lbl-n", preset.n, "kg/ha");
  setPair("slider-p", "num-p", "lbl-p", preset.p, "kg/ha");
  setPair("slider-k", "num-k", "lbl-k", preset.k, "kg/ha");
  setPair("slider-ph", "num-ph", "lbl-ph", typeof preset.ph === "number" ? preset.ph.toFixed(2) : preset.ph, "");
  setPair("slider-moisture", "num-moisture", "lbl-moisture", preset.moisture, "%");
  setPair("slider-temp", "num-temp", "lbl-temp", preset.temp, "°C");
  setPair("slider-humidity", "num-humidity", "lbl-humidity", preset.humidity, "%");
  setPair("slider-rainfall", "num-rainfall", "lbl-rainfall", preset.rainfall || 120, "mm");

  updatePhChip(preset.ph);

  // Immediately dispatch pipeline on preset click
  executeTelemetryPipeline();
  if (typeof evaluateTargetCropSuitability === "function") {
    evaluateTargetCropSuitability();
  }
  if (typeof updateRawTelemetryOutput === "function") {
    updateRawTelemetryOutput();
  }
}

// -------------------------------------------------------------
// Scientific Crop Feasibility Benchmarks & Real-Time Suitability Engine
// -------------------------------------------------------------
const CROP_BENCHMARKS = {
  rice: {
    name: "Rice (Paddy)",
    optimal_n: 80, min_n: 60, max_n: 100,
    optimal_p: 48, min_p: 35, max_p: 60,
    optimal_k: 40, min_k: 30, max_k: 50,
    min_ph: 5.5, max_ph: 6.8, opt_ph: 6.2,
    min_moisture: 45, max_moisture: 85, opt_moisture: 65,
    min_temp: 20, max_temp: 35, opt_temp: 28,
    min_humidity: 60, max_humidity: 95, opt_humidity: 80,
    optimal_rainfall: 200,
    advice_acidic: "Tolerates slightly acidic submerged soil (pH > 5.5). If pH < 5.5, apply 1.0 t/ha agricultural lime to prevent Al toxicity.",
    advice_alkaline: "Alkaline soil inhibits micronutrients. Apply 150 kg/acre gypsum to buffer alkalinity.",
  },
  wheat: {
    name: "Wheat",
    optimal_n: 120, min_n: 90, max_n: 140,
    optimal_p: 55, min_p: 40, max_p: 70,
    optimal_k: 45, min_k: 35, max_k: 55,
    min_ph: 6.0, max_ph: 7.5, opt_ph: 6.8,
    min_moisture: 30, max_moisture: 55, opt_moisture: 40,
    min_temp: 15, max_temp: 26, opt_temp: 22,
    min_humidity: 40, max_humidity: 65, opt_humidity: 50,
    optimal_rainfall: 50,
    advice_acidic: "Wheat is highly sensitive to soil acidity. Apply 600-800 kg/acre agricultural lime 2-3 weeks before sowing.",
    advice_alkaline: "Prefers neutral to slightly alkaline alluvial loams. Supply zinc sulfate (10 kg/acre) as basal.",
  },
  maize: {
    name: "Maize (Corn)",
    optimal_n: 90, min_n: 70, max_n: 110,
    optimal_p: 48, min_p: 35, max_p: 60,
    optimal_k: 30, min_k: 20, max_k: 40,
    min_ph: 5.8, max_ph: 7.2, opt_ph: 6.5,
    min_moisture: 30, max_moisture: 60, opt_moisture: 45,
    min_temp: 18, max_temp: 32, opt_temp: 26,
    min_humidity: 50, max_humidity: 75, opt_humidity: 65,
    optimal_rainfall: 80,
    advice_acidic: "Lime acidic soils (<5.8) with 500 kg/acre calcite to improve nitrogen use efficiency.",
    advice_alkaline: "Requires good drainage; avoid salinity and water stagnation.",
  },
  cotton: {
    name: "Cotton",
    optimal_n: 120, min_n: 90, max_n: 140,
    optimal_p: 46, min_p: 35, max_p: 60,
    optimal_k: 25, min_k: 15, max_k: 35,
    min_ph: 6.0, max_ph: 7.8, opt_ph: 7.0,
    min_moisture: 20, max_moisture: 45, opt_moisture: 30,
    min_temp: 22, max_temp: 35, opt_temp: 30,
    min_humidity: 35, max_humidity: 60, opt_humidity: 45,
    optimal_rainfall: 65,
    advice_acidic: "Cotton fails in acidic vertisols. Apply 800 kg/acre agricultural lime.",
    advice_alkaline: "Thrives in deep black cotton soils (vertisols) up to pH 7.8.",
  },
  banana: {
    name: "Banana",
    optimal_n: 100, min_n: 80, max_n: 120,
    optimal_p: 75, min_p: 60, max_p: 90,
    optimal_k: 50, min_k: 40, max_k: 60,
    min_ph: 5.5, max_ph: 7.0, opt_ph: 6.5,
    min_moisture: 55, max_moisture: 80, opt_moisture: 65,
    min_temp: 22, max_temp: 32, opt_temp: 27,
    min_humidity: 65, max_humidity: 90, opt_humidity: 80,
    optimal_rainfall: 110,
    advice_acidic: "Heavy potassium feeder. If pH < 5.5, apply dolomite (contains Mg) at 500g/plant.",
    advice_alkaline: "Ensure adequate organic mulch to buffer high pH and retain soil moisture.",
  },
  coffee: {
    name: "Coffee",
    optimal_n: 100, min_n: 80, max_n: 115,
    optimal_p: 30, min_p: 20, max_p: 40,
    optimal_k: 30, min_k: 20, max_k: 40,
    min_ph: 5.8, max_ph: 6.8, opt_ph: 6.2,
    min_moisture: 35, max_moisture: 65, opt_moisture: 50,
    min_temp: 18, max_temp: 28, opt_temp: 24,
    min_humidity: 65, max_humidity: 90, opt_humidity: 80,
    optimal_rainfall: 180,
    advice_acidic: "Coffee prefers porous acidic highland soil (pH 5.8-6.5). If pH < 5.2 apply 300 kg/acre lime.",
    advice_alkaline: "Alkaline soils cause iron chlorosis. Not suitable for soils above pH 7.2.",
  },
  apple: {
    name: "Apple",
    optimal_n: 25, min_n: 15, max_n: 35,
    optimal_p: 135, min_p: 115, max_p: 145,
    optimal_k: 200, min_k: 185, max_k: 205,
    min_ph: 5.5, max_ph: 6.8, opt_ph: 6.2,
    min_moisture: 30, max_moisture: 55, opt_moisture: 40,
    min_temp: 15, max_temp: 25, opt_temp: 21,
    min_humidity: 45, max_humidity: 70, opt_humidity: 55,
    optimal_rainfall: 115,
    advice_acidic: "Requires temperate climate and chilling hours. Apply 500 kg/acre lime if pH < 5.5.",
    advice_alkaline: "High pH causes severe zinc and iron deficiencies in fruit trees.",
  },
  chickpea: {
    name: "Chickpea (Gram)",
    optimal_n: 40, min_n: 20, max_n: 45,
    optimal_p: 68, min_p: 55, max_p: 80,
    optimal_k: 80, min_k: 65, max_k: 90,
    min_ph: 6.0, max_ph: 7.5, opt_ph: 6.8,
    min_moisture: 20, max_moisture: 40, opt_moisture: 28,
    min_temp: 15, max_temp: 25, opt_temp: 20,
    min_humidity: 40, max_humidity: 60, opt_humidity: 50,
    optimal_rainfall: 75,
    advice_acidic: "Legume root nodulation inhibited in acidic soil. Apply 500 kg/acre lime.",
    advice_alkaline: "Tolerates moderate alkaline conditions well.",
  },
  kidneybeans: {
    name: "Kidney Beans (Rajma)",
    optimal_n: 25, min_n: 15, max_n: 35,
    optimal_p: 67, min_p: 55, max_p: 80,
    optimal_k: 20, min_k: 15, max_k: 25,
    min_ph: 5.5, max_ph: 6.5, opt_ph: 6.0,
    min_moisture: 25, max_moisture: 45, opt_moisture: 35,
    min_temp: 15, max_temp: 24, opt_temp: 19,
    min_humidity: 50, max_humidity: 70, opt_humidity: 60,
    optimal_rainfall: 105,
    advice_acidic: "Apply organic compost and seed Rhizobium inoculation.",
    advice_alkaline: "Sensitive to waterlogging and alkalinity.",
  },
  pigeonpeas: {
    name: "Pigeonpeas (Arhar / Toor)",
    optimal_n: 25, min_n: 15, max_n: 35,
    optimal_p: 68, min_p: 55, max_p: 80,
    optimal_k: 20, min_k: 15, max_k: 25,
    min_ph: 5.5, max_ph: 7.5, opt_ph: 6.5,
    min_moisture: 20, max_moisture: 40, opt_moisture: 28,
    min_temp: 20, max_temp: 35, opt_temp: 28,
    min_humidity: 40, max_humidity: 70, opt_humidity: 55,
    optimal_rainfall: 150,
    advice_acidic: "Deep taproot tolerates moderate acidity.",
    advice_alkaline: "Well-suited for black soils.",
  },
  mothbeans: {
    name: "Mothbeans",
    optimal_n: 20, min_n: 10, max_n: 30,
    optimal_p: 48, min_p: 35, max_p: 60,
    optimal_k: 20, min_k: 15, max_k: 25,
    min_ph: 5.5, max_ph: 7.8, opt_ph: 6.8,
    min_moisture: 15, max_moisture: 30, opt_moisture: 20,
    min_temp: 24, max_temp: 34, opt_temp: 28,
    min_humidity: 30, max_humidity: 55, opt_humidity: 40,
    optimal_rainfall: 50,
    advice_acidic: "Extreme drought-hardy arid pulse.",
    advice_alkaline: "Tolerates dry alkaline soils.",
  },
  mungbean: {
    name: "Mungbean (Green Gram)",
    optimal_n: 20, min_n: 15, max_n: 30,
    optimal_p: 48, min_p: 35, max_p: 60,
    optimal_k: 20, min_k: 15, max_k: 25,
    min_ph: 6.2, max_ph: 7.5, opt_ph: 6.8,
    min_moisture: 20, max_moisture: 35, opt_moisture: 26,
    min_temp: 25, max_temp: 35, opt_temp: 28,
    min_humidity: 50, max_humidity: 70, opt_humidity: 60,
    optimal_rainfall: 50,
    advice_acidic: "Incorporate lime if soil pH < 6.0.",
    advice_alkaline: "Tolerant to neutral-alkaline loams.",
  },
  blackgram: {
    name: "Blackgram (Urad)",
    optimal_n: 40, min_n: 30, max_n: 50,
    optimal_p: 67, min_p: 55, max_p: 80,
    optimal_k: 20, min_k: 15, max_k: 25,
    min_ph: 6.5, max_ph: 7.8, opt_ph: 7.0,
    min_moisture: 20, max_moisture: 40, opt_moisture: 30,
    min_temp: 25, max_temp: 35, opt_temp: 28,
    min_humidity: 55, max_humidity: 75, opt_humidity: 65,
    optimal_rainfall: 65,
    advice_acidic: "Requires neutral loams.",
    advice_alkaline: "Grows well in black soils.",
  },
  lentil: {
    name: "Lentil (Masoor)",
    optimal_n: 20, min_n: 15, max_n: 30,
    optimal_p: 68, min_p: 55, max_p: 80,
    optimal_k: 20, min_k: 15, max_k: 25,
    min_ph: 6.0, max_ph: 7.5, opt_ph: 6.8,
    min_moisture: 20, max_moisture: 35, opt_moisture: 25,
    min_temp: 15, max_temp: 25, opt_temp: 20,
    min_humidity: 45, max_humidity: 65, opt_humidity: 55,
    optimal_rainfall: 45,
    advice_acidic: "Lime required for acidic sandy loams.",
    advice_alkaline: "Prefers cool season neutral soil.",
  },
  pomegranate: {
    name: "Pomegranate",
    optimal_n: 20, min_n: 15, max_n: 30,
    optimal_p: 20, min_p: 10, max_p: 30,
    optimal_k: 40, min_k: 30, max_k: 50,
    min_ph: 5.5, max_ph: 7.5, opt_ph: 6.5,
    min_moisture: 20, max_moisture: 40, opt_moisture: 30,
    min_temp: 20, max_temp: 35, opt_temp: 28,
    min_humidity: 35, max_humidity: 60, opt_humidity: 45,
    optimal_rainfall: 105,
    advice_acidic: "Prefers well-drained light loams.",
    advice_alkaline: "Tolerates slightly alkaline soils up to pH 7.5.",
  },
  mango: {
    name: "Mango",
    optimal_n: 20, min_n: 15, max_n: 30,
    optimal_p: 27, min_p: 20, max_p: 35,
    optimal_k: 30, min_k: 20, max_k: 40,
    min_ph: 5.5, max_ph: 7.5, opt_ph: 6.5,
    min_moisture: 25, max_moisture: 50, opt_moisture: 35,
    min_temp: 25, max_temp: 38, opt_temp: 31,
    min_humidity: 45, max_humidity: 70, opt_humidity: 55,
    optimal_rainfall: 95,
    advice_acidic: "Deep alluvial soils with pH 5.5-7.5.",
    advice_alkaline: "Avoid shallow rocky soils.",
  },
  grapes: {
    name: "Grapes",
    optimal_n: 23, min_n: 15, max_n: 30,
    optimal_p: 132, min_p: 115, max_p: 145,
    optimal_k: 200, min_k: 185, max_k: 205,
    min_ph: 5.5, max_ph: 7.0, opt_ph: 6.5,
    min_moisture: 30, max_moisture: 50, opt_moisture: 38,
    min_temp: 15, max_temp: 35, opt_temp: 24,
    min_humidity: 40, max_humidity: 65, opt_humidity: 50,
    optimal_rainfall: 70,
    advice_acidic: "High potassium and phosphorus demand for berry sugar content.",
    advice_alkaline: "Requires well-drained gravelly loam.",
  },
  watermelon: {
    name: "Watermelon",
    optimal_n: 100, min_n: 80, max_n: 120,
    optimal_p: 18, min_p: 10, max_p: 25,
    optimal_k: 50, min_k: 40, max_k: 60,
    min_ph: 6.0, max_ph: 7.0, opt_ph: 6.5,
    min_moisture: 30, max_moisture: 50, opt_moisture: 38,
    min_temp: 24, max_temp: 30, opt_temp: 26,
    min_humidity: 45, max_humidity: 65, opt_humidity: 55,
    optimal_rainfall: 50,
    advice_acidic: "Sandy loam river beds with neutral pH are ideal.",
    advice_alkaline: "Avoid waterlogged clay.",
  },
  muskmelon: {
    name: "Muskmelon",
    optimal_n: 100, min_n: 80, max_n: 120,
    optimal_p: 18, min_p: 10, max_p: 25,
    optimal_k: 50, min_k: 40, max_k: 60,
    min_ph: 6.0, max_ph: 7.0, opt_ph: 6.5,
    min_moisture: 30, max_moisture: 50, opt_moisture: 38,
    min_temp: 26, max_temp: 32, opt_temp: 29,
    min_humidity: 40, max_humidity: 60, opt_humidity: 50,
    optimal_rainfall: 25,
    advice_acidic: "Warm dry climate during fruit ripening.",
    advice_alkaline: "Neutral sandy loam preferred.",
  },
  orange: {
    name: "Orange / Citrus",
    optimal_n: 20, min_n: 15, max_n: 30,
    optimal_p: 17, min_p: 10, max_p: 25,
    optimal_k: 10, min_k: 5, max_k: 15,
    min_ph: 6.0, max_ph: 7.5, opt_ph: 6.5,
    min_moisture: 30, max_moisture: 55, opt_moisture: 40,
    min_temp: 15, max_temp: 35, opt_temp: 25,
    min_humidity: 50, max_humidity: 75, opt_humidity: 60,
    optimal_rainfall: 110,
    advice_acidic: "Sub-tropical or tropical; deep well-aerated soil.",
    advice_alkaline: "Avoid calcareous subsoil hardpan.",
  },
  papaya: {
    name: "Papaya",
    optimal_n: 50, min_n: 40, max_n: 60,
    optimal_p: 60, min_p: 50, max_p: 70,
    optimal_k: 50, min_k: 40, max_k: 60,
    min_ph: 6.0, max_ph: 7.0, opt_ph: 6.5,
    min_moisture: 40, max_moisture: 60, opt_moisture: 48,
    min_temp: 25, max_temp: 38, opt_temp: 32,
    min_humidity: 60, max_humidity: 85, opt_humidity: 72,
    optimal_rainfall: 190,
    advice_acidic: "Susceptible to collar rot; raise planting mounds.",
    advice_alkaline: "Rich loam with high organic matter.",
  },
  coconut: {
    name: "Coconut",
    optimal_n: 22, min_n: 15, max_n: 30,
    optimal_p: 17, min_p: 10, max_p: 25,
    optimal_k: 30, min_k: 20, max_k: 40,
    min_ph: 5.2, max_ph: 7.5, opt_ph: 6.2,
    min_moisture: 50, max_moisture: 80, opt_moisture: 60,
    min_temp: 24, max_temp: 32, opt_temp: 27,
    min_humidity: 70, max_humidity: 90, opt_humidity: 80,
    optimal_rainfall: 175,
    advice_acidic: "Coastal alluvium or red loam; tolerates acidity down to 5.2.",
    advice_alkaline: "Ensure regular salt/potash application in non-coastal areas.",
  },
  jute: {
    name: "Jute",
    optimal_n: 80, min_n: 60, max_n: 100,
    optimal_p: 46, min_p: 35, max_p: 60,
    optimal_k: 40, min_k: 30, max_k: 50,
    min_ph: 6.0, max_ph: 7.5, opt_ph: 6.8,
    min_moisture: 50, max_moisture: 80, opt_moisture: 65,
    min_temp: 24, max_temp: 35, opt_temp: 30,
    min_humidity: 70, max_humidity: 90, opt_humidity: 80,
    optimal_rainfall: 175,
    advice_acidic: "Requires warm humid monsoon climate and standing water for retting.",
    advice_alkaline: "Floodplain alluvial silt is ideal.",
  }
};

let selectedTargetCrop = null;

function evaluateTargetCropSuitability() {
  const verdictEl = document.getElementById("crop-suitability-verdict");
  const scoreNumEl = document.getElementById("crop-suitability-score-num");
  const scoreBadge = document.getElementById("crop-suitability-score-badge");
  const summaryEl = document.getElementById("crop-suitability-summary");
  const breakdownGrid = document.getElementById("crop-suitability-breakdown");
  const adviceBox = document.getElementById("crop-suitability-advice");
  const adviceText = document.getElementById("crop-suitability-advice-text");

  if (!verdictEl || !scoreNumEl || !scoreBadge || !summaryEl) return;

  if (!selectedTargetCrop || !CROP_BENCHMARKS[selectedTargetCrop]) {
    scoreNumEl.textContent = "--";
    verdictEl.textContent = "Select a crop above";
    scoreBadge.className = "suitability-score-badge";
    summaryEl.textContent = "Select a crop from the dropdown or click a quick crop chip to test if your currently inputted soil and climate conditions can support it.";
    if (breakdownGrid) breakdownGrid.classList.add("hidden");
    if (adviceBox) adviceBox.classList.add("hidden");
    return;
  }

  const crop = CROP_BENCHMARKS[selectedTargetCrop];
  if (breakdownGrid) breakdownGrid.classList.remove("hidden");
  if (adviceBox) adviceBox.classList.remove("hidden");

  // Read current sensor input values
  const n = parseFloat(document.getElementById("num-n")?.value || document.getElementById("slider-n")?.value || 35);
  const p = parseFloat(document.getElementById("num-p")?.value || document.getElementById("slider-p")?.value || 60);
  const k = parseFloat(document.getElementById("num-k")?.value || document.getElementById("slider-k")?.value || 32);
  const ph = parseFloat(document.getElementById("num-ph")?.value || document.getElementById("slider-ph")?.value || 5.4);
  const moisture = parseFloat(document.getElementById("num-moisture")?.value || document.getElementById("slider-moisture")?.value || 28);
  const temp = parseFloat(document.getElementById("num-temp")?.value || document.getElementById("slider-temp")?.value || 31);
  const humidity = parseFloat(document.getElementById("num-humidity")?.value || document.getElementById("slider-humidity")?.value || 80);
  const rain = parseFloat(document.getElementById("num-rainfall")?.value || document.getElementById("slider-rainfall")?.value || currentRainfall || 180);

  // 1. pH Score (25 max)
  let phScore = 0;
  let phStatus = "ok";
  let phMsg = "";
  if (ph >= crop.min_ph && ph <= crop.max_ph) {
    phScore = 25;
    phStatus = "ok";
    phMsg = `pH ${ph.toFixed(2)} is within optimal range (${crop.min_ph} - ${crop.max_ph}).`;
  } else {
    const diff = ph < crop.min_ph ? crop.min_ph - ph : ph - crop.max_ph;
    if (diff <= 0.6) {
      phScore = 15;
      phStatus = "warn";
      phMsg = ph < crop.min_ph 
        ? `Soil is slightly acidic for ${crop.name} (Tol: ${crop.min_ph} - ${crop.max_ph}). Light liming advised.` 
        : `Soil is slightly alkaline for ${crop.name} (Tol: ${crop.min_ph} - ${crop.max_ph}). Gypsum advised.`;
    } else {
      phScore = 5;
      phStatus = "bad";
      phMsg = ph < crop.min_ph
        ? `Soil is too acidic (pH ${ph.toFixed(2)}) for ${crop.name}. Heavy liming required before sowing.`
        : `Soil is too alkaline (pH ${ph.toFixed(2)}) for ${crop.name}. Remediation required.`;
    }
  }

  // 2. NPK Score (35 max)
  const nRatio = Math.min(1.2, n / crop.optimal_n);
  const pRatio = Math.min(1.2, p / crop.optimal_p);
  const kRatio = Math.min(1.2, k / crop.optimal_k);

  const nScore = (nRatio >= 0.75) ? 15 : (nRatio >= 0.4 ? 8 : 2);
  const pScore = (pRatio >= 0.7) ? 10 : (pRatio >= 0.35 ? 6 : 2);
  const kScore = (kRatio >= 0.7) ? 10 : (kRatio >= 0.35 ? 6 : 2);
  const npkScore = nScore + pScore + kScore;

  const nDiff = Math.round(n - crop.optimal_n);
  const pDiff = Math.round(p - crop.optimal_p);
  const kDiff = Math.round(k - crop.optimal_k);

  // 3. Moisture & Water Score (20 max)
  let moistScore = 0;
  let moistStatus = "ok";
  if (moisture >= crop.min_moisture && moisture <= crop.max_moisture) {
    moistScore = 20;
    moistStatus = "ok";
  } else if (Math.abs(moisture - crop.opt_moisture) <= 15) {
    moistScore = 12;
    moistStatus = "warn";
  } else {
    moistScore = 5;
    moistStatus = "bad";
  }

  // 4. Climate Score (20 max)
  let climScore = 0;
  if (temp >= crop.min_temp && temp <= crop.max_temp) climScore += 10;
  else climScore += 4;
  if (humidity >= crop.min_humidity && humidity <= crop.max_humidity) climScore += 10;
  else climScore += 4;

  const totalScore = Math.min(100, Math.round(phScore + npkScore + moistScore + climScore));
  scoreNumEl.textContent = `${totalScore}%`;

  if (totalScore >= 75) {
    scoreBadge.className = "suitability-score-badge status-high";
    verdictEl.textContent = "Highly Suitable";
    summaryEl.innerHTML = `Your soil and climate parameters are <strong>well-matched for ${crop.name}</strong>. Minimal adjustments needed.`;
  } else if (totalScore >= 52) {
    scoreBadge.className = "suitability-score-badge status-moderate";
    verdictEl.textContent = "Conditionally Suitable";
    summaryEl.innerHTML = `<strong>${crop.name} can grow conditionally</strong>, but requires nutrient balancing and/or pH amendment for optimal yield.`;
  } else {
    scoreBadge.className = "suitability-score-badge status-low";
    verdictEl.textContent = "Sub-optimal / High Risk";
    summaryEl.innerHTML = `Current soil state has significant deviations from <strong>${crop.name}</strong> requirements. Major amendments necessary.`;
  }

  // Factor breakdown
  const npkEl = document.getElementById("suit-npk-details");
  if (npkEl) {
    npkEl.innerHTML = `
      N: <strong>${n}</strong> (Target ${crop.optimal_n}, ${nDiff >= 0 ? '+' + nDiff : nDiff})<br>
      P: <strong>${p}</strong> (Target ${crop.optimal_p}, ${pDiff >= 0 ? '+' + pDiff : pDiff})<br>
      K: <strong>${k}</strong> (Target ${crop.optimal_k}, ${kDiff >= 0 ? '+' + kDiff : kDiff})
    `;
  }

  const phEl = document.getElementById("suit-ph-details");
  if (phEl) {
    phEl.innerHTML = `
      <span class="chip-status-${phStatus}">● pH ${ph.toFixed(2)}</span><br>
      Tolerance: <strong>${crop.min_ph} - ${crop.max_ph}</strong><br>
      ${phMsg}
    `;
  }

  const moistEl = document.getElementById("suit-moisture-details");
  if (moistEl) {
    moistEl.innerHTML = `
      <span class="chip-status-${moistStatus}">● Moisture: ${moisture}%</span><br>
      Ideal: <strong>${crop.min_moisture}% - ${crop.max_moisture}%</strong><br>
      Rainfall: <strong>${rain} mm</strong> (Opt: ${crop.optimal_rainfall} mm)
    `;
  }

  const climEl = document.getElementById("suit-climate-details");
  if (climEl) {
    climEl.innerHTML = `
      Temp: <strong>${temp}°C</strong> (Ideal: ${crop.min_temp}-${crop.max_temp}°C)<br>
      Humidity: <strong>${humidity}%</strong> (Ideal: ${crop.min_humidity}-${crop.max_humidity}%)
    `;
  }

  // Action advice
  if (adviceText) {
    const advice = ph < crop.min_ph ? crop.advice_acidic : (ph > crop.max_ph ? crop.advice_alkaline : "Soil pH is favorable. Focus on basal fertilizer placement.");
    adviceText.innerHTML = `<strong>Agronomic Protocol for ${crop.name}:</strong> ${advice}`;
  }
}

function initCropSuitabilityFeature() {
  const cropSelect = document.getElementById("sensor-target-crop-select");
  const quickChips = document.querySelectorAll(".crop-chip-btn");
  const btnLoadPreset = document.getElementById("btn-load-crop-ideal-preset");

  const setTargetCrop = (cropKey) => {
    selectedTargetCrop = cropKey || null;
    if (cropSelect && cropSelect.value !== cropKey) {
      cropSelect.value = cropKey || "";
    }
    quickChips.forEach((btn) => {
      if (btn.getAttribute("data-crop") === cropKey) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
    evaluateTargetCropSuitability();
    if (typeof renderTargetCropGapAnalysis === "function" && lastRecData) {
      renderTargetCropGapAnalysis(lastRecData);
    }
  };

  cropSelect?.addEventListener("change", (e) => {
    setTargetCrop(e.target.value);
  });

  quickChips.forEach((btn) => {
    btn.addEventListener("click", () => {
      const cropKey = btn.getAttribute("data-crop");
      setTargetCrop(cropKey);
    });
  });

  btnLoadPreset?.addEventListener("click", () => {
    if (!selectedTargetCrop || !CROP_BENCHMARKS[selectedTargetCrop]) {
      alert("Please select a target crop first using the dropdown or quick chips above.");
      return;
    }
    const crop = CROP_BENCHMARKS[selectedTargetCrop];
    const cropPreset = {
      n: crop.optimal_n,
      p: crop.optimal_p,
      k: crop.optimal_k,
      ph: crop.opt_ph,
      moisture: crop.opt_moisture,
      temp: crop.opt_temp,
      humidity: crop.opt_humidity,
      rainfall: crop.optimal_rainfall,
    };
    applyPreset(cropPreset);
    showToast(`🎯 Loaded ideal soil preset for ${crop.name}!`, "success");
  });
}

// -------------------------------------------------------------
// SECTION 6: Kisan AI Multilingual RAG Copilot Client Logic
// -------------------------------------------------------------

function escapeHtml(unsafe) {
  return (unsafe || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatMarkdown(text) {
  try {
    if (!text) return "";
    let formatted = escapeHtml(text);
    // Bold **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Inline code `code`
    formatted = formatted.replace(/`([^`]+)`/g, "<code>$1</code>");
    // Bullet lists (- or * at start of line)
    formatted = formatted.replace(/^\s*[-*]\s+(.*)$/gm, "<li>$1</li>");
    formatted = formatted.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");
    formatted = formatted.replace(/<\/ul>\s*<ul>/g, "");

    // Transform citations like [Research Resource: s41598-025-26910-4.pdf | Page 4]
    // into styled badge cards with lowercase document names and highlighted amber page pills
    formatted = formatted.replace(
      /\[(Research Resource|Agronomic Table|Knowledge Base|Research Document)\s*:\s*([^\|\]]+)(?:\s*\|\s*([^\]]+))?\]/gi,
      (match, type, docName, pagePart) => {
        const cleanType = (type || "").trim().toLowerCase();
        const cleanDoc = (docName || "").trim().toLowerCase();
        let pageBadge = "";
        if (pagePart) {
          pageBadge = `<span class="citation-page">${escapeHtml(pagePart.trim().toLowerCase())}</span>`;
        }
        return `<span class="resource-citation-card"><span class="citation-type">📑 ${escapeHtml(cleanType)}:</span> <span class="citation-doc">${escapeHtml(cleanDoc)}</span>${pageBadge}</span>`;
      }
    );

    // Line breaks into paragraphs
    const paragraphs = formatted.split(/\n\n+/);
    return paragraphs
      .map((p) => {
        const trimmed = p.trim();
        if (trimmed.startsWith("<ul>") && trimmed.endsWith("</ul>")) {
          return trimmed;
        }
        return `<p>${trimmed.replace(/\n/g, "<br>")}</p>`;
      })
      .join("");
  } catch (err) {
    console.warn("Markdown formatting fallback:", err);
    return `<p>${escapeHtml(text).replace(/\n/g, "<br>")}</p>`;
  }
}

function appendChatMessage(opts) {
  try {
    const { role, text, language, source, gdriveFolder, gdriveResourcesFolder, timeStr } = opts || {};
    const container = document.getElementById("chat-messages");
    if (!container) return;

    const msgDiv = document.createElement("div");
    const isFarmer = role === "user" || role === "farmer";
    msgDiv.className = `chat-msg ${isFarmer ? "farmer-msg" : "ai-msg"}`;

    const timeDisplay = timeStr || new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

    if (isFarmer) {
      msgDiv.innerHTML = `
        <div class="msg-avatar">👨‍🌾</div>
        <div class="msg-bubble">
          <div class="msg-header-meta">
            <span class="msg-sender">Farmer</span>
            <span class="msg-source-tag user">Active Field</span>
          </div>
          <div class="msg-content">
            <p>${escapeHtml(text)}</p>
          </div>
          <div class="msg-footer-row">
            <span class="msg-time">${timeDisplay}</span>
          </div>
        </div>
      `;
    } else {
      let sourceLabel = "ICAR & FAO-56 Grounded";
      let sourceClass = "gemini";
      if (source === "gemini") {
        sourceLabel = "Gemini 1.5 Flash (Audited)";
        sourceClass = "gemini";
      } else if (source === "ollama") {
        sourceLabel = "Ollama 3.2:3b (Fallback)";
        sourceClass = "ollama";
      } else {
        sourceLabel = "ICAR & FAO-56 Grounded";
        sourceClass = "gemini";
      }

      const langBadge = language ? `<span class="metric-chip" style="padding: 0.1rem 0.4rem; font-size: 0.65rem;">${language}</span>` : "";
      const driveUrl = gdriveFolder || "https://drive.google.com/drive/folders/1wp9xKSZSxIzTriKEWmQYVlEhXcUfQXSE?usp=drive_link";
      const resourcesUrl = gdriveResourcesFolder || "https://drive.google.com/drive/folders/1LdRwAKBybFYsijbMmOd2EdLRDqISTpI6?usp=drive_link";

      msgDiv.innerHTML = `
        <div class="msg-avatar">🌾</div>
        <div class="msg-bubble">
          <div class="msg-header-meta">
            <div style="display:flex; align-items:center; gap: 0.4rem;">
              <span class="msg-sender">Kisan AI Advisor</span>
              ${langBadge}
            </div>
            <span class="msg-source-tag ${sourceClass}">${sourceLabel}</span>
          </div>
          <div class="msg-content">
            ${formatMarkdown(text)}
          </div>
          <div class="msg-footer-row">
            <div style="display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap;">
              <a href="${driveUrl}" target="_blank" rel="noopener noreferrer" class="msg-sync-pill" title="View chat session in Google Drive Cloud Folder">
                <span>☁️ Synced to Chat Logs</span>
              </a>
              <a href="${resourcesUrl}" target="_blank" rel="noopener noreferrer" class="msg-sync-pill" title="Open Research Papers & Tables Drive Folder">
                <span>📂 View Research Papers</span>
              </a>
            </div>
            <span class="msg-time">${timeDisplay}</span>
          </div>
        </div>
      `;
    }

    container.appendChild(msgDiv);
    container.scrollTop = container.scrollHeight;
  } catch (renderErr) {
    console.error("Critical rendering error in appendChatMessage:", renderErr);
    // Absolute fallback so text is never lost
    try {
      const fallbackContainer = document.getElementById("chat-messages");
      if (fallbackContainer) {
        const fallbackDiv = document.createElement("div");
        fallbackDiv.className = "chat-msg ai-msg";
        fallbackDiv.innerHTML = `<div class="msg-avatar">🌾</div><div class="msg-bubble"><p>${escapeHtml(opts && opts.text)}</p></div>`;
        fallbackContainer.appendChild(fallbackDiv);
      }
    } catch (_) {}
  }
}

function showTypingIndicator() {
  removeTypingIndicator();
  const container = document.getElementById("chat-messages");
  if (!container) return;

  const typingDiv = document.createElement("div");
  typingDiv.className = "chat-msg ai-msg";
  typingDiv.id = "chat-typing-indicator";
  typingDiv.innerHTML = `
    <div class="msg-avatar">🌾</div>
    <div class="msg-bubble" style="padding: 0.6rem 0.9rem;">
      <div class="typing-dots">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>
  `;
  container.appendChild(typingDiv);
  container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
  const indicator = document.getElementById("chat-typing-indicator");
  if (indicator) indicator.remove();
}

async function handleChatSubmit(queryText) {
  const query = (queryText || "").trim();
  if (!query) return;

  // Append user's message immediately
  appendChatMessage({
    role: "user",
    text: query,
  });

  const sendBtn = document.getElementById("chat-send-btn");
  const inputField = document.getElementById("chat-input");
  if (inputField) inputField.value = "";
  if (sendBtn) sendBtn.disabled = true;

  showTypingIndicator();

  try {
    // If no telemetry ID exists yet, create one from current slider values
    let telemetryId = currentTelemetryId;
    if (!telemetryId && typeof executeTelemetryPipeline === "function") {
      try {
        await executeTelemetryPipeline();
        telemetryId = currentTelemetryId;
      } catch (e) {
        console.warn("Could not pre-run telemetry pipeline:", e);
      }
    }

    const response = await fetch("/api/kisan-ai/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: query,
        telemetry_id: telemetryId || 1,
      }),
    });

    removeTypingIndicator();

    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `Server error: ${response.status}`);
    }

    const data = await response.json();
    appendChatMessage({
      role: "ai",
      text: data.answer,
      language: data.language,
      source: data.source,
      gdriveFolder: data.gdrive_folder,
      gdriveResourcesFolder: data.gdrive_resources_folder,
    });
  } catch (err) {
    console.error("Kisan AI Chat Error:", err);
    removeTypingIndicator();
    appendChatMessage({
      role: "ai",
      text: `⚠️ Error contacting Kisan AI: ${err.message}. Please verify the backend is active.`,
      source: "offline-kb",
      gdriveFolder: "https://drive.google.com/drive/folders/1wp9xKSZSxIzTriKEWmQYVlEhXcUfQXSE?usp=drive_link",
      gdriveResourcesFolder: "https://drive.google.com/drive/folders/1LdRwAKBybFYsijbMmOd2EdLRDqISTpI6?usp=drive_link",
    });
  } finally {
    if (sendBtn) sendBtn.disabled = false;
    if (inputField) inputField.focus();
  }
}

async function loadChatHistory() {
  try {
    const res = await fetch("/api/kisan-ai/history");
    if (!res.ok) return;
    const data = await res.json();
    if (data.history && Array.isArray(data.history) && data.history.length > 0) {
      const messagesContainer = document.getElementById("chat-messages");
      // Only render previous sessions if container has only the welcome message
      if (messagesContainer && messagesContainer.children.length <= 1) {
        data.history.slice(-4).forEach((entry) => {
          appendChatMessage({
            role: "user",
            text: entry.query,
            timeStr: entry.timestamp ? entry.timestamp.split(" ")[1] : undefined,
          });
          appendChatMessage({
            role: "ai",
            text: entry.answer,
            language: entry.language,
            source: entry.source,
            gdriveFolder: entry.gdrive_folder,
            gdriveResourcesFolder: data.gdrive_resources_folder,
            timeStr: entry.timestamp ? entry.timestamp.split(" ")[1] : undefined,
          });
        });
      }
    }
  } catch (e) {
    console.warn("Could not load initial chat history:", e);
  }
}

async function loadResourcesSummary() {
  try {
    const res = await fetch("/api/kisan-ai/resources");
    if (!res.ok) return;
    const data = await res.json();
    const badge = document.getElementById("resources-count-badge");
    if (badge && data.total_files) {
      badge.textContent = `📚 ${data.total_files} Research Documents & Tables Indexed (${data.total_chunks} Chunks)`;
    }
    const engineBadge = document.getElementById("kisan-engine-status");
    if (engineBadge && data.engine_mode) {
      engineBadge.textContent = data.engine_mode;
    }
  } catch (e) {
    console.warn("Could not load resources summary:", e);
  }
}

// -------------------------------------------------------------
// Farmer Authentication & Session Management
// -------------------------------------------------------------
let currentUser = null;
let authToken = null;

function getStoredUser() {
  try {
    const raw = localStorage.getItem("krishimitra_user") || sessionStorage.getItem("krishimitra_user");
    return raw ? JSON.parse(raw) : null;
  } catch (e) {
    return null;
  }
}

function getStoredToken() {
  return localStorage.getItem("krishimitra_token") || sessionStorage.getItem("krishimitra_token");
}

function setStoredUser(user, token, rememberMe = true) {
  currentUser = user;
  authToken = token;
  const storage = rememberMe ? localStorage : sessionStorage;
  storage.setItem("krishimitra_user", JSON.stringify(user));
  if (token) storage.setItem("krishimitra_token", token);
  if (rememberMe) {
    sessionStorage.removeItem("krishimitra_user");
    sessionStorage.removeItem("krishimitra_token");
  } else {
    localStorage.removeItem("krishimitra_user");
    localStorage.removeItem("krishimitra_token");
  }
}

function clearStoredUser() {
  currentUser = null;
  authToken = null;
  localStorage.removeItem("krishimitra_user");
  localStorage.removeItem("krishimitra_token");
  sessionStorage.removeItem("krishimitra_user");
  sessionStorage.removeItem("krishimitra_token");
}

function showToast(message, type = "success", duration = 3500) {
  const container = document.getElementById("toast-container");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  const icon = type === "success" ? "✅" : type === "error" ? "⚠️" : "ℹ️";
  toast.innerHTML = `<span style="font-size:1.15rem;line-height:1;">${icon}</span> <div style="display:flex;align-items:center;gap:0.6rem;flex:1;">${message}</div>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateY(20px)";
    setTimeout(() => toast.remove(), 350);
  }, duration);
}

function updateUserHeaderUI() {
  const container = document.getElementById("user-header-widget");
  if (!container) return;

  if (currentUser) {
    container.innerHTML = `
      <div class="farmer-header-pill" id="farmer-profile-pill" title="Active Farmer: ${currentUser.name} (${currentUser.role || 'Farmer'})">
        <div class="farmer-avatar-sm">👨‍🌾</div>
        <div class="farmer-meta-sm">
          <span class="farmer-name-sm">${currentUser.name}</span>
          <span class="farmer-sector-sm">${currentUser.kisan_id || 'IND-KISAN'} • ${currentUser.farm_sector || 'Field Cluster'}</span>
        </div>
        <button type="button" class="btn-header-logout" id="btn-header-logout" title="Sign out">Logout</button>
      </div>
    `;

    document.getElementById("btn-header-logout")?.addEventListener("click", (e) => {
      e.stopPropagation();
      clearStoredUser();
      updateUserHeaderUI();
      showToast("Signed out successfully.", "info");
      openLoginModal();
    });

    document.getElementById("farmer-profile-pill")?.addEventListener("click", (e) => {
      if (e.target.id === "btn-header-logout") return;
      openLoginModal();
    });
  } else {
    container.innerHTML = `
      <button type="button" class="btn-header-login" id="btn-header-login" title="Sign in with your name & password">
        <span>🔑 Farmer Login</span>
      </button>
    `;

    document.getElementById("btn-header-login")?.addEventListener("click", () => {
      openLoginModal();
    });
  }
}

function openLoginModal() {
  const overlay = document.getElementById("auth-modal-overlay");
  if (overlay) {
    overlay.classList.remove("hidden");
    const errBanner = document.getElementById("auth-error-banner");
    if (errBanner) {
      errBanner.classList.add("hidden");
      errBanner.textContent = "";
    }
    setTimeout(() => {
      document.getElementById("login-name-input")?.focus();
    }, 100);
  }
}

function closeLoginModal() {
  const overlay = document.getElementById("auth-modal-overlay");
  if (overlay) {
    overlay.classList.add("hidden");
  }
}

function showAuthError(msg) {
  const errBanner = document.getElementById("auth-error-banner");
  if (errBanner) {
    errBanner.textContent = msg;
    errBanner.classList.remove("hidden");
  }
}

async function performLogin(nameOrUser, password, rememberMe = true) {
  showAuthError("");
  const errBanner = document.getElementById("auth-error-banner");
  if (errBanner) errBanner.classList.add("hidden");

  const submitBtn = document.getElementById("btn-login-submit");
  const originalBtnHtml = submitBtn ? submitBtn.innerHTML : "Sign In";
  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.innerHTML = "<span>Authenticating...</span>";
  }

  try {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: nameOrUser,
        username_or_email: nameOrUser,
        password: password,
      }),
    });

    const data = await res.json();

    if (!res.ok) {
      const errMsg = data.detail || "Invalid login credentials. Please check name and password.";
      showAuthError(errMsg);
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = originalBtnHtml;
      }
      return false;
    }

    setStoredUser(data.user, data.token, rememberMe);
    updateUserHeaderUI();
    closeLoginModal();
    showToast(`🌾 Welcome, ${data.user.name}! (${data.user.role || 'Verified Farmer'})`, "success");

    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnHtml;
    }
    return true;
  } catch (err) {
    showAuthError(`Network connection error: ${err.message}`);
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.innerHTML = originalBtnHtml;
    }
    return false;
  }
}

function initAuthHandlers() {
  currentUser = getStoredUser();
  authToken = getStoredToken();
  updateUserHeaderUI();

  // 1-Click Demo Login Button
  document.getElementById("btn-quick-demo-login")?.addEventListener("click", async () => {
    const nameField = document.getElementById("login-name-input");
    const pwdField = document.getElementById("login-password-input");
    if (nameField) nameField.value = "Ramesh Patel";
    if (pwdField) pwdField.value = "kisan2025";
    await performLogin("kisan_demo", "kisan2025", true);
  });

  // "Use Demo Creds" quick link
  document.getElementById("link-fill-demo")?.addEventListener("click", (e) => {
    e.preventDefault();
    const nameField = document.getElementById("login-name-input");
    const pwdField = document.getElementById("login-password-input");
    if (nameField) nameField.value = "Ramesh Patel";
    if (pwdField) {
      pwdField.value = "kisan2025";
      pwdField.focus();
    }
  });

  // Password visibility toggle
  const togglePwdBtn = document.getElementById("btn-toggle-pwd");
  const pwdInput = document.getElementById("login-password-input");
  if (togglePwdBtn && pwdInput) {
    togglePwdBtn.addEventListener("click", () => {
      const isPwd = pwdInput.type === "password";
      pwdInput.type = isPwd ? "text" : "password";
      togglePwdBtn.textContent = isPwd ? "🙈" : "👁️";
    });
  }

  // Login form submit
  document.getElementById("farmer-login-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nameVal = document.getElementById("login-name-input").value.trim();
    const pwdVal = document.getElementById("login-password-input").value.trim();
    const rememberVal = document.getElementById("login-remember-me")?.checked ?? true;

    if (!nameVal || !pwdVal) {
      showAuthError("Please enter both your name and password.");
      return;
    }

    await performLogin(nameVal, pwdVal, rememberVal);
  });

  // Close modal button
  document.getElementById("btn-auth-close")?.addEventListener("click", () => {
    closeLoginModal();
    sessionStorage.setItem("krishimitra_guest_dismissed", "true");
  });

  // Guest continue button
  document.getElementById("btn-guest-continue")?.addEventListener("click", () => {
    closeLoginModal();
    sessionStorage.setItem("krishimitra_guest_dismissed", "true");
    showToast("Continuing as Guest. Click 'Farmer Login' in the header anytime to sign in.", "info");
  });

  // Click outside modal card to close
  document.getElementById("auth-modal-overlay")?.addEventListener("click", (e) => {
    if (e.target.id === "auth-modal-overlay") {
      closeLoginModal();
      sessionStorage.setItem("krishimitra_guest_dismissed", "true");
    }
  });

  // ESC key to close modal
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const overlay = document.getElementById("auth-modal-overlay");
      if (overlay && !overlay.classList.contains("hidden")) {
        closeLoginModal();
        sessionStorage.setItem("krishimitra_guest_dismissed", "true");
      }
    }
  });

  // Check initial authentication state
  if (currentUser) {
    closeLoginModal();
  } else {
    openLoginModal();
  }
}

// -------------------------------------------------------------
// Wireframe Landing Architecture: Tab Switcher & "Test Now"
// -------------------------------------------------------------
function formatCurrentTestTime() {
  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  const dateStr = now.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" });
  return `${dateStr} at ${timeStr} • Palakkad IoT Field Station #04`;
}

function updateRawTelemetryOutput() {
  const outputEl = document.getElementById("raw-telemetry-output");
  if (!outputEl) return;

  const n = parseFloat(document.getElementById("slider-n")?.value || document.getElementById("num-n")?.value || 35);
  const p = parseFloat(document.getElementById("slider-p")?.value || document.getElementById("num-p")?.value || 60);
  const k = parseFloat(document.getElementById("slider-k")?.value || document.getElementById("num-k")?.value || 32);
  const ph = parseFloat(document.getElementById("slider-ph")?.value || document.getElementById("num-ph")?.value || 5.4);
  const moisture = parseFloat(document.getElementById("slider-moisture")?.value || document.getElementById("num-moisture")?.value || 28);
  const temp = parseFloat(document.getElementById("slider-temp")?.value || document.getElementById("num-temp")?.value || 31);
  const humidity = parseFloat(document.getElementById("slider-humidity")?.value || document.getElementById("num-humidity")?.value || 80);
  const rain = parseFloat(document.getElementById("slider-rainfall")?.value || document.getElementById("num-rainfall")?.value || currentRainfall || 180);

  const packet = {
    timestamp: new Date().toISOString(),
    node_id: "ESP32-S3-KRISHI-01",
    firmware_build: "v2.4.1-SIM-CALIB",
    acquisition_mode: "MANUAL_PROBE_INJECTION",
    field_sector: "Palakkad Sector #04",
    farmer_id: currentUser ? currentUser.kisan_id : "IND-KISAN-9024",
    farmer_name: currentUser ? currentUser.name : "Ramesh Patel",
    hardware: {
      battery_pct: 96,
      battery_voltage: "3.92V (Li-Po)",
      solar_charging: true,
      uplink_protocol: "LoRa 868MHz SF7 BW125 / MQTT",
      rssi_dbm: -68,
      snr_db: 9.4,
      adc_bus: "ADS1115 16-Bit I2C (Addr: 0x48)",
      last_sync_status: "SUCCESS"
    },
    sensor_channels: {
      npk_optical_spectrometry: {
        n_kg_ha: n,
        p_kg_ha: p,
        k_kg_ha: k,
        ads1115_volts: {
          ch0_n: (n * 0.025 + 0.1).toFixed(3) + "V",
          ch1_p: (p * 0.02 + 0.2).toFixed(3) + "V",
          ch2_k: (k * 0.015 + 0.15).toFixed(3) + "V"
        },
        calibrated: true
      },
      glass_ph_isfet: {
        ph_value: ph,
        sensitivity_mv_ph: 59.16,
        temp_compensated: true,
        calibrated: true
      },
      tdr_moisture_modbus: {
        volumetric_water_content_pct: moisture,
        dielectric_constant: (moisture * 0.45 + 3.2).toFixed(2),
        calibrated: true
      },
      sht31_ambient: {
        temperature_c: temp,
        relative_humidity_pct: humidity,
        dew_point_c: (temp - (100 - humidity) / 5).toFixed(1),
        calibrated: true
      },
      agromet_precipitation: {
        forecast_14d_rainfall_mm: rain,
        gauge_type: "Tipping Bucket 0.2mm"
      }
    },
    soil_health_index: document.getElementById("health-index-val")?.textContent || "84",
    health_rating: document.getElementById("health-rating-val")?.textContent || "Adequate"
  };

  outputEl.textContent = JSON.stringify(packet, null, 2);
}

function initTabSwitcher() {
  const tabUI = document.getElementById("tab-btn-ui");
  const tabSensor = document.getElementById("tab-btn-sensor");
  const paneUI = document.getElementById("view-user-interface");
  const paneSensor = document.getElementById("view-sensor-screen");

  if (!tabUI || !tabSensor || !paneUI || !paneSensor) return;

  tabUI.addEventListener("click", () => {
    tabUI.classList.add("active");
    tabSensor.classList.remove("active");
    paneUI.classList.remove("hidden");
    paneSensor.classList.add("hidden");
  });

  tabSensor.addEventListener("click", () => {
    tabSensor.classList.add("active");
    tabUI.classList.remove("active");
    paneSensor.classList.remove("hidden");
    paneUI.classList.add("hidden");
    updateRawTelemetryOutput();
  });
}

function initTestNowButtons() {
  const btnUI = document.getElementById("btn-test-now");
  const btnSensor = document.getElementById("btn-test-now-sensor");
  const timeVal = document.getElementById("last-tested-time-val");

  if (timeVal) {
    timeVal.textContent = formatCurrentTestTime();
  }

  const triggerTestFlow = async (sourceName) => {
    const allBtns = [btnUI, btnSensor].filter(Boolean);
    allBtns.forEach((b) => {
      b.classList.add("scanning");
      b.innerHTML = `<span class="btn-test-icon">⏳</span> <span>Sampling &amp; Transmitting...</span>`;
    });

    const bufferState = document.getElementById("telemetry-buffer-state");
    if (bufferState) bufferState.textContent = "Transmitting IoT Telemetry to KrishiMitra...";

    // Visual feedback: animate gauges
    const gaugeCards = document.querySelectorAll(".gauge-card");
    gaugeCards.forEach((card) => card.classList.add("loading"));

    // Micro delay to simulate hardware acquisition
    await new Promise((resolve) => setTimeout(resolve, 600));

    // Trigger telemetry pipeline
    await executeTelemetryPipeline();

    if (timeVal) {
      timeVal.textContent = formatCurrentTestTime();
    }

    if (bufferState) bufferState.textContent = "Synchronized (ACK Received: 201 Created)";
    updateRawTelemetryOutput();

    gaugeCards.forEach((card) => card.classList.remove("loading"));
    allBtns.forEach((b) => {
      b.classList.remove("scanning");
      b.innerHTML = `<span class="btn-test-icon">⚡</span> <span>Test Now</span>`;
    });

    if (sourceName === "sensor") {
      // Auto-switch to User Interface tab to immediately showcase the Top Rank and Tested Crop Gap analysis
      document.getElementById("tab-btn-ui")?.click();
      setTimeout(() => {
        document.getElementById("section-target-crop-gap")?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 150);

      const targetLabel = selectedTargetCrop 
        ? (CROP_BENCHMARKS[selectedTargetCrop]?.name || selectedTargetCrop)
        : (lastRecData?.top_crop || "Selected Crop");
      const topLabel = lastRecData?.top_crop || "Rice";

      showToast(
        `🎯 Tested Crop: <strong>${targetLabel}</strong> | 🏆 Top Rank AI: <strong>${topLabel}</strong>`,
        "success",
        5000
      );
    } else {
      showToast("🌱 Soil Sensor Scan Complete! Recommendations & Health Score updated.", "success");
    }
  };

  btnUI?.addEventListener("click", () => triggerTestFlow("ui"));
  btnSensor?.addEventListener("click", () => triggerTestFlow("sensor"));
}

// -------------------------------------------------------------
// Initialization
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  // Initialize Farmer Authentication & Login Modal
  initAuthHandlers();

  // Initialize Wireframe Landing Architecture: Tabs & Dual Test Now Actions
  initTabSwitcher();
  initTestNowButtons();
  initCropSuitabilityFeature();

  // Bind all 8 dual-control sensor inputs (numeric input + fine slider)
  bindDualControl("slider-n", "num-n", "lbl-n", "kg/ha");
  bindDualControl("slider-p", "num-p", "lbl-p", "kg/ha");
  bindDualControl("slider-k", "num-k", "lbl-k", "kg/ha");
  bindDualControl("slider-ph", "num-ph", "lbl-ph", "", updatePhChip);
  bindDualControl("slider-moisture", "num-moisture", "lbl-moisture", "%");
  bindDualControl("slider-temp", "num-temp", "lbl-temp", "°C");
  bindDualControl("slider-humidity", "num-humidity", "lbl-humidity", "%");
  bindDualControl("slider-rainfall", "num-rainfall", "lbl-rainfall", "mm");

  // Bind Preset Buttons
  document.getElementById("btn-preset-palakkad")?.addEventListener("click", () => {
    applyPreset(PRESETS.palakkad);
  });
  document.getElementById("btn-preset-punjab")?.addEventListener("click", () => {
    applyPreset(PRESETS.punjab);
  });
  document.getElementById("btn-preset-maharashtra")?.addEventListener("click", () => {
    applyPreset(PRESETS.maharashtra);
  });
  document.getElementById("btn-preset-wayanad")?.addEventListener("click", () => {
    applyPreset(PRESETS.wayanad);
  });

  // Bind Quick Prompt buttons in Kisan AI section
  document.querySelectorAll(".quick-prompt-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const query = btn.getAttribute("data-query");
      if (query) {
        handleChatSubmit(query);
      }
    });
  });

  // Bind Chat Form submission
  const chatForm = document.getElementById("chat-form");
  if (chatForm) {
    chatForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const input = document.getElementById("chat-input");
      if (input) handleChatSubmit(input.value);
    });
  }

  // Bind Configure Gemini API Key Button
  const btnConfigGemini = document.getElementById("btn-configure-gemini");
  if (btnConfigGemini) {
    btnConfigGemini.addEventListener("click", async () => {
      const currentKey = prompt(
        "Enter your Google Gemini API Key (from Google AI Studio):",
        ""
      );
      if (currentKey && currentKey.trim()) {
        try {
          const res = await fetch("/api/kisan-ai/set-key", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_key: currentKey.trim() }),
          });
          const resData = await res.json();
          if (res.ok) {
            alert("✅ Google Gemini API key configured successfully! Live multimodal reasoning is now active.");
            loadResourcesSummary();
          } else {
            alert(`⚠️ Error setting API key: ${resData.detail || "Server error"}`);
          }
        } catch (err) {
          alert(`⚠️ Connection error: ${err.message}`);
        }
      }
    });
  }

  // Load chat history & dynamic research resources count
  loadChatHistory();
  loadResourcesSummary();

  // Initial trigger with Palakkad Rice Paddy defaults
  applyPreset(PRESETS.palakkad);
});
