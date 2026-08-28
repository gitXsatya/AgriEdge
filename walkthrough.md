# AgriEdge Phase 2 Architecture Walkthrough

## Summary of Phase 2 Implementation
Completed Phase 2: Hardware-Ready Architecture with strict decoupling, validation, data freshness/staleness checks, fail-safe actuator protection, and placeholder for real sensor integration.

### Deliverables:
1. **SensorProvider Abstraction ([app/sensors/base.py](file:///C:/Users/KIIT/Desktop/AgriEdge/app/sensors/base.py))**:
   - `SensorProvider`: Abstract Base Class with `read() -> SensorReading`.
   - `SensorReading`: Data model with `soil_moisture`, `temperature`, `humidity`, `timestamp`, and `is_stale()` method.
   - `ISensorData`: Structural runtime protocol.
2. **SensorSimulator ([app/sensors/simulator.py](file:///C:/Users/KIIT/Desktop/AgriEdge/app/sensors/simulator.py))**:
   - Implements `SensorProvider` interface for development without physical hardware.
3. **RealSensorProvider Placeholder ([app/sensors/real.py](file:///C:/Users/KIIT/Desktop/AgriEdge/app/sensors/real.py))**:
   - Placeholder subclass of `SensorProvider` for future hardware driver attachment (ADC/I2C/SPI).
4. **DecisionEngine Decoupling & Fail-Safe ([app/decision/engine.py](file:///C:/Users/KIIT/Desktop/AgriEdge/app/decision/engine.py))**:
   - Depends solely on `SensorProvider` / `ISensorData`.
   - Validates ranges: Soil Moisture (0–100%), Humidity (0–100%), Temperature (-20–60 °C).
   - Enforces fail-safe: Invalid, unavailable, stale, or out-of-range telemetry forces `irrigation_required = False` (Pump remains OFF) and issues `"Sensor data invalid — irrigation disabled."`.
5. **Full Test Suite & CLI Demo**:
   - 42 tests passing via `pytest`.
   - CLI execution (`python -m app.main`) runs all 4 predefined scenarios successfully.

---

## Test Run Results

```bash
pytest -v
```

```text
==================== 42 passed, 7 subtests passed in 0.17s ====================
```
