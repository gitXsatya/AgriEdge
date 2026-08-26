"""
AgriEdge - Image preprocessing (Person 1 - Edge AI).

The exact same resize + scale steps here are used conceptually for
training, validation, testing, and local inference, so the model never
sees a distribution shift between training and the real world.

Preprocessing math: this reimplements the MobileNetV2 'tf'-mode formula
(scale [0,255] -> [-1,1]) directly with numpy:

    tf.keras.applications.mobilenet_v2.preprocess_input(x)
        is documented to scale pixels to [-1, 1], and is equivalent to
    tf.keras.layers.Rescaling(1./127.5, offset=-1)(x)
        i.e. x / 127.5 - 1.0

Doing it with numpy (instead of importing TensorFlow just for this one
function) keeps local inference lightweight -- tflite-runtime + numpy +
Pillow is enough, no full TensorFlow install required on the edge
device. The training notebook uses the official TF function directly;
both produce identical output since it's the same formula.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from PIL import Image, UnidentifiedImageError

import config

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class ImageValidationError(ValueError):
    """Raised when an uploaded/loaded image cannot be used for inference."""


def load_image(image_path: str) -> Image.Image:
    """Load an image from disk and validate it can actually be used."""
    path = Path(image_path)

    if not path.exists():
        raise ImageValidationError(f"Image not found: {image_path}")

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ImageValidationError(
            f"Unsupported image format '{path.suffix}'. "
            f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
        )

    try:
        image = Image.open(path)
        image.verify()  # cheap structural corruption check
        image = Image.open(path)  # re-open: verify() leaves the handle unusable
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageValidationError(f"Could not read image (corrupted?): {exc}") from exc

    return image.convert("RGB")


def preprocess_for_model(image: Image.Image) -> np.ndarray:
    """Resize + MobileNetV2 'tf'-mode scaling. Returns shape (1, H, W, 3) float32."""
    height, width = config.IMAGE_SIZE
    resized = image.resize((width, height), Image.BILINEAR)
    array = np.asarray(resized, dtype=np.float32)
    array = (array / 127.5) - 1.0  # [0,255] -> [-1,1]
    return np.expand_dims(array, axis=0)


def prepare_image(image_path: str) -> np.ndarray:
    """End-to-end: load from disk, validate, and preprocess for the model."""
    image = load_image(image_path)
    return preprocess_for_model(image)
