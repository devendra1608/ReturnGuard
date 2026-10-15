
from app.models import Evaluation
from sqlalchemy import select
import asyncio


def valid_payload() -> dict:
    return {
        "case_id": "case-retrieval-001",
        "order_id": "order-retrieval-001",
        "order_amount": "2500.00",
        "refund_amount": "500.00",
        "days_since_delivery": 3,
        "return_window_days": 30,
        "evidence_required": False,
        "evidence_available": True,
        "duplicate_request": False,
        "previous_returns_90d": 0,
        "delivery_status": "delivered",
        "evidence_consistent": True,
    }


def test_get_existing_return_case(client):
    payload = valid_payload()
    created = client.post("/returns/evaluate", json=payload)
    assert created.status_code == 200

    response = client.get(
        f"/returns/{payload['case_id']}"
    )

    assert response.status_code == 200
    data = response.json()

    assert data["case_id"] == payload["case_id"]
    assert data["order_id"] == payload["order_id"]
    assert data["refund_amount"] == "500.00"
    assert data["evaluation"]["outcome"] == "auto_approve"
    assert data["evaluation"]["risk_level"] == "low"
    assert isinstance(data["evaluation"]["reasons"], list)


def test_get_unknown_return_case_returns_404(client):
    response = client.get("/returns/does-not-exist")

    assert response.status_code == 404


def test_get_evaluation_history(client):
    payload = valid_payload()
    created = client.post("/returns/evaluate", json=payload)
    assert created.status_code == 200

    response = client.get(
        f"/returns/{payload['case_id']}/evaluations"
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["case_id"] == payload["case_id"]
    assert data[0]["outcome"] == "auto_approve"
    assert data[0]["risk_level"] == "low"
    assert data[0]["policy_version"] == "demo-v1"


def test_evaluation_history_returns_404_for_unknown_case(client):
    response = client.get(
        "/returns/does-not-exist/evaluations"
    )

    assert response.status_code == 404
