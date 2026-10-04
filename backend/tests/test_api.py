from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_inference_confident_answer():
    r = client.post(
        "/api/inference",
        json={"sector": "tourism", "text": "I want to book a tour, how much", "language": "en"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "answer"
    assert body["label"] in {"booking_request", "price_enquiry"}
    assert body["confidence"] >= 0.65


def test_inference_defers_to_human_when_unsure():
    r = client.post(
        "/api/inference",
        json={"sector": "tourism", "text": "zzzz nothing matches", "language": "hi"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["decision"] == "ask_a_person"
    assert body["label"] is None
    assert "पक्का नहीं" in body["explanation"]  # Hindi fallback message


def test_sync_is_idempotent():
    payload = {
        "client_id": "device-1",
        "records": [
            {
                "id": "rec-1",
                "sector": "tourism",
                "payload": {"text": "hello"},
                "captured_at": "2026-10-03T10:00:00Z",
                "language": "en",
            }
        ],
    }
    r1 = client.post("/api/sync", json=payload)
    r2 = client.post("/api/sync", json=payload)
    assert r1.json()["accepted"] == ["rec-1"]
    assert r2.json()["accepted"] == ["rec-1"]
    assert client.get("/api/sync").json()["count"] == 1


def test_datasets_filter_includes_common():
    r = client.get("/api/datasets", params={"sector": "tourism"})
    sectors = {d["sector"] for d in r.json()}
    assert sectors <= {"tourism", "common"}
    assert "common" in sectors
