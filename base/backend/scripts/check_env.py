"""Script kiểm tra môi trường khởi tạo Base Code FastAPI + MySQL + CRUD mẫu."""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app


def verify_base_environment():
    client = TestClient(app)
    h = client.get("/api/health")
    assert h.status_code == 200, f"Health check failed: {h.text}"
    data = h.json()
    assert data.get("database") == "connected", f"MySQL not connected: {data}"

    items_res = client.get("/api/items")
    assert items_res.status_code == 200, f"Items API failed: {items_res.text}"
    print(f"[OK] Base code verified: {data.get('mysql_display', 'MySQL: connected')} | Items count: {len(items_res.json())}")


if __name__ == "__main__":
    verify_base_environment()
