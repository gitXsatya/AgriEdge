"""
Unit tests for AgriEdge Hardware Communication Module (ESP32 Serial Message Parser).
Tests:
- Valid message parsing
- Missing moisture key
- Invalid temperature value
- Humidity above 100%
- Malformed messages
- Integration with SensorProvider and DecisionEngine
"""
import unittest
from datetime import datetime
import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.sensors.base import SensorReading
from app.communication.parser import (
    TelemetryParser,
    InvalidTelemetryMessageError,
    SerialMessageSensorProvider,
)
from app.decision.engine import DecisionEngine
from app.actuator.pump import PumpActuator


class TestESP32TelemetryParser(unittest.TestCase):
    """Test suite for ESP32 serial telemetry parser and validation rules."""

    def setUp(self):
        self.parser = TelemetryParser()

    def test_valid_message(self):
        """Test parsing of a standard valid ESP32 serial telemetry message."""
        raw = "MOISTURE=24.5,TEMP=34.2,HUMIDITY=48.0"
        reading = self.parser.parse(raw)

        self.assertIsInstance(reading, SensorReading)
        self.assertAlmostEqual(reading.soil_moisture, 24.5)
        self.assertAlmostEqual(reading.temperature, 34.2)
        self.assertAlmostEqual(reading.humidity, 48.0)
        self.assertEqual(reading.scenario_name, "esp32_serial")
        self.assertIsInstance(reading.timestamp, datetime)

    def test_valid_message_with_whitespace_and_mixed_case(self):
        """Test parsing messages with spaces and case variations."""
        raw = " moisture = 18.0 , Temp = 26.5 , humidity = 55.0 \r\n"
        reading = self.parser.parse(raw)

        self.assertEqual(reading.soil_moisture, 18.0)
        self.assertEqual(reading.temperature, 26.5)
        self.assertEqual(reading.humidity, 55.0)

    def test_missing_moisture(self):
        """Test rejection when MOISTURE key is missing."""
        raw = "TEMP=34.2,HUMIDITY=48.0"
        with self.assertRaises(InvalidTelemetryMessageError) as ctx:
            self.parser.parse(raw)
        self.assertIn("MOISTURE", str(ctx.exception))

    def test_missing_temperature(self):
        """Test rejection when TEMP key is missing."""
        raw = "MOISTURE=24.5,HUMIDITY=48.0"
        with self.assertRaises(InvalidTelemetryMessageError) as ctx:
            self.parser.parse(raw)
        self.assertIn("TEMP", str(ctx.exception))

    def test_missing_humidity(self):
        """Test rejection when HUMIDITY key is missing."""
        raw = "MOISTURE=24.5,TEMP=34.2"
        with self.assertRaises(InvalidTelemetryMessageError) as ctx:
            self.parser.parse(raw)
        self.assertIn("HUMIDITY", str(ctx.exception))

    def test_invalid_temperature_non_numeric(self):
        """Test rejection when temperature contains non-numeric characters."""
        raw = "MOISTURE=24.5,TEMP=abc,HUMIDITY=48.0"
        with self.assertRaises(InvalidTelemetryMessageError) as ctx:
            self.parser.parse(raw)
        self.assertIn("Invalid numeric value", str(ctx.exception))

    def test_invalid_temperature_out_of_bounds(self):
        """Test rejection when temperature exceeds valid physical range (e.g. 95 C)."""
        raw = "MOISTURE=24.5,TEMP=95.0,HUMIDITY=48.0"
        with self.assertRaises(InvalidTelemetryMessageError) as ctx:
            self.parser.parse(raw)
        self.assertIn("outside valid range", str(ctx.exception))

    def test_humidity_above_100(self):
        """Test rejection when humidity is above 100%."""
        raw = "MOISTURE=24.5,TEMP=34.2,HUMIDITY=105.0"
        with self.assertRaises(InvalidTelemetryMessageError) as ctx:
            self.parser.parse(raw)
        self.assertIn("outside valid range", str(ctx.exception))

    def test_humidity_below_zero(self):
        """Test rejection when humidity is negative."""
        raw = "MOISTURE=24.5,TEMP=34.2,HUMIDITY=-5.0"
        with self.assertRaises(InvalidTelemetryMessageError) as ctx:
            self.parser.parse(raw)
        self.assertIn("outside valid range", str(ctx.exception))

    def test_soil_moisture_above_100(self):
        """Test rejection when soil moisture is above 100%."""
        raw = "MOISTURE=120.0,TEMP=34.2,HUMIDITY=48.0"
        with self.assertRaises(InvalidTelemetryMessageError) as ctx:
            self.parser.parse(raw)
        self.assertIn("outside valid range", str(ctx.exception))

    def test_malformed_message_corrupted_format(self):
        """Test rejection on completely malformed strings."""
        malformed_samples = [
            "CORRUPTED_SERIAL_STREAM_ERROR",
            "MOISTURE:24.5;TEMP:34.2;HUMIDITY:48.0",
            "MOISTURE=,TEMP=34.2,HUMIDITY=48.0",
            "MOISTURE=24.5,TEMP=34.2,HUMIDITY=",
            "===",
            "",
            "   ",
        ]
        for sample in malformed_samples:
            with self.subTest(sample=sample):
                with self.assertRaises(InvalidTelemetryMessageError):
                    self.parser.parse(sample)

    def test_try_parse_helper(self):
        """Test that try_parse returns None on error and SensorReading on success."""
        self.assertIsNone(self.parser.try_parse("INVALID_MESSAGE"))
        reading = self.parser.try_parse("MOISTURE=20.0,TEMP=25.0,HUMIDITY=50.0")
        self.assertIsNotNone(reading)
        self.assertEqual(reading.soil_moisture, 20.0)


class TestSerialProviderDecisionEngineIntegration(unittest.TestCase):
    """Test integrating the ESP32 serial provider directly with DecisionEngine and Actuator."""

    def test_end_to_end_serial_stream_to_pump_control(self):
        """Simulate feeding ESP32 serial lines through the provider to the decision engine."""
        provider = SerialMessageSensorProvider()
        engine = DecisionEngine()
        pump = PumpActuator(name="ESP32 Controlled Pump")

        # 1. Feed a dry message -> pump should turn ON
        provider.feed_message("MOISTURE=15.0,TEMP=28.0,HUMIDITY=40.0")
        decision = engine.evaluate(provider)

        self.assertTrue(decision.water_stress)
        self.assertTrue(decision.irrigation_required)
        self.assertEqual(decision.recommendation, "Irrigate now")
        pump.set_state(decision.irrigation_required)
        self.assertTrue(pump.is_running)

        # 2. Feed a normal message -> pump should turn OFF
        provider.feed_message("MOISTURE=55.0,TEMP=26.0,HUMIDITY=60.0")
        decision = engine.evaluate(provider)

        self.assertFalse(decision.water_stress)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(decision.recommendation, "Irrigation not required")
        pump.set_state(decision.irrigation_required)
        self.assertFalse(pump.is_running)

    def test_invalid_serial_message_triggers_engine_failsafe(self):
        """Verify that an unhandled invalid message fed to provider keeps pump OFF."""
        class RawBrokenProvider(SerialMessageSensorProvider):
            def read(self):
                # Simulates exception during read
                raise InvalidTelemetryMessageError("Corrupted UART buffer")

        broken_provider = RawBrokenProvider()
        engine = DecisionEngine()
        pump = PumpActuator()

        decision = engine.evaluate(broken_provider)
        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)

        pump.set_state(decision.irrigation_required)
        self.assertFalse(pump.is_running)


if __name__ == "__main__":
    unittest.main()
