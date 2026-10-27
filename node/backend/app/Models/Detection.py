"""
Model Detection — sesi deteksi radar sebelum capture kamera.

Alur:
  radar mendeteksi objek → detection dibuat (awaiting_rfid / waiting_capture)
  → RFID diterima / jeda selesai → capture kamera → detection captured.
"""
from dataclasses import dataclass
from typing import Optional
import sqlite3


@dataclass
class Detection:
    id: Optional[int] = None
    detection_id: str = ""
    direction: str = ""
    status: str = "awaiting_rfid"
    rfid_uid: Optional[str] = None
    capture_at: Optional[str] = None
    event_id: Optional[str] = None
    vehicle_id: Optional[int] = None
    message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "Detection":
        """Buat Detection dari sqlite3.Row."""
        return cls(
            id=row["id"],
            detection_id=row["detection_id"],
            direction=row["direction"],
            status=row["status"],
            rfid_uid=row["rfid_uid"],
            capture_at=row["capture_at"],
            event_id=row["event_id"],
            vehicle_id=row["vehicle_id"],
            message=row["message"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def to_dict(self) -> dict:
        return {
            "detection_id": self.detection_id,
            "direction": self.direction,
            "status": self.status,
            "rfid_uid": self.rfid_uid,
            "capture_at": self.capture_at,
            "event_id": self.event_id,
            "message": self.message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

