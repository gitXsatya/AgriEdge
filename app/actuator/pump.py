"""
Simulated Pump Actuator for AgriEdge.
Simulates turning an irrigation pump ON or OFF without real GPIO/relay hardware.
Includes fail-safe handling and safety interlocks.
"""
from typing import Optional


class PumpActuator:
    """
    Simulated pump actuator.
    Provides a standardized interface (turn_on, turn_off, set_state, emergency_stop)
    so hardware drivers (Relay, MOSFET, GPIO) can easily drop in later.
    """

    def __init__(self, name: str = "Main Irrigation Pump"):
        self.name = name
        self.is_running: bool = False

    def turn_on(self, reason: Optional[str] = None) -> None:
        """Engage the simulated pump."""
        self.is_running = True
        reason_str = f" | Reason: {reason}" if reason else ""
        print(f"[ACTUATOR] [PUMP ON] {self.name} Status: ON{reason_str}")

    def turn_off(self, reason: Optional[str] = None) -> None:
        """Disengage the simulated pump."""
        self.is_running = False
        reason_str = f" | Reason: {reason}" if reason else ""
        print(f"[ACTUATOR] [PUMP OFF] {self.name} Status: OFF{reason_str}")

    def set_state(self, activate: bool, reason: Optional[str] = None) -> None:
        """
        Set pump state based on boolean decision.
        Enforces fail-safe: if activate is False or not strictly truthy, pump remains OFF.
        """
        if bool(activate):
            self.turn_on(reason)
        else:
            self.turn_off(reason)

    def emergency_stop(self, reason: str = "Fail-safe triggered") -> None:
        """Immediately disengage the pump for fail-safe protection."""
        self.turn_off(reason=f"FAIL-SAFE STOP - {reason}")

    def get_status(self) -> str:
        """Return the current pump status as a string ('ON' or 'OFF')."""
        return "ON" if self.is_running else "OFF"
