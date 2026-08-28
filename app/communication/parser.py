"""
Hardware Communication & Serial Message Parser for AgriEdge.
Parses incoming telemetry strings (e.g. from ESP32 serial / UART stream)
into validated SensorReading structures without requiring active serial port hardware.

Expected message format:
MOISTURE=24.5,TEMP=34.2,HUMIDITY=48.0
"""
from datetime import datetime
import math
from typing import Dict, Optional

from app.sensors.base import SensorProvider, SensorReading
from config.thresholds import (
    VALID_SOIL_MOISTURE_MIN,
    VALID_SOIL_MOISTURE_MAX,
    VALID_HUMIDITY_MIN,
    VALID_HUMIDITY_MAX,
    VALID_TEMPERATURE_MIN,
    VALID_TEMPERATURE_MAX,
)


class InvalidTelemetryMessageError(ValueError):
    """Raised when an incoming serial message is malformed, missing keys, or out of range."""
    pass


class TelemetryParser:
    """
    Parser for ESP32 / Arduino serial telemetry messages.
    Converts key-value comma-separated message strings into validated SensorReading instances.
    """

    REQUIRED_KEYS = {"MOISTURE", "TEMP", "HUMIDITY"}

    def parse(self, raw_message: str) -> SensorReading:
        """
        Parse a raw serial message string into a validated SensorReading.
        
        Format:
        MOISTURE=24.5,TEMP=34.2,HUMIDITY=48.0

        Raises:
            InvalidTelemetryMessageError: If the message is malformed, missing fields,
                                         or contains out-of-range/non-numeric values.
        """
        if raw_message is None or not isinstance(raw_message, str):
            raise InvalidTelemetryMessageError("Message must be a non-empty string.")

        clean_message = raw_message.strip()
        if not clean_message:
            raise InvalidTelemetryMessageError("Received empty message string.")

        # Split key-value pairs by comma
        pairs = clean_message.split(",")
        parsed_values: Dict[str, float] = {}

        for pair in pairs:
            pair = pair.strip()
            if not pair:
                continue

            if "=" not in pair:
                raise InvalidTelemetryMessageError(f"Malformed key-value pair '{pair}'. Expected 'KEY=VALUE'.")

            parts = pair.split("=", 1)
            key = parts[0].strip().upper()
            val_str = parts[1].strip()

            # Normalize aliases if any (e.g., TEMPERATURE -> TEMP)
            if key == "TEMPERATURE":
                key = "TEMP"

            if not val_str:
                raise InvalidTelemetryMessageError(f"Missing value for key '{key}'.")

            try:
                val = float(val_str)
            except ValueError:
                raise InvalidTelemetryMessageError(f"Invalid numeric value '{val_str}' for key '{key}'.")

            if math.isnan(val) or math.isinf(val):
                raise InvalidTelemetryMessageError(f"Non-finite numeric value for key '{key}'.")

            parsed_values[key] = val

        # Validate presence of required keys
        missing_keys = self.REQUIRED_KEYS - set(parsed_values.keys())
        if missing_keys:
            raise InvalidTelemetryMessageError(
                f"Missing required telemetry keys: {', '.join(sorted(missing_keys))}."
            )

        moisture = parsed_values["MOISTURE"]
        temperature = parsed_values["TEMP"]
        humidity = parsed_values["HUMIDITY"]

        # Validate physical limits
        if not (VALID_SOIL_MOISTURE_MIN <= moisture <= VALID_SOIL_MOISTURE_MAX):
            raise InvalidTelemetryMessageError(
                f"Soil moisture {moisture:.1f}% outside valid range [{VALID_SOIL_MOISTURE_MIN}, {VALID_SOIL_MOISTURE_MAX}]."
            )

        if not (VALID_HUMIDITY_MIN <= humidity <= VALID_HUMIDITY_MAX):
            raise InvalidTelemetryMessageError(
                f"Humidity {humidity:.1f}% outside valid range [{VALID_HUMIDITY_MIN}, {VALID_HUMIDITY_MAX}]."
            )

        if not (VALID_TEMPERATURE_MIN <= temperature <= VALID_TEMPERATURE_MAX):
            raise InvalidTelemetryMessageError(
                f"Temperature {temperature:.1f} C outside valid range [{VALID_TEMPERATURE_MIN}, {VALID_TEMPERATURE_MAX}]."
            )

        return SensorReading(
            soil_moisture=moisture,
            temperature=temperature,
            humidity=humidity,
            scenario_name="esp32_serial",
            timestamp=datetime.now(),
        )

    def try_parse(self, raw_message: str) -> Optional[SensorReading]:
        """
        Safely parse raw message, returning None if validation fails instead of raising an error.
        """
        try:
            return self.parse(raw_message)
        except InvalidTelemetryMessageError:
            return None


class SerialMessageSensorProvider(SensorProvider):
    """
    SensorProvider implementation that ingests serial telemetry messages (e.g. from ESP32).
    Enables direct integration with DecisionEngine without touching hardware serial ports.
    """

    def __init__(self, parser: Optional[TelemetryParser] = None):
        self.parser = parser or TelemetryParser()
        self._current_reading: Optional[SensorReading] = None

    def feed_message(self, raw_message: str) -> SensorReading:
        """
        Feed a new incoming serial message string into the provider.
        Parses and stores the resulting SensorReading.
        """
        self._current_reading = self.parser.parse(raw_message)
        return self._current_reading

    def read(self) -> SensorReading:
        """
        SensorProvider interface implementation.
        Returns the latest successfully parsed reading.
        """
        if self._current_reading is None:
            raise RuntimeError("No valid telemetry message has been received from ESP32 serial stream.")
        return self._current_reading
