
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)

VALID_REQUEST = {
    "case_id": "RET-API-0001",
    "order_id": "ORD-API-0001",
    "order_amount": "1500.00",
    "refund_amount": "1500.00",
    "days_since_delivery": 5,
    "return_window_days": 30,
    "evidence_required": False,
    "evidence_available": True,
    "duplicate_request": False,
    "previous_returns_90d": 1,
    "delivery_status": "delivered",
    "evidence_consistent": True,
}


def test_evaluate_eligible_return():
    response = client.post(
        "/returns/evaluate",
        json=VALID_REQUEST,
    )

    assert response.status_code == 200

    data = response.json()
    assert data["case_id"] == "RET-API-0001"
    assert data["outcome"] == "auto_approve"
    assert data["risk_level"] == "low"
    assert len(data["reasons"]) > 0


def test_evaluate_duplicate_request():
    payload = {
        **VALID_REQUEST,
        "duplicate_request": True,
    }

    response = client.post("/returns/evaluate", json=payload)

    assert response.status_code == 200
    assert response.json()["outcome"] == "human_review"
    assert response.json()["risk_level"] == "high"


def test_reject_refund_above_order_amount():
    payload = {
        **VALID_REQUEST,
        "refund_amount": "2000.00",
    }

    response = client.post("/returns/evaluate", json=payload)

    assert response.status_code == 422


def test_reject_negative_days_since_delivery():
    payload = {
        **VALID_REQUEST,
        "days_since_delivery": -1,
    }

    response = client.post("/returns/evaluate", json=payload)

    assert response.status_code == 422


def test_reject_unexpected_fields():
    payload = {
        **VALID_REQUEST,
        "admin_override": True,
    }

    response = client.post("/returns/evaluate", json=payload)

    assert response.status_code == 422
