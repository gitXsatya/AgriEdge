"""
Threshold configurations for AgriEdge Decision Engine.
These thresholds define agronomic boundaries for soil moisture,
temperature, and humidity, as well as predefined simulation scenario parameters.
"""

# Soil Moisture Thresholds (percentage: 0 - 100%)
SOIL_MOISTURE_DRY_THRESHOLD = 30.0          # Below this level: crop suffers from water stress
SOIL_MOISTURE_OPTIMAL_MIN = 30.0            # Lower bound of optimal soil moisture
SOIL_MOISTURE_OPTIMAL_MAX = 70.0            # Upper bound of optimal soil moisture
SOIL_MOISTURE_OVER_IRRIGATED_THRESHOLD = 70.0  # Above this level: risk of over-irrigation / waterlogging

# Temperature Thresholds (Celsius)
TEMPERATURE_HEAT_STRESS_THRESHOLD = 38.0    # At or above this level: crops experience heat stress
TEMPERATURE_OPTIMAL_MIN = 18.0
TEMPERATURE_OPTIMAL_MAX = 32.0

# Humidity Thresholds (percentage: 0 - 100%)
HUMIDITY_LOW_THRESHOLD = 30.0               # Dry air accelerates evapotranspiration
HUMIDITY_HIGH_THRESHOLD = 85.0              # Saturated air reduces evaporation

# Sensor Validity & Safety Range Bounds (Physical limits for validation fail-safe)
VALID_SOIL_MOISTURE_MIN = 0.0
VALID_SOIL_MOISTURE_MAX = 100.0
VALID_HUMIDITY_MIN = 0.0
VALID_HUMIDITY_MAX = 100.0
VALID_TEMPERATURE_MIN = -20.0               # Plausible agricultural ambient min (Celsius)
VALID_TEMPERATURE_MAX = 60.0                # Plausible agricultural ambient max (Celsius)

# Staleness Safety Threshold (Seconds)
MAX_SENSOR_DATA_AGE_SECONDS = 300.0         # Telemetry older than 5 minutes is considered stale

# Predefined Simulation Scenarios
SCENARIOS = {
    "dry field": {
        "name": "dry field",
        "description": "Low soil moisture requiring immediate irrigation.",
        "soil_moisture": 18.0,
        "temperature": 26.0,
        "humidity": 45.0,
    },
    "normal field": {
        "name": "normal field",
        "description": "Optimal soil moisture and ambient conditions.",
        "soil_moisture": 52.0,
        "temperature": 25.0,
        "humidity": 60.0,
    },
    "over-irrigated field": {
        "name": "over-irrigated field",
        "description": "High soil moisture indicating waterlogged soil.",
        "soil_moisture": 85.0,
        "temperature": 24.0,
        "humidity": 80.0,
    },
    "heat stress": {
        "name": "heat stress",
        "description": "High ambient temperature with low humidity inducing severe crop heat stress.",
        "soil_moisture": 28.0,
        "temperature": 41.5,
        "humidity": 22.0,
    },
}
