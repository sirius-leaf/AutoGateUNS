"""
Controller deteksi radar — Pos Satpam.

Endpoint untuk frontend:
  - GET  /api/detections/pending          → daftar deteksi aktif
  - GET  /api/detections/{detection_id}   → status satu deteksi
  - POST /api/detections/{detection_id}/rfid → kirim RFID, trigger capture
  - POST /api/detections/trigger/{direction} → simulasi event radar (untuk testing)
"""
from typing import Optional
from fastapi import HTTPException, status

from app.Http.Requests.DetectionRequest import DetectionListOut, DetectionOut, DetectionRfidRequest
from app.Services.DetectionService import detection_service


def pending(direction: Optional[str] = None) -> DetectionListOut:
    """GET /api/detections/pending — deteksi yang masih menunggu RFID/capture."""
    items = detection_service.get_pending(direction=direction)
    return DetectionListOut(items=[DetectionOut(**item) for item in items])


async def trigger(direction: str) -> DetectionOut:
    """POST /api/detections/trigger/{direction} — simulasi event radar (untuk testing)."""
    if direction not in ("masuk", "keluar"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arah harus 'masuk' atau 'keluar'.",
        )
    detection = await detection_service.on_radar_detected(direction)
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Masih ada deteksi aktif untuk arah '{direction}'.",
        )
    return DetectionOut(**detection)


def show(detection_id: str) -> DetectionOut:
    """GET /api/detections/{detection_id} — status deteksi."""
    detection = detection_service.get(detection_id)
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deteksi '{detection_id}' tidak ditemukan.",
        )
    return DetectionOut(**detection)


async def submit_rfid(detection_id: str, payload: DetectionRfidRequest) -> DetectionOut:
    """POST /api/detections/{detection_id}/rfid — terima RFID lalu capture kamera."""
    detection = detection_service.get(detection_id)
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deteksi '{detection_id}' tidak ditemukan.",
        )

    if detection["status"] not in ("awaiting_rfid", "waiting_capture", "capturing", "captured"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detection.get("message") or "Deteksi sudah tidak aktif.",
        )

    result = await detection_service.submit_rfid(detection_id, payload.rfid_uid)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deteksi '{detection_id}' tidak ditemukan.",
        )
    return DetectionOut(**result)

