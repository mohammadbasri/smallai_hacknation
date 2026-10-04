import os
import tempfile

# Throwaway database for the whole test session; must be set before app modules import settings.
os.environ["DB_PATH"] = os.path.join(tempfile.mkdtemp(), "test.db")
os.environ["SMS_PROVIDER"] = "console"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402
from app.services import store  # noqa: E402

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    store.reset_for_tests()
    yield


def test_health_lists_models():
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["sector"] == "tourism"
    assert any(m.startswith("intent@") for m in body["models"])


# --------------------------------------------------------------------------- enquiries / guardrails
def test_price_enquiry_in_english_gets_fixed_reply_and_swahili_summary():
    r = client.post("/api/inference/enquiry", json={"text": "Hi! How much is the coffee farm tour for 2 adults?", "operator_language": "sw"})
    assert r.status_code == 200
    a = r.json()
    assert a["language"] == "en"
    assert a["decision"] == "answer"
    assert a["intent"] == "price"
    assert a["confidence"] >= 0.65
    assert "USD" in a["reply_for_visitor"]  # slot from profile rendered
    assert "bei" in a["operator_summary"].lower()  # Noor reads Kiswahili
    assert a["reply_for_operator"].startswith("Habari")


def test_swahili_booking_enquiry_is_detected_in_swahili():
    r = client.post("/api/inference/enquiry", json={"text": "Ningependa kuweka nafasi ya ziara kwa watu 4 siku ya Jumamosi"})
    a = r.json()
    assert a["language"] == "sw"
    assert a["intent"] in ("booking", "availability")  # both lead to the same human step: Noor confirms the date
    assert a["reply_for_visitor"].startswith("Asante") or a["reply_for_visitor"].startswith("Tunapokea")


def test_french_enquiry_answered_in_french():
    r = client.post("/api/inference/enquiry", json={"text": "Bonjour, combien coûte la visite pour deux adultes ?"})
    a = r.json()
    assert a["language"] == "fr"
    if a["decision"] == "answer":
        assert "Bonjour" in a["reply_for_visitor"] or "Merci" in a["reply_for_visitor"]


def test_unsupported_language_is_flagged_not_guessed():
    r = client.post("/api/inference/enquiry", json={"text": "Wie viel kostet die Kaffeetour für vier Personen am Samstag?"})
    a = r.json()
    assert a["language_supported"] is False
    assert a["decision"] == "ask_a_person"
    assert "English, French or Kiswahili" in a["reply_for_visitor"]


def test_nonsense_defers_to_a_person():
    r = client.post("/api/inference/enquiry", json={"text": "asdf qwer zxcv lorem"})
    a = r.json()
    assert a["decision"] == "ask_a_person"
    assert a["intent"] is None
    assert a["reply_for_visitor"] is None
    assert a["holding_reply"]  # the safe fallback is always available


def test_other_intent_is_never_auto_answered():
    r = client.post("/api/inference/enquiry", json={"text": "Is this the number for the clinic?"})
    a = r.json()
    assert a["decision"] == "ask_a_person"


def test_fixed_label_lists_are_published():
    r = client.get("/api/inference/labels/intent")
    assert r.status_code == 200
    assert "price" in r.json()["labels"] and "other" in r.json()["labels"]
    assert client.get("/api/inference/labels/nope").status_code == 404
    replies = client.get("/api/inference/replies").json()
    assert set(replies["intents"]["price"].keys()) == {"en", "fr", "sw"}


def test_models_endpoint_reports_size_and_metrics():
    body = client.get("/api/inference/models").json()
    names = {m["name"] for m in body["models"]}
    assert names == {"intent", "langid", "aspect", "sentiment"}
    total = sum(m["size_bytes"] for m in body["models"])
    assert total < 4 * 1024 * 1024  # side-loadable: under 4 MB uncompressed
    assert all("accuracy" in m["metrics_holdout"] for m in body["models"])


# --------------------------------------------------------------------------- human in the loop
def test_enquiry_action_requires_operator_decision_and_logs_sms():
    created = client.post("/api/enquiries", json={"text": "How much is the tour?", "visitor_contact": "+15550001", "source": "sms"}).json()
    assert created["analysis"]["decision"] == "answer"
    eid = created["id"]
    listed = client.get("/api/enquiries").json()["enquiries"]
    assert listed[0]["status"] == "new"  # nothing sent yet

    r = client.post(f"/api/enquiries/{eid}/action", json={"action": "send_standard"})
    assert r.status_code == 200
    assert r.json()["status"] == "handled"
    out = client.get("/api/sms/outbox").json()["messages"]
    assert out[0]["direction"] == "out" and out[0]["counterpart"] == "+15550001"


def test_custom_reply_requires_text():
    eid = client.post("/api/enquiries", json={"text": "asdf qwer"}).json()["id"]
    assert client.post(f"/api/enquiries/{eid}/action", json={"action": "send_custom"}).status_code == 400
    assert client.post(f"/api/enquiries/{eid}/action", json={"action": "send_standard"}).status_code == 400  # no standard reply when unsure


