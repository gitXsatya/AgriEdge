# AgriEdge Smart Farm

Edge AI prototype for tomato leaf disease screening, built for a hackathon.
This document covers **Person 1's** deliverable: Edge AI / Computer Vision.

## 1. Overview

AgriEdge captures a photo of a tomato leaf on a phone, sends it to a laptop
over the local Wi-Fi network, and runs a locally-hosted TensorFlow Lite
model to screen for disease -- no cloud inference, no internet dependency
once the model is deployed.

## 2. Problem

Smallholder tomato farmers often can't access an agronomist quickly enough
to catch leaf disease early, when intervention is cheapest and most
effective. A phone photo and a few seconds of on-device inference can give
a fast first read.

## 3. Solution

A 3-class image classifier (Healthy / Early Blight / Late Blight) trained
via transfer learning on MobileNetV2, exported to TensorFlow Lite, and
served through a small local Flask app that a phone browser can reach over
the same Wi-Fi network as the laptop running it. No app install required.

## 4. Edge AI architecture

```
📱 Phone (camera) --HTTP--> 💻 Laptop (Flask) --> 🧠 TFLite model --> Dashboard
                                                        |
                                          (Person 2: sensor data) --> Decision engine --> Farmer advice
```

Inference runs entirely on the laptop, locally, via TensorFlow Lite --
this is the "edge" in Edge AI: no round trip to a cloud API.

## 5. Person 1 responsibility

Edge AI / Computer Vision: dataset pipeline, model training, evaluation,
TFLite conversion and verification, local inference module, and the
Flask bridge + dashboard that exposes results as clean JSON for Person 2
(sensor fusion) and Person 3 (overall dashboard/integration).

## 6. Dataset

**PlantVillage** tomato subset (Mohanty, Hughes & Salathé, 2016), sourced
from `spMohanty/PlantVillage-Dataset` on GitHub. Classes used:

| Folder (raw) | Class |
|---|---|
| `Tomato___healthy` | Healthy |
| `Tomato___Early_blight` | Early Blight |
| `Tomato___Late_blight` | Late Blight |

Exact image counts, class balance, and a corruption check are computed
live in the training notebook (`ai/training/AgriEdge_Tomato_Disease_Training.ipynb`)
-- see Section 13, "Actual Results," below once training has run.

Split: 70% train / 15% validation / 15% test, stratified by class, fixed
seed (42), no image appears in more than one split. The test set is
never used for training or model selection.

## 7. Supported classes

The prototype intentionally starts with **three** tomato classes to keep
the model focused and reliable within the hackathon scope:

1. Healthy
2. Early Blight
3. Late Blight

Class names live in one place (`ai/inference/config.py`, synced from
`ai/models/model_metadata.json` after training) -- nothing in the
codebase branches on a specific disease name.

## 8. Model architecture

```
Input (224x224x3)
  -> MobileNetV2 (ImageNet weights, frozen initially)
  -> GlobalAveragePooling2D
  -> Dropout(0.3)
  -> Dense(num_classes, softmax)
```

`num_classes` is derived from configuration, never hardcoded in more than
one place.

## 9. Why MobileNetV2

MobileNetV2 is a lightweight convolutional network designed to run
efficiently on resource-constrained devices. It gives a strong balance
of accuracy, model size, and inference speed, which matters here because
the final model needs to run locally rather than on a powerful server.

## 10. Transfer learning

Rather than training a network from scratch (which needs far more data
and time than a 5-hour hackathon allows), we reuse MobileNetV2's
ImageNet-pretrained features. The base is frozen while the new
classification head trains, then the top ~30 layers are optionally
unfrozen and fine-tuned at a much lower learning rate.

## 11. Training pipeline

- Preprocessing: resize to 224x224, scale to `[-1, 1]` (MobileNetV2's
  expected input range) -- identical logic in training and local inference.
- Augmentation (flip, small rotation/zoom/shift, mild brightness) applied
  to the training split only.
- Class weights applied if the dataset is meaningfully imbalanced.
- Optimizer: Adam. Loss: sparse categorical cross-entropy.
- Callbacks: EarlyStopping, ModelCheckpoint, ReduceLROnPlateau.
- Two phases: frozen-base head training, then optional fine-tuning.

Full, runnable pipeline: `ai/training/AgriEdge_Tomato_Disease_Training.ipynb`
(designed for Google Colab with a GPU runtime).

