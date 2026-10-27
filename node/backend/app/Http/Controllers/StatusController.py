"""
Controller status perangkat — Pos Satpam.
Update & baca status kamera dan relay.
"""
from datetime import datetime

from app.database import get_db
from app.Models.DeviceStatus import DeviceStatus
from app.Services.CameraService import check_camera_alive
from app.Services.RadarService import radar_service


def get_status() -> dict:
    """GET /api/status — status perangkat saat ini."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM device_status WHERE id = 1").fetchone()
    status = DeviceStatus.from_row(row).to_dict() if row else DeviceStatus().to_dict()
    status["radar"] = radar_service.status()
    return status


def update_camera_status(direction: str, active: bool):
    """Update status kamera di database."""
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        if direction == "masuk":
            conn.execute(
                "UPDATE device_status SET camera_in_active = ?, last_camera_in_at = ?, updated_at = ? WHERE id = 1",
                (int(active), now, now),
            )
        elif direction == "keluar":
            conn.execute(
                "UPDATE device_status SET camera_out_active = ?, last_camera_out_at = ?, updated_at = ? WHERE id = 1",
                (int(active), now, now),
            )


def refresh_camera_status():
    """Cek kamera dan update status. Dipanggil secara periodik."""
    for direction in ("masuk", "keluar"):
        alive = check_camera_alive(direction)
        update_camera_status(direction, alive)
