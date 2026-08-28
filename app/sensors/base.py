"""
Sensor Provider Abstraction Layer for AgriEdge.
Defines the base interface / protocol for sensor telemetry acquisition,
enabling interchangeable use between SensorSimulator and future RealSensorProvider hardware drivers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import math
from typing import Any, Optional, Protocol, Tuple, runtime_checkable

from config.thresholds import (
    VALID_SOIL_MOISTURE_MIN,
    VALID_SOIL_MOISTURE_MAX,
    VALID_HUMIDITY_MIN,
    VALID_HUMIDITY_MAX,
    VALID_TEMPERATURE_MIN,
    VALID_TEMPERATURE_MAX,
    MAX_SENSOR_DATA_AGE_SECONDS,
)


@dataclass(frozen=True)
class SensorReading:
    """
    Standardized sensor telemetry data model providing:
    - soil_moisture: Soil moisture percentage (0.0 - 100.0%)
    - temperature: Ambient temperature in Celsius
    - humidity: Relative air humidity percentage (0.0 - 100.0%)
    - timestamp: Date and time of telemetry acquisition
    """
    soil_moisture: float  # Percentage (0 - 100)
    temperature: float    # Celsius
    humidity: float       # Percentage (0 - 100)
    scenario_name: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not (0.0 <= self.soil_moisture <= 100.0):
            raise ValueError(f"Soil moisture must be between 0 and 100%, got {self.soil_moisture}")
        if not (0.0 <= self.humidity <= 100.0):
            raise ValueError(f"Humidity must be between 0 and 100%, got {self.humidity}")

    def is_stale(self, max_age_seconds: float = MAX_SENSOR_DATA_AGE_SECONDS) -> bool:
        """Helper to determine whether the reading is stale."""
        if not isinstance(self.timestamp, datetime):
            return True
        age = (datetime.now() - self.timestamp).total_seconds()
        return age > max_age_seconds or age < -60.0


def is_reading_stale(reading: Any, max_age_seconds: float = MAX_SENSOR_DATA_AGE_SECONDS) -> bool:
    """Standalone helper to determine whether any sensor reading object is stale."""
    if reading is None or not hasattr(reading, "timestamp"):
        return True
    ts = getattr(reading, "timestamp")
    if not isinstance(ts, datetime):
        return True
    age = (datetime.now() - ts).total_seconds()
    return age > max_age_seconds or age < -60.0


@runtime_checkable
class ISensorData(Protocol):
    """
    Structural protocol for any sensor data container.
    Guarantees access to:
    - soil_moisture (float)
    - temperature (float)
    - humidity (float)
    - timestamp (datetime)
    """
    soil_moisture: float
    temperature: float
    humidity: float
    timestamp: datetime


class SensorProvider(ABC):
    """
    Abstract Base Class / Interface for Sensor Providers.
    Defines the contract for acquiring sensor telemetry.
    Implemented by SensorSimulator and future RealSensorProvider (ADC, I2C, SPI, UART).
    """

    @abstractmethod
    def read(self) -> SensorReading:
        """
        Acquire current sensor readings.
        Returns a SensorReading containing:
        - soil_moisture (float)
        - temperature (float)
        - humidity (float)
        - timestamp (datetime)
        """
        pass
