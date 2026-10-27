"""
Service pembaca input radar via Modbus TCP (Discrete Input).

Radar dihubungkan ke relay BSM:
  - Address 0 (X1) = arah MASUK
  - Address 1 (X2) = arah KELUAR

Setiap perubahan status LOW → HIGH dianggap satu deteksi objek.
Deteksi diteruskan ke DetectionService untuk memulai alur RFID/capture.
"""
import asyncio
import logging
import socket
import time
from datetime import datetime, timezone
from typing import Optional

from pymodbus.client import ModbusTcpClient

from app.config import settings
from app.Services.DetectionService import detection_service

logger = logging.getLogger(__name__)


class RadarModbusClient(ModbusTcpClient):
    """
    ModbusTcpClient yang membuang byte sapaan 0x00 dari relay BSM.
    Relay BSM mengirim 1 byte 0x00 begitu koneksi TCP dibuka (tanpa diminta).
    Byte itu membuat header MBAP bergeser dan memunculkan error
    "Invalid Modbus protocol id: 256".
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._greeting_done = False

    def connect(self):
        already_connected = self.socket is not None
        if not super().connect():
            return False
        if not already_connected and not self._greeting_done:
            try:
                self.socket.settimeout(0.5)
                self.socket.recv(1)  # buang byte sapaan
            except (socket.timeout, OSError):
                pass
            finally:
                timeout = getattr(self.comm_params, "timeout_connect", 2.0)
                self.socket.settimeout(timeout)
            self._greeting_done = True
        return True


class RadarService:
    def __init__(self):
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._client: Optional[RadarModbusClient] = None
        self._client_key: Optional[tuple] = None
        self._previous_state = {"masuk": None, "keluar": None}
        self._last_trigger = {"masuk": 0.0, "keluar": 0.0}
        self._connected = False
        self._last_error: Optional[str] = None
        self._last_detection_at: Optional[str] = None
        self._error_logged_at = 0.0

    def start(self):
        if self._task and not self._task.done():
            return

        detection_service.mark_orphaned_on_startup()

        self._running = True
        self._task = asyncio.create_task(self._loop())

        if not settings.RADAR_ENABLED:
            logger.info("RadarService standby — radar nonaktif (RADAR_ENABLED=false).")
        else:
            logger.info(
                f"RadarService started — {settings.RADAR_HOST}:{settings.RADAR_PORT}, "
                f"poll {settings.RADAR_POLL_INTERVAL}s, X1(masuk)={settings.RADAR_ADDRESS_IN}, "
                f"X2(keluar)={settings.RADAR_ADDRESS_OUT}"
            )

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._close_client()
        logger.info("RadarService stopped")

    async def _loop(self):
        last_cleanup = 0.0
        while self._running:
            if not settings.RADAR_ENABLED:
                self._close_client()
                await asyncio.sleep(2.0)
                continue

            delay = max(settings.RADAR_POLL_INTERVAL, 0.1)
            await asyncio.sleep(delay)

            try:
                readings = await asyncio.to_thread(self._poll_once)
                now = time.monotonic()

                for direction, state in readings.items():
                    previous = self._previous_state.get(direction)
                    self._previous_state[direction] = state

                    # Rising edge: LOW -> HIGH
                    if previous is False and state is True:
                        self._handle_rising_edge(direction, now)

                # Periodik bersihkan deteksi kadaluarsa
                if now - last_cleanup > 10:
                    last_cleanup = now
                    detection_service.cleanup_stale()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._connected = False
                self._last_error = str(e)
                self._log_error_throttled(str(e))

    def _handle_rising_edge(self, direction: str, now: float):
        cooldown = settings.RADAR_COOLDOWN
        elapsed = now - self._last_trigger.get(direction, 0.0)
        if elapsed < cooldown:
            logger.debug(
                f"Radar {direction}: cooldown {cooldown}s belum lewat ({elapsed:.1f}s), deteksi diabaikan."
            )
            return

        self._last_trigger[direction] = now
        self._last_detection_at = datetime.now(timezone.utc).isoformat()
        logger.info(f"RADAR MENDETEKSI OBJEK — arah {direction}!")
        asyncio.create_task(detection_service.on_radar_detected(direction))

    def _ensure_client(self) -> RadarModbusClient:
        key = (settings.RADAR_HOST, settings.RADAR_PORT)
        if self._client is None or self._client_key != key:
            self._close_client()
            self._client = RadarModbusClient(
                settings.RADAR_HOST,
                port=settings.RADAR_PORT,
                timeout=2,
                retries=1,
            )
            self._client_key = key
        return self._client

    def _poll_once(self) -> dict[str, bool]:
        client = self._ensure_client()
        if not client.connected:
            if not client.connect():
                self._connected = False
                raise ConnectionError(
                    f"Gagal terhubung ke radar {settings.RADAR_HOST}:{settings.RADAR_PORT}"
                )

        self._connected = True
        addresses = {
            "masuk": settings.RADAR_ADDRESS_IN,
            "keluar": settings.RADAR_ADDRESS_OUT,
        }
        readings = {}
        errors = []

        for direction, address in addresses.items():
            try:
                response = client.read_discrete_inputs(
                    address=address,
                    count=1,
                    device_id=settings.RADAR_DEVICE_ID,
                )
                if response.isError():
                    errors.append(f"{direction}@{address}: {response}")
                else:
                    readings[direction] = bool(response.bits[0])
            except Exception as e:
                errors.append(f"{direction}@{address}: {e}")

        if errors:
            self._last_error = "; ".join(errors)
            logger.debug(f"Sebagian input radar gagal dibaca: {self._last_error}")

        return readings

    def _close_client(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            self._client_key = None
            self._connected = False

    def _log_error_throttled(self, error: str):
        now = time.monotonic()
        if now - self._error_logged_at > 30:
            self._error_logged_at = now
            logger.warning(f"Radar tidak bisa dibaca: {error}")

    def status(self) -> dict:
        return {
            "enabled": settings.RADAR_ENABLED,
            "connected": bool(self._connected),
            "host": settings.RADAR_HOST,
            "port": settings.RADAR_PORT,
            "address_in": settings.RADAR_ADDRESS_IN,
            "address_out": settings.RADAR_ADDRESS_OUT,
            "last_detection_at": self._last_detection_at,
            "last_error": self._last_error,
        }


radar_service = RadarService()

