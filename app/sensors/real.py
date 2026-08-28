"""
Real ESP32 sensor provider for AgriEdge.

Reads telemetry from an ESP32 over USB serial.

Expected ESP32 message format:
MOISTURE=45.2,TEMP=27.4,HUMIDITY=61.0
"""

from typing import Optional

import serial

from app.communication.parser import TelemetryParser
from app.sensors.base import SensorProvider, SensorReading


class RealSensorProvider(SensorProvider):
    """
    Reads real sensor telemetry from an ESP32 through USB serial.
    """

    def __init__(
        self,
        port: str,
        baud_rate: int = 115200,
        timeout: float = 2.0,
        parser: Optional[TelemetryParser] = None,
    ):
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.parser = parser or TelemetryParser()
        self.serial_connection = None
        self.is_connected = False

    def connect(self) -> None:
        """Open the USB serial connection to the ESP32."""

        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=self.timeout,
            )

            self.is_connected = True

            print(
                f"[HARDWARE] Connected to ESP32 on "
                f"{self.port} at {self.baud_rate} baud."
            )

        except serial.SerialException as exc:
            self.is_connected = False
            self.serial_connection = None

            raise ConnectionError(
                f"Unable to connect to ESP32 on {self.port}: {exc}"
            ) from exc

    def disconnect(self) -> None:
        """Safely close the serial connection."""

        if self.serial_connection is not None:
            try:
                self.serial_connection.close()
            finally:
                self.serial_connection = None
                self.is_connected = False

    def read(self) -> SensorReading:
        """
        Read telemetry from ESP32 and convert it into SensorReading.

        Invalid startup/boot messages are skipped automatically.
        """

        if not self.is_connected or self.serial_connection is None:
            raise ConnectionError(
                "ESP32 serial connection is not available."
            )

        while True:
            try:
                raw_message = (
                    self.serial_connection.readline()
                    .decode("utf-8", errors="replace")
                    .strip()
                )

            except (serial.SerialException, OSError) as exc:
                self.is_connected = False

                raise ConnectionError(
                    f"Lost communication with ESP32: {exc}"
                ) from exc

            if not raw_message:
                raise TimeoutError(
                    "No sensor data received from ESP32."
                )

            # Ignore ESP32 boot messages and other non-telemetry lines.
            if not raw_message.startswith("MOISTURE="):
                continue

            try:
                return self.parser.parse(raw_message)

            except ValueError:
                # Ignore malformed serial lines and wait for
                # the next valid telemetry message.
                continue

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()