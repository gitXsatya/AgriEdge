"""
AgriEdge - Local Flask server

Phone -> Flask -> AI -> Decision Engine -> Dashboard
"""

import sys
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

from decision_engine import generate_recommendation


# ============================================================
# PROJECT PATHS
# ============================================================

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent

UPLOAD_DIR = APP_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# AI IMPORTS
# ============================================================

sys.path.insert(0, str(PROJECT_ROOT / "ai" / "inference"))

import config
from predict import predict_image, ModelNotFoundError, InferenceError


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# ============================================================
# ALLOWED IMAGE TYPES
# ============================================================

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


# ============================================================
# LATEST RESULT
# ============================================================

latest_result = {
    "has_result": False
}


def set_latest_result(**fields):

    latest_result.clear()

    latest_result.update(
        has_result=True,
        timestamp=time.time(),
        **fields
    )


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def index():

    return render_template(
        "index.html",
        crop=config.CROP_NAME
    )


# ============================================================
# IMAGE UPLOAD
# ============================================================

@app.route("/upload", methods=["POST"])
def upload():

    # --------------------------------------------------------
    # GET IMAGE
    # --------------------------------------------------------

    file = request.files.get("image")

    if file is None or file.filename == "":

        return render_template(
            "index.html",
            crop=config.CROP_NAME,
            error="No image selected."
        ), 400


    # --------------------------------------------------------
    # CHECK FILE TYPE
    # --------------------------------------------------------

    ext = Path(file.filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:

        return render_template(
            "index.html",
            crop=config.CROP_NAME,
            error=f"Unsupported file type '{ext}'."
        ), 400


    # --------------------------------------------------------
    # SAVE IMAGE
    # --------------------------------------------------------

    filename = f"{uuid.uuid4().hex}{ext}"

    save_path = UPLOAD_DIR / filename

    file.save(save_path)

    image_url = url_for(
        "static",
        filename=f"uploads/{filename}"
    )


    # ========================================================
    # PERSON 1 - AI PREDICTION
    # ========================================================

    try:

        result = predict_image(str(save_path))

    except (ModelNotFoundError, InferenceError) as exc:

        set_latest_result(
            image_url=image_url,
            crop=config.CROP_NAME,
            prediction=None,
            confidence=None,
            status=config.STATUS_ERROR,
            recommendation=None,
            error=str(exc)
        )

        return redirect(url_for("index"))


    # ========================================================
    # PERSON 2 - DEMO SENSOR VALUES
    # ========================================================
    #
    # Person 2 has not connected the real sensors yet.
    #
    # These are temporary values for our prototype.
    #
    # Later:
    #
    # temperature    -> real sensor
    # soil_moisture  -> real sensor
    # humidity       -> real sensor
    #
    # ========================================================

    temperature = 34

    soil_moisture = 27

    humidity = 48


    # ========================================================
    # PERSON 3 - DECISION ENGINE
    # ========================================================

    recommendation = generate_recommendation(

        temperature=temperature,

        soil_moisture=soil_moisture,

        humidity=humidity,

        disease_status=result.get("status"),

        disease_confidence=result.get("confidence"),

        disease_prediction=result.get("prediction")
    )


     # ========================================================
    # SEND EVERYTHING TO DASHBOARD
    # ========================================================

    result_without_recommendation = {
        key: value
        for key, value in result.items()
        if key != "recommendation"
    }

    set_latest_result(
        image_url=image_url,
        temperature=temperature,
        soil_moisture=soil_moisture,
        humidity=humidity,
        recommendation=recommendation,
        **result_without_recommendation
    )

    return redirect(url_for("index"))
# ============================================================
# API - LATEST RESULT
# ============================================================

@app.route("/api/latest")
def api_latest():

    return jsonify(latest_result)


# ============================================================
# FILE TOO LARGE
# ============================================================

@app.errorhandler(413)
def too_large(_exc):

    return jsonify({

        "status": config.STATUS_ERROR,

        "error": "Image too large (max 10MB)."

    }), 413


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )