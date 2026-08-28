"""
Decision Engine for AgriEdge.
Evaluates sensor telemetry against agronomic thresholds to determine:
- water stress
- irrigation required
- over-irrigation risk
- heat stress

And generates farmer-friendly recommendations:
- 'Irrigate now'
- 'Irrigation not required'
- 'Delay irrigation'
- 'Heat stress warning'
- 'Sensor data invalid — irrigation disabled.' (Fail-safe for invalid/stale/unavailable sensor data)

Includes comprehensive fail-safe validation:
If sensor data is invalid, unavailable, stale, or outside valid ranges,
the engine guarantees irrigation_required is False so the pump remains OFF.
"""
from dataclasses import dataclass
from datetime import datetime
import math
from typing import Any, Optional, Tuple, Union

from app.sensors.base import SensorProvider, SensorReading, ISensorData, is_reading_stale
from config.thresholds import (
    SOIL_MOISTURE_DRY_THRESHOLD,
    SOIL_MOISTURE_OVER_IRRIGATED_THRESHOLD,
    TEMPERATURE_HEAT_STRESS_THRESHOLD,
    VALID_SOIL_MOISTURE_MIN,
    VALID_SOIL_MOISTURE_MAX,
    VALID_HUMIDITY_MIN,
    VALID_HUMIDITY_MAX,
    VALID_TEMPERATURE_MIN,
    VALID_TEMPERATURE_MAX,
    MAX_SENSOR_DATA_AGE_SECONDS,
)


@dataclass(frozen=True)
class DecisionResult:
    """Represents the outcome of the agronomic evaluation."""
    water_stress: bool
    irrigation_required: bool
    over_irrigation_risk: bool
    heat_stress: bool
    recommendation: str
    details: str
    is_valid: bool = True


