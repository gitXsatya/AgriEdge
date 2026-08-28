"""
Unit tests for AgriEdge Decision Engine, Sensor Provider Abstraction,
Simulator, and Actuator.

Covers:
- Existing Predefined Scenarios
  - dry field
  - normal field
  - over-irrigated field
  - heat stress
- SensorProvider interface compliance
- RealSensorProvider placeholder behavior
- Sensor validation
- Stale sensor reading detection
- Future timestamp detection
- Invalid / unavailable / corrupted sensor data
- Fail-safe actuator behavior
- Pump remains OFF whenever sensor data is invalid
"""

import unittest
from datetime import datetime, timedelta
from dataclasses import dataclass
import sys
import os

# Add project root directory to sys.path
sys.path.insert(
    0,
    os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from app.sensors.base import (
    SensorProvider,
    SensorReading,
    ISensorData,
    is_reading_stale,
)
from app.sensors.simulator import SensorSimulator
from app.sensors.real import RealSensorProvider
from app.decision.engine import DecisionEngine
from app.actuator.pump import PumpActuator


@dataclass
class UnvalidatedTelemetry:
    """
    Mock telemetry object used to test raw inputs that bypass
    SensorReading validation.
    """

    soil_moisture: float
    temperature: float
    humidity: float
    timestamp: datetime


# ============================================================================
# PREDEFINED AGRICULTURAL SCENARIOS
# ============================================================================

class TestAgriEdgeScenarios(unittest.TestCase):
    """Test suite covering all predefined agricultural scenarios."""

    def setUp(self):
        self.simulator = SensorSimulator()
        self.engine = DecisionEngine()
        self.pump = PumpActuator()

    def test_dry_field_scenario(self):
        """
        Scenario: Dry field

        Expectations:
        - Water stress: True
        - Over-irrigation risk: False
        - Heat stress: False
        - Irrigation required: True
        - Recommendation: 'Irrigate now'
        - Pump: ON
        """

        reading = self.simulator.read_scenario("dry field")
        decision = self.engine.evaluate(reading)

        self.assertTrue(decision.water_stress)
        self.assertTrue(decision.irrigation_required)
        self.assertFalse(decision.over_irrigation_risk)
        self.assertFalse(decision.heat_stress)
        self.assertTrue(decision.is_valid)
        self.assertEqual(
            decision.recommendation,
            "Irrigate now"
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertTrue(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "ON")

    def test_normal_field_scenario(self):
        """
        Scenario: Normal field

        Expectations:
        - Water stress: False
        - Over-irrigation risk: False
        - Heat stress: False
        - Irrigation required: False
        - Recommendation: 'Irrigation not required'
        - Pump: OFF
        """

        reading = self.simulator.read_scenario("normal field")
        decision = self.engine.evaluate(reading)

        self.assertFalse(decision.water_stress)
        self.assertFalse(decision.irrigation_required)
        self.assertFalse(decision.over_irrigation_risk)
        self.assertFalse(decision.heat_stress)
        self.assertTrue(decision.is_valid)
        self.assertEqual(
            decision.recommendation,
            "Irrigation not required"
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_over_irrigated_field_scenario(self):
        """
        Scenario: Over-irrigated field

        Expectations:
        - Water stress: False
        - Over-irrigation risk: True
        - Heat stress: False
        - Irrigation required: False
        - Recommendation: 'Delay irrigation'
        - Pump: OFF
        """

        reading = self.simulator.read_scenario("over-irrigated field")
        decision = self.engine.evaluate(reading)

        self.assertFalse(decision.water_stress)
        self.assertFalse(decision.irrigation_required)
        self.assertTrue(decision.over_irrigation_risk)
        self.assertFalse(decision.heat_stress)
        self.assertTrue(decision.is_valid)
        self.assertEqual(
            decision.recommendation,
            "Delay irrigation"
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_heat_stress_scenario(self):
        """
        Scenario: Heat stress

        Expectations:
        - Heat stress: True
        - Over-irrigation risk: False
        - Irrigation required: True
        - Recommendation: 'Heat stress warning'
        - Pump: ON
        """

        reading = self.simulator.read_scenario("heat stress")
        decision = self.engine.evaluate(reading)

        self.assertTrue(decision.heat_stress)
        self.assertTrue(decision.irrigation_required)
        self.assertFalse(decision.over_irrigation_risk)
        self.assertTrue(decision.is_valid)
        self.assertEqual(
            decision.recommendation,
            "Heat stress warning"
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertTrue(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "ON")


# ============================================================================
# SENSOR VALIDATION AND SIMULATOR
# ============================================================================

class TestSensorValidationAndSimulator(unittest.TestCase):
    """Test sensor validation and simulator utility methods."""

    def test_valid_sensor_reading(self):
        """Test constructing and validating a normal sensor reading."""

        reading = SensorReading(
            soil_moisture=45.0,
            temperature=28.0,
            humidity=65.0,
        )

        self.assertEqual(reading.soil_moisture, 45.0)
        self.assertEqual(reading.temperature, 28.0)
        self.assertEqual(reading.humidity, 65.0)
        self.assertFalse(reading.is_stale())

    def test_invalid_soil_moisture_below_zero(self):
        """Check that soil moisture below 0 raises ValueError."""

        with self.assertRaises(ValueError):
            SensorReading(
                soil_moisture=-5.0,
                temperature=25.0,
                humidity=50.0,
            )

    def test_invalid_soil_moisture_above_100(self):
        """Check that soil moisture above 100 raises ValueError."""

        with self.assertRaises(ValueError):
            SensorReading(
                soil_moisture=150.0,
                temperature=25.0,
                humidity=50.0,
            )

    def test_invalid_humidity_below_zero(self):
        """Check that humidity below 0 raises ValueError."""

        with self.assertRaises(ValueError):
            SensorReading(
                soil_moisture=50.0,
                temperature=25.0,
                humidity=-10.0,
            )

    def test_invalid_humidity_above_100(self):
        """Check that humidity above 100 raises ValueError."""

        with self.assertRaises(ValueError):
            SensorReading(
                soil_moisture=50.0,
                temperature=25.0,
                humidity=120.0,
            )

    def test_invalid_scenario_name(self):
        """Check that an invalid scenario name raises KeyError."""

        simulator = SensorSimulator()

        with self.assertRaises(KeyError):
            simulator.read_scenario("non_existent_scenario")

    def test_custom_reading(self):
        """Check that custom reading creation works properly."""

        simulator = SensorSimulator()

        reading = simulator.read_custom(
            soil_moisture=20.0,
            temperature=30.0,
            humidity=40.0,
        )

        self.assertEqual(reading.soil_moisture, 20.0)
        self.assertEqual(reading.temperature, 30.0)
        self.assertEqual(reading.humidity, 40.0)


# ============================================================================
# PUMP ACTUATOR
# ============================================================================

class TestPumpActuatorDirect(unittest.TestCase):
    """Test direct pump operations and emergency stop."""

    def test_pump_toggle(self):
        """Test turning the pump ON and OFF directly."""

        pump = PumpActuator(name="Test Pump")

        self.assertFalse(pump.is_running)
        self.assertEqual(pump.get_status(), "OFF")

        pump.turn_on(reason="Testing ON")

        self.assertTrue(pump.is_running)
        self.assertEqual(pump.get_status(), "ON")

        pump.turn_off(reason="Testing OFF")

        self.assertFalse(pump.is_running)
        self.assertEqual(pump.get_status(), "OFF")

    def test_pump_emergency_stop(self):
        """Test that emergency stop immediately turns pump OFF."""

        pump = PumpActuator(name="Test Pump")

        pump.turn_on(reason="Running")

        self.assertTrue(pump.is_running)

        pump.emergency_stop(reason="Sensor fault detected")

        self.assertFalse(pump.is_running)
        self.assertEqual(pump.get_status(), "OFF")


# ============================================================================
# SENSOR PROVIDER ABSTRACTION
# ============================================================================

class TestSensorProviderAbstraction(unittest.TestCase):
    """
    Test SensorProvider interface, protocol compliance,
    and RealSensorProvider behavior.
    """

    def test_simulator_implements_sensor_provider(self):
        """Verify SensorSimulator implements SensorProvider."""

        simulator = SensorSimulator()

        self.assertIsInstance(simulator, SensorProvider)
        self.assertTrue(
            issubclass(SensorSimulator, SensorProvider)
        )

    def test_sensor_reading_matches_protocol(self):
        """Verify SensorReading complies with ISensorData."""

        reading = SensorReading(
            soil_moisture=25.0,
            temperature=30.0,
            humidity=50.0,
        )

        self.assertIsInstance(reading, ISensorData)
        self.assertEqual(reading.soil_moisture, 25.0)
        self.assertEqual(reading.temperature, 30.0)
        self.assertEqual(reading.humidity, 50.0)
        self.assertIsInstance(reading.timestamp, datetime)

    def test_decision_engine_evaluates_sensor_provider_directly(self):
        """Verify DecisionEngine can evaluate a SensorProvider directly."""

        simulator = SensorSimulator()
        simulator.set_scenario("dry field")

        engine = DecisionEngine()

        decision = engine.evaluate(simulator)

        self.assertTrue(decision.water_stress)
        self.assertTrue(decision.irrigation_required)
        self.assertTrue(decision.is_valid)
        self.assertEqual(
            decision.recommendation,
            "Irrigate now"
        )

    def test_real_sensor_provider_requires_connection(self):
        """
        Verify RealSensorProvider fails safely when the ESP32
        is disconnected.
        """

        real_provider = RealSensorProvider(port="COM3")

        self.assertIsInstance(real_provider, SensorProvider)
        self.assertTrue(
            issubclass(RealSensorProvider, SensorProvider)
        )

        # The placeholder/real provider should raise ConnectionError
        # when the requested serial connection is unavailable.
        with self.assertRaises(ConnectionError):
            real_provider.read()


# ============================================================================
# FAIL-SAFE AND SENSOR CORRUPTION TESTS
# ============================================================================

class TestActuatorSafetyAndFailSafe(unittest.TestCase):
    """
    Fail-Safe & Validation Tests.

    Verifies that if sensor data is invalid, unavailable, stale,
    corrupted, or outside valid ranges:

    - irrigation_required is False
    - the recommendation indicates invalid sensor data
    - the pump remains OFF
    """

    def setUp(self):
        self.engine = DecisionEngine()
        self.pump = PumpActuator()

    def test_failsafe_when_reading_is_none(self):
        """When sensor data is None, pump must remain OFF."""

        decision = self.engine.evaluate(None)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_failsafe_when_provider_throws_exception(self):
        """
        When a sensor provider raises an exception,
        the decision engine must fail safely.
        """

        class DisconnectedSensorProvider(SensorProvider):

            def read(self) -> SensorReading:
                raise RuntimeError(
                    "I2C Bus Error: Sensor not responding "
                    "on address 0x48"
                )

        faulty_provider = DisconnectedSensorProvider()

        decision = self.engine.evaluate(faulty_provider)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_stale_sensor_reading_detection(self):
        """Test stale sensor reading detection helper."""

        old_time = datetime.now() - timedelta(minutes=10)

        stale_reading = SensorReading(
            soil_moisture=20.0,
            temperature=25.0,
            humidity=50.0,
            timestamp=old_time,
        )

        self.assertTrue(
            stale_reading.is_stale(max_age_seconds=300.0)
        )

        self.assertTrue(
            is_reading_stale(
                stale_reading,
                max_age_seconds=300.0,
            )
        )

    def test_failsafe_when_sensor_data_is_stale(self):
        """
        When telemetry timestamp is older than the maximum
        allowed age, pump must remain OFF.
        """

        stale_timestamp = (
            datetime.now() - timedelta(minutes=10)
        )

        stale_reading = UnvalidatedTelemetry(
            soil_moisture=15.0,
            temperature=25.0,
            humidity=50.0,
            timestamp=stale_timestamp,
        )

        decision = self.engine.evaluate(stale_reading)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.assertIn(
            "stale",
            decision.details.lower()
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_failsafe_when_timestamp_is_in_future(self):
        """
        When telemetry timestamp is in the future,
        the decision engine must fail safely.
        """

        future_timestamp = (
            datetime.now() + timedelta(hours=2)
        )

        future_reading = UnvalidatedTelemetry(
            soil_moisture=15.0,
            temperature=25.0,
            humidity=50.0,
            timestamp=future_timestamp,
        )

        decision = self.engine.evaluate(future_reading)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_invalid_temperature_non_numeric(self):
        """Non-numeric temperature must cause a fail-safe decision."""

        corrupted = UnvalidatedTelemetry(
            soil_moisture=15.0,
            temperature="invalid_temp",  # type: ignore
            humidity=50.0,
            timestamp=datetime.now(),
        )

        decision = self.engine.evaluate(corrupted)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_temperature_outside_valid_range(self):
        """
        Temperature outside plausible agricultural limits
        must cause a fail-safe decision.
        """

        extreme_temp_reading = UnvalidatedTelemetry(
            soil_moisture=15.0,
            temperature=95.0,
            humidity=40.0,
            timestamp=datetime.now(),
        )

        decision = self.engine.evaluate(extreme_temp_reading)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_failsafe_when_soil_moisture_out_of_bounds(self):
        """
        Soil moisture outside 0-100% must cause a fail-safe decision.
        """

        out_of_range_reading = UnvalidatedTelemetry(
            soil_moisture=-15.0,
            temperature=25.0,
            humidity=50.0,
            timestamp=datetime.now(),
        )

        decision = self.engine.evaluate(out_of_range_reading)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_failsafe_when_humidity_out_of_bounds(self):
        """
        Humidity outside 0-100% must cause a fail-safe decision.
        """

        out_of_range_reading = UnvalidatedTelemetry(
            soil_moisture=15.0,
            temperature=25.0,
            humidity=150.0,
            timestamp=datetime.now(),
        )

        decision = self.engine.evaluate(out_of_range_reading)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_failsafe_when_nan_or_inf_telemetry(self):
        """NaN or infinity telemetry must cause a fail-safe decision."""

        nan_reading = UnvalidatedTelemetry(
            soil_moisture=float("nan"),
            temperature=25.0,
            humidity=50.0,
            timestamp=datetime.now(),
        )

        decision = self.engine.evaluate(nan_reading)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_failsafe_when_infinite_telemetry(self):
        """Infinite sensor values must cause a fail-safe decision."""

        inf_reading = UnvalidatedTelemetry(
            soil_moisture=float("inf"),
            temperature=25.0,
            humidity=50.0,
            timestamp=datetime.now(),
        )

        decision = self.engine.evaluate(inf_reading)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_failsafe_when_attributes_are_corrupted_or_none(self):
        """
        When telemetry attributes are None or corrupted,
        pump must remain OFF.
        """

        corrupted_reading = UnvalidatedTelemetry(
            soil_moisture=None,  # type: ignore
            temperature=25.0,
            humidity=50.0,
            timestamp=datetime.now(),
        )

        decision = self.engine.evaluate(corrupted_reading)

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")

    def test_missing_sensor_attribute(self):
        """
        When telemetry is missing a required attribute,
        pump must remain OFF.
        """

        class IncompleteData:
            soil_moisture = 20.0
            temperature = 25.0
            # humidity and timestamp intentionally missing

        decision = self.engine.evaluate(IncompleteData())

        self.assertFalse(decision.is_valid)
        self.assertFalse(decision.irrigation_required)
        self.assertEqual(
            decision.recommendation,
            DecisionEngine.RECOMMENDATION_SENSOR_INVALID
        )

        self.pump.set_state(decision.irrigation_required)

        self.assertFalse(self.pump.is_running)
        self.assertEqual(self.pump.get_status(), "OFF")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    unittest.main()

