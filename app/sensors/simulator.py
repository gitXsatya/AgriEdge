"""
Sensor Simulator for AgriEdge.
Implements the SensorProvider interface to simulate environmental
and soil conditions without physical hardware.
"""
import random
from typing import List, Optional

from config.thresholds import SCENARIOS
from app.sensors.base import SensorProvider, SensorReading


class SensorSimulator(SensorProvider):
    """
    Simulates agricultural sensors (soil moisture, temperature, humidity).
    Implements SensorProvider interface so it can be swapped with RealSensorProvider.
    """

    def __init__(self, default_scenario: str = "normal field"):
        self._available_scenarios = SCENARIOS
        self._current_scenario = default_scenario

    def get_available_scenarios(self) -> List[str]:
        """Return list of predefined scenario names."""
        return list(self._available_scenarios.keys())

    def set_scenario(self, scenario_name: str) -> None:
        """Set the active scenario for default read() calls."""
        normalized_name = scenario_name.strip().lower()
        if normalized_name not in self._available_scenarios:
            raise KeyError(
                f"Unknown scenario '{scenario_name}'. Available: {list(self._available_scenarios.keys())}"
            )
        self._current_scenario = normalized_name

    def read(self) -> SensorReading:
        """
        Implementation of SensorProvider.read().
        Returns sensor reading for the currently configured scenario.
        """
        return self.read_scenario(self._current_scenario)

    def read_scenario(self, scenario_name: str) -> SensorReading:
        """
        Simulate sensor readings for a predefined scenario.
        """
        normalized_name = scenario_name.strip().lower()
        if normalized_name not in self._available_scenarios:
            raise KeyError(
                f"Unknown scenario '{scenario_name}'. Available: {list(self._available_scenarios.keys())}"
            )

        data = self._available_scenarios[normalized_name]
        return SensorReading(
            soil_moisture=float(data["soil_moisture"]),
            temperature=float(data["temperature"]),
            humidity=float(data["humidity"]),
            scenario_name=normalized_name,
        )

    def read_custom(self, soil_moisture: float, temperature: float, humidity: float) -> SensorReading:
        """
        Create a custom sensor reading snapshot.
        """
        return SensorReading(
            soil_moisture=float(soil_moisture),
            temperature=float(temperature),
            humidity=float(humidity),
            scenario_name="custom",
        )

    def read_random(self) -> SensorReading:
        """
        Generate a random sensor reading within plausible physical limits.
        """
        return SensorReading(
            soil_moisture=round(random.uniform(10.0, 95.0), 1),
            temperature=round(random.uniform(15.0, 45.0), 1),
            humidity=round(random.uniform(15.0, 90.0), 1),
            scenario_name="random",
        )