# --------------------------------------------------------------------------- SMS channel (basic phone)
def test_sms_roundtrip_africastalking_form_then_operator_presses_1():
    r = client.post("/api/sms/inbound", data={"from": "+447700900123", "to": "+000000000001", "text": "How much is the coffee tour for 3?"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] and body["analysis"]["intent"] == "price"
    assert body["operator_sms"]["text"].startswith("KARIBU")
    assert "bei" in body["operator_sms"]["text"].lower()  # notification to Noor is in Kiswahili

    r = client.post("/api/sms/operator", data={"From": "+000000000000", "Body": "1"})
    body = r.json()
    assert body["ok"] and body["operator_action"] == "send_standard"
    assert "USD" in body["sent_text"]
    outbox = client.get("/api/sms/outbox").json()["messages"]
    to_visitor = [m for m in outbox if m["direction"] == "out" and m["counterpart"] == "+447700900123"]
    assert len(to_visitor) == 1


def test_sms_operator_free_text_goes_to_visitor_verbatim():
    client.post("/api/sms/inbound", json={"from": "+33600000000", "text": "zzz unclear"})
    r = client.post("/api/sms/operator", json={"from": "+000000000000", "text": "Karibu! Please call me at 10."})
    assert r.json()["operator_action"] == "send_custom"
    assert r.json()["sent_text"] == "Karibu! Please call me at 10."


def test_sms_operator_with_nothing_pending():
    r = client.post("/api/sms/operator", json={"from": "+000000000000", "text": "1"})
    assert r.json()["ok"] is False


# --------------------------------------------------------------------------- feedback
def test_feedback_is_split_into_clauses_and_summarised():
    text = ("The coffee tasting was the highlight of our trip. The walk was beautiful but the road was terrible, "
            "you need a 4x4. Lunch was delicious.")
    r = client.post("/api/feedback", json={"text": text, "source": "paste"})
    assert r.status_code == 200
    a = r.json()
    assert a["language"] == "en"
    assert len(a["clauses"]) >= 4
    for c in a["clauses"]:
        assert c["aspect_decision"] in ("answer", "ask_a_person")
        if c["aspect_decision"] == "ask_a_person":
            assert c["aspect"] is None
    s = client.get("/api/feedback/summary").json()
    assert s["n_reviews"] == 1
    assert s["n_confident"] + s["n_unsure"] == s["n_clauses"]
    assert len(s["aspects"]) == 8  # 'other' is excluded from the operator summary


# --------------------------------------------------------------------------- bookings
def test_booking_lifecycle_and_fixed_messages():
    b = client.post("/api/bookings", json={"visitor_name": "Anna", "visitor_contact": "+4915000", "language": "fr",
                                            "date": "2026-10-18", "time": "09:00", "party_size": 3}).json()
    assert b["status"] == "pending"
    msg = client.get(f"/api/bookings/{b['id']}/message", params={"kind": "booking_confirmed"}).json()
    assert "2026-10-18" in msg["text"] and msg["language"] == "fr" and "confirmée" in msg["text"]
    p = client.patch(f"/api/bookings/{b['id']}", json={"status": "confirmed"}).json()
    assert p["status"] == "confirmed"
    sent = client.post(f"/api/bookings/{b['id']}/send", params={"kind": "booking_confirmed"}).json()
    assert sent["delivery"]["direction"] == "out"
    assert client.get("/api/bookings", params={"status": "confirmed"}).json()[0]["id"] == b["id"]


# --------------------------------------------------------------------------- profile / listing
def test_profile_roundtrip_changes_replies_and_listing():
    p = client.get("/api/profile").json()
    p["price_adult"] = "20"
    p["farm_name"] = "Test Farm"
    assert client.put("/api/profile", json=p).status_code == 200
    a = client.post("/api/inference/enquiry", json={"text": "How much is the tour?"}).json()
    assert "20 USD" in a["reply_for_visitor"] and "Test Farm" in a["reply_for_visitor"]
    listing = client.get("/api/profile/listing", params={"lang": "sw"}).json()["text"]
    assert listing.startswith("Test Farm")


# --------------------------------------------------------------------------- sync
def test_sync_is_idempotent_and_applies_records():
    payload = {
        "client_id": "device-1",
        "records": [
            {"id": "b-1", "kind": "booking", "captured_at": "2026-10-03T10:00:00Z", "language": "en",
             "payload": {"date": "2026-10-20", "time": "14:00", "party_size": 2, "visitor_name": "Tom", "status": "pending"}},
            {"id": "e-1", "kind": "enquiry", "captured_at": "2026-10-03T10:01:00Z", "language": "en",
             "payload": {"text": "Where is the farm?", "language": "en", "intent": "directions", "confidence": 0.8, "decision": "answer"}},
            {"id": "bad-1", "kind": "feedback", "captured_at": "2026-10-03T10:02:00Z", "language": "en", "payload": {}},
        ],
    }
    r1 = client.post("/api/sync", json=payload).json()
    assert set(r1["accepted"]) == {"b-1", "e-1"}
    assert "bad-1" in r1["rejected"]  # missing text: stays on the phone with a reason
    r2 = client.post("/api/sync", json=payload).json()
    assert set(r2["accepted"]) == {"b-1", "e-1"}
    assert client.get("/api/sync").json()["count"] == 2
    assert client.get("/api/bookings").json()[0]["visitor_name"] == "Tom"
    assert client.get("/api/enquiries").json()["enquiries"][0]["intent"] == "directions"


# --------------------------------------------------------------------------- datasets
def test_datasets_declare_coverage_gaps_in_both_layers():
    ds = client.get("/api/datasets").json()
    kinds = {d["kind"] for d in ds}
    assert {"problem_evidence", "build_data"} <= kinds
    assert all(d["coverage_gaps"] for d in ds)
