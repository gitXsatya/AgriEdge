"""
AgriEdge - Local Flask server (phone -> laptop bridge).

Run:
    python app/app.py
Then open http://<laptop-ip>:5000 from a phone on the same Wi-Fi network.

Design note: the phone uploads via a normal form POST to /upload, which
redirects back to "/". Both the phone (right after its own upload) and
the laptop (which may have "/" open already, watching) pick up the
result the same way: a small JS poll against /api/latest every few
seconds. That's what makes "laptop displays the captured image" work
without needing websockets -- deliberately simple for a hackathon demo.
"""
import sys
import time
import uuid
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, url_for

APP_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = APP_DIR.parent
UPLOAD_DIR = APP_DIR / "static" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(PROJECT_ROOT / "ai" / "inference"))
import config  # noqa: E402
from predict import predict_image, ModelNotFoundError, InferenceError  # noqa: E402

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# In-memory "latest result" -- intentionally simple for a hackathon demo:
# one active capture at a time, no database. Good enough for a live demo;
# not meant to survive a server restart or handle concurrent demos.
latest_result = {"has_result": False}


def set_latest_result(**fields):
    latest_result.clear()
    latest_result.update(has_result=True, timestamp=time.time(), **fields)


@app.route("/")
def index():
    return render_template("index.html", crop=config.CROP_NAME)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("image")
    if file is None or file.filename == "":
        return render_template("index.html", crop=config.CROP_NAME, error="No image selected."), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return render_template(
            "index.html", crop=config.CROP_NAME, error=f"Unsupported file type '{ext}'."
        ), 400

    filename = f"{uuid.uuid4().hex}{ext}"
    save_path = UPLOAD_DIR / filename
    file.save(save_path)
    image_url = url_for("static", filename=f"uploads/{filename}")

    try:
        result = predict_image(str(save_path))
    except (ModelNotFoundError, InferenceError) as exc:
        set_latest_result(
            image_url=image_url, crop=config.CROP_NAME, prediction=None,
            confidence=None, status=config.STATUS_ERROR, recommendation=None,
            error=str(exc),
        )
        return redirect(url_for("index"))

    set_latest_result(image_url=image_url, **result)
    return redirect(url_for("index"))


@app.route("/api/latest")
def api_latest():
    """Clean JSON for the dashboard poller AND for Person 3's integration."""
    return jsonify(latest_result)


@app.errorhandler(413)
def too_large(_exc):
    return jsonify({"status": config.STATUS_ERROR, "error": "Image too large (max 10MB)."}), 413


if __name__ == "__main__":
    # debug=True is convenient for a hackathon demo (auto-reload, clear
    # error pages). Turn it off if this is ever exposed beyond a trusted
    # local Wi-Fi network.
    app.run(host="0.0.0.0", port=5000, debug=True)
