import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app.api.server import app


client = TestClient(app)


def test_create_session_base():
    r = client.post("/sessions", json={"mode": "base"})
    assert r.status_code == 200
    data = r.json()
    assert "session_id" in data
    sid = data["session_id"]
    r2 = client.post(f"/sessions/{sid}/messages", json={"content": "你好", "mode": "base"})
    assert r2.status_code == 200
    info = client.get(f"/sessions/{sid}", params={"mode": "base"}).json()
    assert info["session_id"] == sid
    assert info["integrity"] is True


def test_financial_risk_profile_and_message():
    r = client.post("/sessions", json={"mode": "financial"})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    r2 = client.post(f"/sessions/{sid}/risk_profile", json={"risk_level": "medium", "factors": {"age": 30}})
    assert r2.status_code == 200
    r3 = client.post(f"/sessions/{sid}/messages", json={"content": "我想投资", "mode": "financial"})
    assert r3.status_code == 200
    audit = client.get(f"/audit/{sid}", params={"mode": "financial"}).json()
    assert "records" in audit
    assert audit["integrity"] is True