class DecisionEngine:
    """
    Evaluates sensor readings and generates actionable agricultural recommendations.
    Pure software logic decoupled from concrete sensor implementations.
    Depends only on the SensorProvider / ISensorData abstraction.
    """

    RECOMMENDATION_IRRIGATE_NOW = "Irrigate now"
    RECOMMENDATION_NOT_REQUIRED = "Irrigation not required"
    RECOMMENDATION_DELAY_IRRIGATION = "Delay irrigation"
    RECOMMENDATION_HEAT_STRESS_WARNING = "Heat stress warning"
    RECOMMENDATION_SENSOR_INVALID = "Sensor data invalid — irrigation disabled."

    def __init__(
        self,
        moisture_dry_threshold: float = SOIL_MOISTURE_DRY_THRESHOLD,
        moisture_over_threshold: float = SOIL_MOISTURE_OVER_IRRIGATED_THRESHOLD,
        temp_heat_threshold: float = TEMPERATURE_HEAT_STRESS_THRESHOLD,
        max_data_age_seconds: float = MAX_SENSOR_DATA_AGE_SECONDS,
    ):
        self.moisture_dry_threshold = moisture_dry_threshold
        self.moisture_over_threshold = moisture_over_threshold
        self.temp_heat_threshold = temp_heat_threshold
        self.max_data_age_seconds = max_data_age_seconds

    def _validate_telemetry(self, reading: Any) -> Tuple[bool, Optional[str]]:
        """
        Validates sensor telemetry integrity, bounds, and timeliness.
        Returns (is_valid, error_reason).
        """
        if reading is None:
            return False, "Sensor data is unavailable (None)."

        # Check required fields
        for field_name in ("soil_moisture", "temperature", "humidity", "timestamp"):
            if not hasattr(reading, field_name):
                return False, f"Missing required telemetry attribute '{field_name}'."
            if getattr(reading, field_name) is None:
                return False, f"Telemetry attribute '{field_name}' is None."

        # Check numeric types and non-NaN/inf values
        for field_name in ("soil_moisture", "temperature", "humidity"):
            val = getattr(reading, field_name)
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                return False, f"Telemetry attribute '{field_name}' must be numeric, got {type(val).__name__}."
            if math.isnan(val) or math.isinf(val):
                return False, f"Telemetry attribute '{field_name}' contains non-finite value ({val})."

        # Check physical ranges
        sm = float(reading.soil_moisture)
        if not (VALID_SOIL_MOISTURE_MIN <= sm <= VALID_SOIL_MOISTURE_MAX):
            return False, f"Soil moisture ({sm:.1f}%) is outside valid range [{VALID_SOIL_MOISTURE_MIN}, {VALID_SOIL_MOISTURE_MAX}]."

        hum = float(reading.humidity)
        if not (VALID_HUMIDITY_MIN <= hum <= VALID_HUMIDITY_MAX):
            return False, f"Humidity ({hum:.1f}%) is outside valid range [{VALID_HUMIDITY_MIN}, {VALID_HUMIDITY_MAX}]."

        temp = float(reading.temperature)
        if not (VALID_TEMPERATURE_MIN <= temp <= VALID_TEMPERATURE_MAX):
            return False, f"Temperature ({temp:.1f} C) is outside valid range [{VALID_TEMPERATURE_MIN}, {VALID_TEMPERATURE_MAX}]."

        # Check timestamp and staleness
        ts = reading.timestamp
        if not isinstance(ts, datetime):
            return False, f"Timestamp must be a datetime instance, got {type(ts).__name__}."

        now = datetime.now()
        age_seconds = (now - ts).total_seconds()
        if age_seconds > self.max_data_age_seconds:
            return False, f"Sensor data is stale ({age_seconds:.1f}s old > {self.max_data_age_seconds}s limit)."
        if age_seconds < -60.0:  # More than 1 minute in the future
            return False, f"Sensor timestamp is in the future ({ts})."

        return True, None

    def evaluate(self, reading_or_provider: Union[ISensorData, SensorReading, SensorProvider, Any]) -> DecisionResult:
        """
        Analyze sensor telemetry and return diagnostic flags and farmer recommendation.
        Accepts either a SensorReading / ISensorData instance or a SensorProvider implementation.
        
        Enforces fail-safe: if data is invalid, unavailable, stale, or out of range,
        irrigation_required is False and pump remains OFF.
        """
        # 1. Acquire reading if a provider was given
        if isinstance(reading_or_provider, SensorProvider):
            try:
                reading = reading_or_provider.read()
            except Exception as err:
                return DecisionResult(
                    water_stress=False,
                    irrigation_required=False,
                    over_irrigation_risk=False,
                    heat_stress=False,
                    recommendation=self.RECOMMENDATION_SENSOR_INVALID,
                    details=f"FAIL-SAFE: Sensor provider acquisition error ({err}). Pump held OFF.",
                    is_valid=False,
                )
        else:
            reading = reading_or_provider

        # 2. Validate telemetry integrity, ranges, and staleness
        is_valid, error_msg = self._validate_telemetry(reading)
        if not is_valid:
            return DecisionResult(
                water_stress=False,
                irrigation_required=False,
                over_irrigation_risk=False,
                heat_stress=False,
                recommendation=self.RECOMMENDATION_SENSOR_INVALID,
                details=f"FAIL-SAFE: {error_msg} Pump held OFF.",
                is_valid=False,
            )

        # 3. Diagnostic evaluations for valid telemetry
        water_stress = reading.soil_moisture < self.moisture_dry_threshold
        over_irrigation_risk = reading.soil_moisture > self.moisture_over_threshold
        heat_stress = reading.temperature >= self.temp_heat_threshold

        # 4. Decision & Recommendation logic
        # 4a. Heat stress condition takes precedence for critical alerts
        if heat_stress:
            recommendation = self.RECOMMENDATION_HEAT_STRESS_WARNING
            irrigation_required = not over_irrigation_risk
            details = (
                f"Critical ambient temperature detected ({reading.temperature:.1f} C >= {self.temp_heat_threshold:.1f} C). "
                f"Crops are experiencing severe heat stress. Urgent cooling/irrigation advised."
            )
        # 4b. Over-irrigated risk
        elif over_irrigation_risk:
            recommendation = self.RECOMMENDATION_DELAY_IRRIGATION
            irrigation_required = False
            details = (
                f"High soil moisture detected ({reading.soil_moisture:.1f}% > {self.moisture_over_threshold:.1f}%). "
                f"Risk of root rot and oxygen depletion. Suspend all watering."
            )
        # 4c. Water stress (dry field)
        elif water_stress:
            recommendation = self.RECOMMENDATION_IRRIGATE_NOW
            irrigation_required = True
            details = (
                f"Soil moisture critically low ({reading.soil_moisture:.1f}% < {self.moisture_dry_threshold:.1f}%). "
                f"Crop root zone is dehydrated. Start irrigation immediately."
            )
        # 4d. Normal / Optimal conditions
        else:
            recommendation = self.RECOMMENDATION_NOT_REQUIRED
            irrigation_required = False
            details = (
                f"Soil moisture ({reading.soil_moisture:.1f}%) and temperature ({reading.temperature:.1f} C) "
                f"are within the optimal growth range. No intervention needed."
            )

        return DecisionResult(
            water_stress=water_stress,
            irrigation_required=irrigation_required,
            over_irrigation_risk=over_irrigation_risk,
            heat_stress=heat_stress,
            recommendation=recommendation,
            details=details,
            is_valid=True,
        )
