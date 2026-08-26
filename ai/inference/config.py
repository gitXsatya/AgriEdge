"""
AgriEdge - Centralized configuration (Person 1 - Edge AI).

Every other file reads class names, paths, and thresholds from here.
Nothing disease-specific lives in predict.py or app.py: adding a future
disease means adding data here (and retraining) -- never a new
`if prediction == "..."` branch anywhere in the codebase.
"""

import json
from pathlib import Path

# --- Paths ----------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = PROJECT_ROOT / "ai" / "models"

# "Current" model: whatever is deployed right now. When you train a new
# version, back the old file up with a version suffix (e.g.
# tomato_disease_model_v1.tflite) and save the new export over this
# filename, so the app never needs a source change to pick it up.
MODEL_PATH = MODEL_DIR / "tomato_disease_model.tflite"
METADATA_PATH = MODEL_DIR / "model_metadata.json"

# --- Defaults (used until model_metadata.json exists, i.e. before you've
# trained anything -- and kept in sync afterwards, see bottom of file) ----
CROP_NAME = "Tomato"
MODEL_VERSION = "v1"
IMAGE_SIZE = (224, 224)  # (height, width) - MUST match training
CLASS_NAMES = ["Healthy", "Early Blight", "Late Blight"]
HEALTHY_LABEL = "Healthy"

# --- Confidence -------------------------------------------------------------
CONFIDENCE_THRESHOLD = 0.80  # below this we report "Uncertain" rather than guess

# --- Status codes (shared by predict.py, app.py, and Person 2/3) -----------
STATUS_HEALTHY = "HEALTHY"
STATUS_DISEASE_DETECTED = "DISEASE_DETECTED"
STATUS_UNCERTAIN = "UNCERTAIN"
STATUS_ERROR = "ERROR"

# --- Farmer-facing recommendations, keyed by class name ---------------------
# Adding a disease later = add a key here + retrain. No code changes.
RECOMMENDATIONS = {
    "Healthy": "No signs of disease detected. Continue regular monitoring.",
    "Early Blight": (
        "Possible early blight. Remove and dispose of affected lower leaves, "
        "avoid overhead watering, and improve airflow around the plant."
    ),
    "Late Blight": (
        "Possible late blight. This spreads quickly in humid conditions -- "
        "remove affected leaves promptly and consult a local agricultural "
        "extension officer."
    ),
    "Uncertain": (
        "The model isn't confident enough to classify this image. Try a "
        "clearer, well-lit photo of a single leaf against a plain background."
    ),
}
DEFAULT_RECOMMENDATION = "No recommendation configured for this class yet."

# --- Load real metadata from the trained model, if it exists ----------------
# Keeps class order/version in sync with whatever was actually trained,
# without hand-editing this file every time the model changes.
if METADATA_PATH.exists():
    try:
        with open(METADATA_PATH, "r") as f:
            _metadata = json.load(f)
        CLASS_NAMES = _metadata.get("class_names", CLASS_NAMES)
        MODEL_VERSION = _metadata.get("model_version", MODEL_VERSION)
        _size = _metadata.get("input_size")
        if _size:
            IMAGE_SIZE = tuple(_size)
    except (json.JSONDecodeError, OSError):
        pass  # fall back to defaults above; predict.py will surface load errors
