"""
AgriEdge CLI Application Entry Point.

Modes:

1. Simulator mode:
   Runs the four predefined scenarios.

2. Hardware mode:
   Reads real ESP32 telemetry through USB serial COM3,
   sends it through the parser and Decision Engine,
   and produces the farmer recommendation.
"""

import sys
import os

# Add project root to sys.path
sys.path.insert(
    0,
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

from app.sensors import SensorSimulator, SensorReading
from app.sensors.real import RealSensorProvider
from app.decision.engine import DecisionEngine
from app.actuator.pump import PumpActuator


def process_reading(
    reading: SensorReading,
    engine: DecisionEngine,
    pump: PumpActuator,
    title: str = "LIVE SENSOR",
):
    """Run one sensor reading through the complete AgriEdge pipeline."""

    print("=" * 70)
    print(f"[*] RUNNING: {title}")
    print("=" * 70)

    # --------------------------------------------------
    # 1. SENSOR TELEMETRY
    # --------------------------------------------------

    print("[1. SENSOR TELEMETRY]")

    print(
        f"   * Soil Moisture : "
        f"{reading.soil_moisture:.2f}%"
    )

    print(
        f"   * Temperature   : "
        f"{reading.temperature:.2f} C"
    )

    print(
        f"   * Air Humidity  : "
        f"{reading.humidity:.2f}%"
    )

    print(
        f"   * Timestamp     : "
        f"{reading.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    print()

    # --------------------------------------------------
    # 2. DECISION ENGINE
    # --------------------------------------------------

    decision = engine.evaluate(reading)

    print("[2. DECISION ENGINE EVALUATION]")

    print(
        "   * Water Stress         : "
        f"{'[YES] (Low Moisture)' if decision.water_stress else '[NO] (Adequate)'}"
    )

    print(
        "   * Over-irrigation Risk : "
        f"{'[YES] (Waterlogged)' if decision.over_irrigation_risk else '[NO] (Safe)'}"
    )

    print(
        "   * Heat Stress          : "
        f"{'[YES] (Critical Temp)' if decision.heat_stress else '[NO] (Optimal)'}"
    )

    print(
        "   * Irrigation Required  : "
        f"{'[YES]' if decision.irrigation_required else '[NO]'}"
    )

    print()

    # --------------------------------------------------
    # 3. FARMER RECOMMENDATION
    # --------------------------------------------------

    print("[3. FARMER RECOMMENDATION]")

    print(
        f'   >>> "{decision.recommendation}" <<<'
    )

    print(
        f"   Details: {decision.details}"
    )

    print()

    # --------------------------------------------------
    # 4. ACTUATOR DECISION
    # --------------------------------------------------

    print("[4. ACTUATOR ACTION]")

    pump.set_state(
        decision.irrigation_required,
        reason=decision.recommendation,
    )

    print("=" * 70)
    print()


def run_simulator():
    """Run the original four predefined scenarios."""

    simulator = SensorSimulator()
    engine = DecisionEngine()
    pump = PumpActuator()

    scenarios = simulator.get_available_scenarios()

    for scenario_name in scenarios:

        reading = simulator.read_scenario(
            scenario_name
        )

        process_reading(
            reading,
            engine,
            pump,
            title=scenario_name.upper(),
        )

    print(
        "All 4 predefined scenarios evaluated successfully!\n"
    )


def run_hardware(port: str = "COM3"):
    """
    Run AgriEdge using real ESP32 sensor data.
    """

    engine = DecisionEngine()
    pump = PumpActuator()

    print("\n" + "#" * 70)
    print("              AgriEdge - LIVE HARDWARE MODE")
    print("#" * 70)

    print()
    print(f"[HARDWARE] Port       : {port}")
    print("[HARDWARE] Baud Rate  : 115200")
    print("[HARDWARE] Sensors    : ESP32 + Capacitive Moisture + DHT22")
    print()
    print("Waiting for ESP32 telemetry...")
    print("Press CTRL+C to stop.")
    print()

    provider = RealSensorProvider(
        port=port,
        baud_rate=115200,
        timeout=3.0,
    )

    try:

        provider.connect()

        while True:

            reading = provider.read()

            process_reading(
                reading,
                engine,
                pump,
                title="LIVE ESP32 SENSOR READING",
            )

    except KeyboardInterrupt:

        print("\n[HARDWARE] Stopping AgriEdge...")

    except ConnectionError as exc:

        print(f"\n[ERROR] Hardware connection failed:")
        print(f"        {exc}")

    except TimeoutError as exc:

        print(f"\n[ERROR] Sensor timeout:")
        print(f"        {exc}")

    finally:

        provider.disconnect()

        print("[HARDWARE] ESP32 disconnected.")
        print()


def main():

    print("\n" + "#" * 70)
    print("           AgriEdge - Precision Irrigation Decision Engine")
    print("#" * 70)

    # --------------------------------------------------
    # COMMAND LINE MODE
    # --------------------------------------------------

    if len(sys.argv) > 1:

        mode = sys.argv[1].lower()

        if mode == "hardware":
            port = (
                sys.argv[2]
                if len(sys.argv) > 2
                else "COM3"
            )

            run_hardware(port)
            return

        if mode == "simulator":
            run_simulator()
            return

        print()
        print("Unknown mode.")
        print()
        print("Use:")
        print("  python -m app.main simulator")
        print("  python -m app.main hardware COM3")
        print()

        return

    # Default = simulator
    run_simulator()


if __name__ == "__main__":
    main()