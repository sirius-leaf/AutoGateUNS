"""
Request/Response models untuk deteksi radar — Pos Satpam.
"""
from typing import Optional, List
from pydantic import BaseModel
from app.Http.Requests.VehicleRequest import VehicleOut


class DetectionRfidRequest(BaseModel):
    """Body untuk POST /api/detections/{detection_id}/rfid."""
    rfid_uid: Optional[str] = None


class DetectionOut(BaseModel):
    detection_id: str
    direction: str
    status: str
    rfid_uid: Optional[str] = None
    capture_at: Optional[str] = None
    capture_in_seconds: Optional[int] = None
    event_id: Optional[str] = None
    message: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    vehicle: Optional[VehicleOut] = None


class DetectionListOut(BaseModel):
    items: List[DetectionOut] = []