## 12. Evaluation

Reported on the untouched test set: accuracy, precision, recall, F1
(per-class and macro), and a confusion matrix. Misclassified examples are
inspected directly rather than assumed away.

## 13. Actual results

**To be populated after training.** Run the notebook end-to-end in
Colab; its final cell prints a ready-to-paste summary block -- replace
this section with that output. Until then, no numbers are claimed here.

## 14. TFLite conversion

Exported with dynamic-range quantization (`tf.lite.Optimize.DEFAULT`):
smaller, faster model, with a documented small potential accuracy cost.
The notebook does not assume this tradeoff is acceptable -- it re-runs
the actual `.tflite` model against the real test set and reports the
Keras-vs-TFLite accuracy difference directly.

Output: `ai/models/tomato_disease_model.tflite` + `ai/models/model_metadata.json`.

## 15. Local inference

```bash
python ai/inference/predict.py test_images/example.jpg
```

Returns JSON built entirely from the model's real output tensor:

```json
{
  "crop": "Tomato",
  "prediction": "Early Blight",
  "confidence": 0.917,
  "status": "DISEASE_DETECTED",
  "recommendation": "Possible early blight. Remove and dispose of affected lower leaves...",
  "error": null
}
```

If confidence is below the configured threshold (default 0.80),
`prediction` becomes `"Uncertain"` and `status` becomes `"UNCERTAIN"`
rather than forcing a guess.

## 16. Phone -> laptop architecture

The laptop runs a Flask server bound to `0.0.0.0:5000`. A phone on the
same Wi-Fi network opens `http://<laptop-ip>:5000` in its browser (no
app install), captures or uploads a photo, and submits it. The laptop
saves the image, runs inference, and both the phone and any laptop
browser with the page open update via a lightweight JS poll against
`/api/latest` every few seconds.

## 17. Local setup

```bash
git clone <your-repo-url>
cd AgriEdge
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Then place the trained model (from Colab) into `ai/models/`:
- `tomato_disease_model.tflite`
- `model_metadata.json`

## 18. Running the application

```bash
python app/app.py
```

Find your laptop's LAN IP (`ipconfig` on Windows, `ifconfig`/`ip a` on
macOS/Linux), then on your phone (same Wi-Fi) open:

```
http://<laptop-ip>:5000
```

## 19. API / JSON output

`GET /api/latest` returns the same structured result shape as
`predict_image()` (see Section 15), plus `has_result`, `image_url`, and
`timestamp`. This is the integration point for Person 2 and Person 3.

## 20. Person 2 integration (sensor data)

This module never implements sensor/threshold logic. It exposes:

```json
{"crop": "Tomato", "prediction": "...", "confidence": 0.0, "status": "..."}
```

Person 2 combines this with sensor readings (soil moisture, temperature,
humidity) in their own decision engine to produce farmer advice.

## 21. Person 3 integration (dashboard/overall app)

`GET /api/latest` on the Flask server (Section 19) is the contract:
captured image URL, crop, prediction, confidence, status, and
recommendation, all as JSON. Person 3's dashboard can poll or fetch this
directly without depending on any AI-specific code.

## 22. Limitations

- Screens for only 3 conditions; anything else will be forced into the
  closest of these three classes or reported as low-confidence/uncertain.
- Trained and evaluated on the PlantVillage dataset, which is captured
  under fairly controlled conditions -- real field photos (variable
  lighting, backgrounds, multiple leaves) may perform differently. This
  is a hackathon prototype for tomato leaf disease **screening**, not a
  clinically validated diagnostic tool, and has not been field-validated.
- Single in-memory "latest result" on the server -- fine for a live demo,
  not designed for multiple concurrent users/devices.

## 23. Future expansion

Architecture supports adding classes without touching inference/UI code:

1. Add labeled images for the new class(es) -- candidates: Leaf Mold,
   Septoria Leaf Spot, Two-Spotted Spider Mite (all present in the same
   PlantVillage source under `Tomato___*`).
2. Update `CLASS_NAMES` in the training notebook.
3. Retrain, evaluate, export a new `.tflite` + `model_metadata.json`.
4. Keep the current model as a versioned fallback
   (e.g. `tomato_disease_model_v1.tflite`) before replacing it.

No changes needed to `predict.py`, `app.py`, or the dashboard -- they
read class names and recommendations from configuration, not code.
