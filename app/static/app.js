const POLL_INTERVAL_MS = 4000;

const el = {
  empty: document.getElementById("result-empty"),
  content: document.getElementById("result-content"),
  image: document.getElementById("result-image"),
  badge: document.getElementById("status-badge"),
  meterFill: document.getElementById("meter-fill"),
  crop: document.getElementById("result-crop"),
  prediction: document.getElementById("result-prediction"),
  confidence: document.getElementById("result-confidence"),
  recommendation: document.getElementById("result-recommendation"),
};

const STATUS_STYLES = {
  HEALTHY: { label: "Healthy", cls: "healthy" },
  DISEASE_DETECTED: { label: "Disease Detected", cls: "disease" },
  UNCERTAIN: { label: "Uncertain", cls: "uncertain" },
  ERROR: { label: "Error", cls: "error" },
};

function render(data) {
  if (!data.has_result) {
    el.empty.classList.remove("hidden");
    el.content.classList.add("hidden");
    return;
  }

  el.empty.classList.add("hidden");
  el.content.classList.remove("hidden");

  el.image.src = data.image_url || "";

  const style = STATUS_STYLES[data.status] || STATUS_STYLES.ERROR;
  el.badge.textContent = style.label;
  el.badge.className = `badge badge-${style.cls}`;
  el.meterFill.className = `meter-fill fill-${style.cls}`;

  const confidencePct = data.confidence != null ? data.confidence * 100 : 0;
  el.meterFill.style.width = `${confidencePct}%`;

  el.crop.textContent = data.crop || "--";

  if (data.status === "ERROR") {
    el.prediction.textContent = "--";
    el.confidence.textContent = "--";
    el.recommendation.textContent = data.error || "Something went wrong.";
  } else {
    el.prediction.textContent = data.prediction || "--";
    el.confidence.textContent = data.confidence != null ? `${confidencePct.toFixed(1)}%` : "--";
    el.recommendation.textContent = data.recommendation || "--";
  }
}

async function refresh() {
  try {
    const res = await fetch("/api/latest");
    if (res.ok) render(await res.json());
  } catch (err) {
    console.error("Could not refresh latest result:", err);
  }
}

refresh();
setInterval(refresh, POLL_INTERVAL_MS);
