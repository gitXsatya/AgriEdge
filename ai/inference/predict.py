"""
AgriEdge - Local TFLite inference (Person 1 - Edge AI).

CLI usage:
    python ai/inference/predict.py path/to/leaf.jpg

Also used by app/app.py by importing `predict_image` directly.

Everything returned here comes straight out of the loaded TFLite model's
output tensor -- there are no hardcoded predictions or confidence values
anywhere in this file.
"""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np

import config
from preprocess import prepare_image, ImageValidationError


class ModelNotFoundError(RuntimeError):
    """Model file missing, or no TFLite runtime is installed."""


class InferenceError(RuntimeError):
    """Model loaded fine but inference itself failed."""


_interpreter = None  # lazily loaded so the Flask app can start before training is done


def _load_interpreter_class():
    """Prefer the lightweight tflite-runtime; fall back to full TensorFlow."""
    try:
        import tflite_runtime.interpreter as tflite
        return tflite.Interpreter
    except ImportError:
        pass
    try:
        import tensorflow as tf
        return tf.lite.Interpreter
    except ImportError as exc:
        raise ModelNotFoundError(
            "Neither tflite-runtime nor tensorflow is installed. "
            "Run: pip install -r requirements.txt"
        ) from exc


def _get_interpreter():
    global _interpreter
    if _interpreter is not None:
        return _interpreter

    if not config.MODEL_PATH.exists():
        raise ModelNotFoundError(
            f"No trained model at {config.MODEL_PATH}. "
            "Run the training notebook in Colab, then copy the exported "
            ".tflite file into ai/models/."
        )

    interpreter_cls = _load_interpreter_class()
    try:
        interpreter = interpreter_cls(model_path=str(config.MODEL_PATH))
        interpreter.allocate_tensors()
    except Exception as exc:  # any TFLite load failure
        raise ModelNotFoundError(f"Failed to load model: {exc}") from exc

    _interpreter = interpreter
    return _interpreter


def predict_image(image_path: str) -> dict:
    """Run the full pipeline on one image and return a structured result.

    Raises ModelNotFoundError if no usable model is available yet.
    Returns a STATUS_ERROR dict (does not raise) for bad/corrupt images,
    since that's a normal, expected outcome the caller should display.
    """
    interpreter = _get_interpreter()

    try:
        input_tensor = prepare_image(image_path)
    except ImageValidationError as exc:
        return {
            "crop": config.CROP_NAME,
            "prediction": None,
            "confidence": None,
            "status": config.STATUS_ERROR,
            "recommendation": None,
            "error": str(exc),
        }

    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    try:
        interpreter.set_tensor(input_details[0]["index"], input_tensor)
        interpreter.invoke()
        output = interpreter.get_tensor(output_details[0]["index"])[0]
    except Exception as exc:
        raise InferenceError(f"Inference failed: {exc}") from exc

    if len(output) != len(config.CLASS_NAMES):
        raise InferenceError(
            f"Model outputs {len(output)} classes but config.CLASS_NAMES has "
            f"{len(config.CLASS_NAMES)}. Retrain or refresh model_metadata.json."
        )

    class_index = int(np.argmax(output))
    confidence = float(output[class_index])
    class_name = config.CLASS_NAMES[class_index]

    if confidence < config.CONFIDENCE_THRESHOLD:
        prediction, status = "Uncertain", config.STATUS_UNCERTAIN
    elif class_name == config.HEALTHY_LABEL:
        prediction, status = class_name, config.STATUS_HEALTHY
    else:
        prediction, status = class_name, config.STATUS_DISEASE_DETECTED

    return {
        "crop": config.CROP_NAME,
        "prediction": prediction,
        "confidence": round(confidence, 3),
        "status": status,
        "recommendation": config.RECOMMENDATIONS.get(prediction, config.DEFAULT_RECOMMENDATION),
        "error": None,
    }


def main():
    if len(sys.argv) != 2:
        print("Usage: python ai/inference/predict.py <image_path>")
        sys.exit(1)

    try:
        result = predict_image(sys.argv[1])
    except (ModelNotFoundError, InferenceError) as exc:
        print(json.dumps({"status": config.STATUS_ERROR, "error": str(exc)}, indent=2))
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
