import os

os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-12")
os.environ["PROVIDER"] = "mock"
os.environ["RATE_LIMIT_PER_MIN"] = "5"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from triageforge.main import app  # noqa: E402
from triageforge.redaction import redact  # noqa: E402

TICKET = {"text": "I was charged twice, this is unacceptable. Mail me at jane@x.com ASAP"}


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def auth(client, user="alice"):
    client.post("/v1/auth/register", json={"username": user, "password": "supersecret1"})
    r = client.post("/v1/auth/token", data={"username": user, "password": "supersecret1"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_requires_jwt(client):
    assert client.post("/v2/triage", json=TICKET).status_code == 401
    bad = {"Authorization": "Bearer nope"}
    assert client.post("/v2/triage", json=TICKET, headers=bad).status_code == 401


def test_bad_login(client):
    auth(client, "bob")
    r = client.post("/v1/auth/token", data={"username": "bob", "password": "wrongwrong"})
    assert r.status_code == 401


def test_v2_happy_path_and_pii(client):
    r = client.post("/v2/triage", json=TICKET, headers=auth(client, "carol"))
    assert r.status_code == 200
    d = r.json()
    assert d["category"] == "billing" and d["priority"] == "urgent"
    assert d["assigned_queue"] == "billing_ops"
    assert d["sla_hours"] >= 1
    assert d["sla_due_at"]
    assert d["rationale"] and d["internal_note"]
    assert 1 <= d["severity_score"] <= 10
    assert d["next_actions"] and d["keywords"]
    assert d["pii_redacted"] == {"email": 1}
    assert 0 <= d["confidence"] <= 1


def test_v1_is_subset(client):
    r = client.post("/v1/triage", json=TICKET, headers=auth(client, "dave"))
    assert r.status_code == 200
    assert "suggested_reply" not in r.json()
    assert "assigned_queue" not in r.json()


def test_taxonomy_public(client):
    r = client.get("/v1/taxonomy")
    assert r.status_code == 200
    body = r.json()
    assert "billing" in body["categories"] and "security" in body["categories"]
    assert "billing_ops" in body["queues"]
    assert "empathetic" in body["reply_tones"]


def test_security_and_shipping_categories(client):
    h = auth(client, "gina")
    sec = client.post(
        "/v2/triage",
        json={
            "text": "Unauthorized login attempt looks like a breach on my account",
            "channel": "email",
        },
        headers=h,
    ).json()
    assert sec["category"] == "security" and sec["assigned_queue"] == "trust_safety"
    ship = client.post(
        "/v2/triage",
        json={
            "text": "Shipping delivery tracking stuck, need replacement ASAP",
            "channel": "chat",
        },
        headers=h,
    ).json()
    assert ship["category"] == "shipping" and ship["assigned_queue"] == "logistics"


def test_analyst_category_priority_and_not_urgent(client):
    h = auth(client, "helen")
    feature = client.post(
        "/v2/triage",
        json={
            "category": "feature_request",
            "priority": "low",
            "text": "It would be great to export CSV. Not urgent, just a suggestion.",
        },
        headers=h,
    ).json()
    assert feature["category"] == "feature_request"
    assert feature["priority"] == "low"
    assert feature["severity_score"] == 2
    assert feature["assigned_queue"] == "success"
    assert feature["suggested_reply"]


def test_validation_rejects_bad_input(client):
    h = auth(client, "erin")
    assert client.post("/v2/triage", json={"text": "short"}, headers=h).status_code == 422
    extra = {**TICKET, "hack": 1}
    assert client.post("/v2/triage", json=extra, headers=h).status_code == 422


def test_rate_limit_and_usage(client):
    h = auth(client, "frank")
    codes = [client.post("/v2/triage", json=TICKET, headers=h).status_code for _ in range(7)]
    assert codes.count(200) == 5 and codes[-1] == 429


def test_redaction():
    out, c = redact("call +1 415 555 2671 card 4242 4242 4242 4242 a@b.io")
    assert "[PHONE]" in out and "[CARD]" in out and "[EMAIL]" in out and len(c) == 3


def test_health(client):
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").json()["provider"] == "mock"


def test_console_served(client):
    r = client.get("/")
    assert r.status_code == 200 and "TriageForge" in r.text


def test_suggest_and_feedback(client):
    h = auth(client, "ivy")
    s = client.post(
        "/v2/suggest",
        json={"text": "Please refund my last invoice, charged twice by mistake"},
        headers=h,
    )
    assert s.status_code == 200
    body = s.json()
    assert body["category"] in {"billing", "refund"}
    assert body["priority"] in {"low", "medium", "high", "urgent"}
    assert body["rationale"]

    triaged = client.post(
        "/v2/triage",
        json={
            "text": TICKET["text"],
            "reply_tone": "brief",
            "category": "billing",
            "priority": "high",
        },
        headers=h,
    ).json()
    assert triaged["reply_tone"] == "brief"
    assert "Got it" in triaged["suggested_reply"] or len(triaged["suggested_reply"]) > 10

    fb = client.post(
        "/v1/feedback",
        json={"ticket_id": triaged["ticket_id"], "helpful": True, "note": "solid routing"},
        headers=h,
    )
    assert fb.status_code == 200 and fb.json()["stored"] is True


def test_history_sidebar_and_dashboard(client):
    h = auth(client, "jade")
    t1 = client.post(
        "/v2/triage",
        json={"text": TICKET["text"], "category": "billing", "priority": "urgent"},
        headers=h,
    ).json()
    client.post(
        "/v2/triage",
        json={
            "text": "Export CSV would be great. Not urgent, just a suggestion.",
            "category": "feature_request",
            "priority": "low",
        },
        headers=h,
    )
    hist = client.get("/v1/history", headers=h)
    assert hist.status_code == 200 and len(hist.json()) == 2
    detail = client.get(f"/v1/history/{t1['ticket_id']}", headers=h)
    assert detail.status_code == 200
    assert detail.json()["result"]["ticket_id"] == t1["ticket_id"]
    pinned = client.post(f"/v1/history/{t1['ticket_id']}/pin", headers=h)
    assert pinned.status_code == 200 and pinned.json()["pinned"] is True
    dash = client.get("/v1/dashboard", headers=h).json()
    assert dash["total_tickets"] == 2
    assert dash["by_category"]["billing"] == 1
    assert dash["pinned"] == 1
