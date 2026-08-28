# 🌾 AgriEdge - Precision Irrigation & Monitoring

AgriEdge is a modular, hardware-independent precision agriculture prototype designed for automated crop monitoring and intelligent irrigation decision-making.

---

## 📁 Project Structure

```text
AgriEdge/
├── app/
│   ├── sensors/
│   │   ├── __init__.py        # Exports SensorProvider, SensorReading, ISensorData, SensorSimulator, RealSensorProvider
│   │   ├── base.py            # SensorProvider abstraction, ISensorData protocol, and SensorReading data model
│   │   ├── real.py            # RealSensorProvider placeholder for future hardware integration
│   │   └── simulator.py       # SensorSimulator implementing SensorProvider
│   ├── decision/
│   │   ├── __init__.py
│   │   └── engine.py          # Agronomic decision engine with validation & fail-safe logic
│   ├── actuator/
│   │   ├── __init__.py
│   │   └── pump.py            # Simulated irrigation pump actuator (prints ON/OFF status)
│   ├── communication/
│   │   ├── __init__.py
│   │   └── parser.py          # ESP32 serial telemetry parser & SerialMessageSensorProvider
│   └── main.py                # Main CLI demo runner executing all scenarios
├── tests/
│   ├── __init__.py
│   ├── test_scenarios.py      # Tests for scenarios, validation, staleness, fail-safe, and abstraction
│   └── test_communication.py  # Tests for serial parser and message validation
├── config/
│   ├── __init__.py
│   └── thresholds.py          # Centralized agronomic thresholds & validity ranges
├── requirements.txt           # Minimal test dependency (pytest)
└── README.md                  # Project documentation
```

---

## 🔌 Hardware Integration Architecture

```text
SensorProvider (Interface)
        ↓
  SensorReading
        ↓
 Decision Engine (Validation & Logic)
        ↓
  DecisionResult
        ↓
     Actuator (Pump ON / OFF)
```

- **`SensorProvider` Abstraction**: Both [`SensorSimulator`](file:///C:/Users/KIIT/Desktop/AgriEdge/app/sensors/simulator.py) and future [`RealSensorProvider`](file:///C:/Users/KIIT/Desktop/AgriEdge/app/sensors/real.py) implement the `SensorProvider` interface, returning standardized [`SensorReading`](file:///C:/Users/KIIT/Desktop/AgriEdge/app/sensors/base.py) objects.
- **Current Development**: `SensorSimulator` provides realistic telemetry for local development and testing without physical hardware.
- **Future Hardware Integration**: `RealSensorProvider` will connect to physical hardware controllers (e.g. ESP32 / Raspberry Pi reading ADC moisture and I2C/SPI temperature & humidity sensors) and feed telemetry directly into the Decision Engine without modifying any decision logic.

---

## 🛡️ Validation & Fail-Safe Protection

- **Telemetry Bounds**: Soil moisture (`0–100%`), humidity (`0–100%`), temperature (`-20–60 °C`).
- **Data Freshness**: Stale readings exceeding timeout (default: 300s) are flagged as unsafe.
- **Fail-Safe Rule**: If sensor telemetry is invalid, unavailable, stale, or out-of-range, the system guarantees `irrigation_required = False`, keeping the pump strictly **OFF** and issuing `"Sensor data invalid — irrigation disabled."`.

---

## 📊 Predefined Simulation Scenarios

| Scenario | Soil Moisture | Temperature | Humidity | Decision Engine Assessment | Farmer Recommendation | Pump Actuator |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **dry field** | 18.0% | 26.0 °C | 45.0% | Water Stress | `Irrigate now` | 🟢 **ON** |
| **normal field** | 52.0% | 25.0 °C | 60.0% | Optimal Conditions | `Irrigation not required` | 🔴 **OFF** |
| **over-irrigated field** | 85.0% | 24.0 °C | 80.0% | Over-irrigation Risk | `Delay irrigation` | 🔴 **OFF** |
| **heat stress** | 28.0% | 41.5 °C | 22.0% | Heat Stress | `Heat stress warning` | 🟢 **ON** |

---

## 🚀 How to Run

### Run All Tests
```bash
pytest
```
or:
```bash
python -m pytest
```

### Run Application Demo
```bash
python -m app.main
```
