"""
Service alur deteksi radar → RFID → capture kamera.

Alur mode "both" / "rfid_only":
  radar mendeteksi objek
    → buat detection (status awaiting_rfid)
    → frontend menampilkan modal RFID
    → RFID diterima → kirim perintah capture ke kamera
    → simpan kendaraan + buka gate

Alur mode "plate_only":
  radar mendeteksi objek
    → buat detection (status waiting_capture)
    → tunggu CAPTURE_DELAY_SECONDS (default 5 detik)
    → kirim perintah capture ke kamera
    → simpan kendaraan + buka gate
"""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException

from app.config import settings
from app.database import get_db
from app.Models.Detection import Detection
from app.Models.Vehicle import Vehicle
from app.Services import VehicleService

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = ("awaiting_rfid", "waiting_capture", "capturing")
TERMINAL_STATUSES = ("captured", "failed", "expired")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except Exception:
        return None


class DetectionService:
    def _get_model(self, detection_id: str) -> Optional[Detection]:
        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM detections WHERE detection_id = ?",
                (detection_id,),
            ).fetchone()
            if not row:
                return None
            return Detection.from_row(row)

    def has_active(self, direction: str) -> bool:
        """True jika masih ada deteksi aktif untuk arah tersebut."""
        placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
        with get_db() as conn:
            row = conn.execute(
                f"SELECT 1 FROM detections WHERE direction = ? AND status IN ({placeholders}) LIMIT 1",
                (direction, *ACTIVE_STATUSES),
            ).fetchone()
            return row is not None

    def get_pending(self, direction: Optional[str] = None) -> list[dict]:
        """Ambil semua deteksi aktif (belum selesai capture)."""
        placeholders = ",".join("?" for _ in ACTIVE_STATUSES)
        query = f"SELECT * FROM detections WHERE status IN ({placeholders})"
        params = list(ACTIVE_STATUSES)
        if direction:
            query += " AND direction = ?"
            params.append(direction)
        query += " ORDER BY created_at DESC"

        with get_db() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
            return [self._serialize(Detection.from_row(row)) for row in rows]

    def get(self, detection_id: str) -> Optional[dict]:
        detection = self._get_model(detection_id)
        if not detection:
            return None
        return self._serialize(detection)

    async def on_radar_detected(self, direction: str) -> Optional[dict]:
        """
        Dipanggil saat radar mendeteksi objek (rising edge).
        Membuat sesi deteksi baru sesuai mode validasi.
        """
        if self.has_active(direction):
            logger.info(f"Radar {direction}: masih ada deteksi aktif, event baru diabaikan.")
            return None

        mode = settings.VALIDATION_MODE
        detection_id = str(uuid.uuid4())
        now = _now()

        if mode == "plate_only":
            status = "waiting_capture"
            capture_at = now + timedelta(seconds=settings.CAPTURE_DELAY_SECONDS)
        else:
            status = "awaiting_rfid"
            capture_at = None

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO detections
                    (detection_id, direction, status, capture_at, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    detection_id,
                    direction,
                    status,
                    capture_at.isoformat() if capture_at else None,
                    now.isoformat(),
                    now.isoformat(),
                ),
            )

        logger.info(
            f"Radar mendeteksi objek ({direction}) — mode {mode}, status {status}, ID: {detection_id}"
        )

        if mode == "plate_only":
            asyncio.create_task(self._capture_after_delay(detection_id))

        return self.get(detection_id)

    async def submit_rfid(self, detection_id: str, rfid_uid: Optional[str]) -> Optional[dict]:
        """
        Terima RFID dari frontend, lalu jadwalkan capture kamera.
        Return None jika detection tidak ditemukan.
        """
        if rfid_uid is not None:
            raw = str(rfid_uid).strip()
            normalized_rfid = raw if raw else "-"
        else:
            normalized_rfid = "-"

        now = _now_iso()

        with get_db() as conn:
            row = conn.execute(
                "SELECT * FROM detections WHERE detection_id = ?",
                (detection_id,),
            ).fetchone()
            if not row:
                return None

            detection = Detection.from_row(row)
            if detection.status != "awaiting_rfid":
                return self._serialize(detection)

            cursor = conn.execute(
                """
                UPDATE detections
                SET status = 'waiting_capture', rfid_uid = ?, capture_at = ?, updated_at = ?
                WHERE detection_id = ? AND status = 'awaiting_rfid'
                """,
                (normalized_rfid, now, now, detection_id),
            )
            if cursor.rowcount == 0:
                return self.get(detection_id)

        logger.info(
            f"RFID diterima untuk deteksi {detection_id} ({detection.direction}) — mengirim perintah capture ke kamera."
        )

        asyncio.create_task(self._process_capture(detection_id))
        return self.get(detection_id)

    async def _capture_after_delay(self, detection_id: str):
        """Tunggu sampai capture_at (mode plate_only), lalu capture."""
        try:
            detection = self._get_model(detection_id)
            if not detection or detection.status != "waiting_capture":
                return

            capture_at = _parse_datetime(detection.capture_at)
            if capture_at:
                remaining = (capture_at - _now()).total_seconds()
            else:
                remaining = 0

            if remaining > 0:
                await asyncio.sleep(remaining)

            await self._process_capture(detection_id)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.error(f"Gagal menunggu delay capture {detection_id}: {e}")
            self._finish_failed(detection_id, f"Gagal menjadwalkan capture: {e}")

    async def _process_capture(self, detection_id: str):
        """Ambil gambar dari kamera, simpan kendaraan, buka gate."""
        detection = self._get_model(detection_id)
        if not detection:
            return

        with get_db() as conn:
            cursor = conn.execute(
                """
                UPDATE detections
                SET status = 'capturing', updated_at = ?
                WHERE detection_id = ? AND status = 'waiting_capture'
                """,
                (_now_iso(), detection_id),
            )
            if cursor.rowcount == 0 and detection.status != "capturing":
                return

        detection = self._get_model(detection_id)
        if not detection:
            return

        logger.info(f"Capture kamera untuk deteksi {detection_id} ({detection.direction})...")

        try:
            outcome = await asyncio.to_thread(
                VehicleService.capture_and_save,
                detection.direction,
                None,
                detection.rfid_uid,
            )
        except HTTPException as e:
            logger.warning(f"Capture gagal untuk deteksi {detection_id}: {e.detail}")
            self._finish_failed(detection_id, str(e.detail))
            return
        except Exception as e:
            logger.error(f"Capture gagal untuk deteksi {detection_id}: {e}")
            self._finish_failed(detection_id, f"Capture gagal: {e}")
            return

        if outcome.ignored or outcome.vehicle is None:
            reason = outcome.reason or "Kendaraan tidak dapat diproses."
            logger.info(f"Deteksi {detection_id} diabaikan: {reason}")
            self._finish_failed(detection_id, reason)
            return

        vehicle = outcome.vehicle
        mode = settings.VALIDATION_MODE
        has_rfid = bool(detection.rfid_uid and detection.rfid_uid != "-")

        # Cek kecocokan RFID untuk keluar
        if detection.direction == "keluar" and has_rfid and mode in ("rfid_only", "both"):
            from app.Http.Controllers.RfidController import _check_rfid_match
            rfid_match = _check_rfid_match(vehicle.plate_number, detection.rfid_uid)
            if rfid_match is False:
                logger.warning(
                    f"RFID mismatch untuk {vehicle.plate_number}: '{detection.rfid_uid}' tidak cocok dengan data masuk."
                )
                self._finish_failed(
                    detection_id,
                    "RFID tidak cocok dengan record masuk. Gate tidak dibuka.",
                )
                return

        # Buka gate
        self._open_gate(detection.direction, vehicle.plate_number)

        # Update status deteksi selesai
        with get_db() as conn:
            conn.execute(
                """
                UPDATE detections
                SET status = 'captured', event_id = ?, vehicle_id = ?, updated_at = ?
                WHERE detection_id = ?
                """,
                (vehicle.event_id, vehicle.id, _now_iso(), detection_id),
            )

        logger.info(f"Deteksi {detection_id} selesai — plat '{vehicle.plate_number}', gate dibuka.")

    def _open_gate(self, direction: str, plate_number: str):
        """Jadwalkan buka/tutup gate sesuai arah."""
        from app.Http.Controllers.RelayController import RelayController

        if direction == "masuk":
            open_ch = settings.CAMERA_IN_RELAY_OPEN
            close_ch = settings.CAMERA_IN_RELAY_CLOSE
        else:
            open_ch = settings.CAMERA_OUT_RELAY_OPEN
            close_ch = settings.CAMERA_OUT_RELAY_CLOSE

        asyncio.create_task(
            RelayController.open_and_close_delayed(open_ch, 15, close_ch)
        )
        logger.info(f"Gate {direction} dijadwalkan buka untuk plat '{plate_number}'")

    def _finish_failed(self, detection_id: str, message: str):
        with get_db() as conn:
            conn.execute(
                """
                UPDATE detections
                SET status = 'failed', message = ?, updated_at = ?
                WHERE detection_id = ?
                """,
                (message, _now_iso(), detection_id),
            )

    def cleanup_stale(self):
        """Tandai deteksi yang menggantung terlalu lama sebagai expired/failed."""
        now = _now()
        with get_db() as conn:
            rows = conn.execute(
                f"SELECT * FROM detections WHERE status IN ({','.join('?' for _ in ACTIVE_STATUSES)})",
                ACTIVE_STATUSES,
            ).fetchall()

            for row in rows:
                detection = Detection.from_row(row)
                ref_time_str = detection.updated_at or detection.created_at
                reference = _parse_datetime(ref_time_str)
                if not reference:
                    continue

                if detection.status == "awaiting_rfid":
                    timeout = settings.DETECTION_RFID_TIMEOUT
                    final_status = "expired"
                    message = "Waktu input RFID habis."
                else:
                    timeout = settings.DETECTION_CAPTURE_TIMEOUT
                    final_status = "failed"
                    message = "Capture timeout."

                if (now - reference).total_seconds() > timeout:
                    conn.execute(
                        """
                        UPDATE detections
                        SET status = ?, message = ?, updated_at = ?
                        WHERE detection_id = ?
                        """,
                        (final_status, message, now.isoformat(), detection.detection_id),
                    )
                    logger.warning(
                        f"Deteksi {detection.detection_id} ({detection.direction}) ditutup ({final_status}): {message}"
                    )

    def mark_orphaned_on_startup(self):
        """Capture yang terputus karena node restart tidak bisa dilanjutkan."""
        with get_db() as conn:
            cursor = conn.execute(
                f"""
                UPDATE detections
                SET status = 'failed', message = 'Server di-restart saat deteksi berlangsung', updated_at = ?
                WHERE status IN ({','.join('?' for _ in ACTIVE_STATUSES)})
                """,
                (_now_iso(), *ACTIVE_STATUSES),
            )
            if cursor.rowcount > 0:
                logger.info(f"Membersihkan {cursor.rowcount} deteksi yatim dari session sebelumnya.")

    def _serialize(self, detection: Detection) -> dict:
        data = detection.to_dict()

        capture_in_seconds = None
        if detection.status == "waiting_capture" and detection.capture_at:
            capture_at = _parse_datetime(detection.capture_at)
            if capture_at:
                capture_in_seconds = max(0, int((capture_at - _now()).total_seconds() + 0.999))
        data["capture_in_seconds"] = capture_in_seconds

        data["vehicle"] = None
        if detection.event_id:
            with get_db() as conn:
                row = conn.execute(
                    "SELECT * FROM vehicles WHERE event_id = ?",
                    (detection.event_id,),
                ).fetchone()
                if row:
                    data["vehicle"] = VehicleService.to_out_dict(Vehicle.from_row(row))

        return data


detection_service = DetectionService()

