import asyncio

from sqlalchemy import func, select

from app.main import app
from app.models import AuditEvent, Evaluation, Order, ReturnCase


def valid_payload() -> dict:
    return {
        "case_id": "case-db-001",
        "order_id": "order-db-001",
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


def test_evaluation_persists_all_records(client):
    response = client.post(
        "/returns/evaluate",
        json=valid_payload(),
    )

    assert response.status_code == 200
    assert response.json()["outcome"] == "auto_approve"

    async def read_counts():
        factory = app.state.test_session_factory

        async with factory() as session:
            return {
                "orders": await session.scalar(
                    select(func.count()).select_from(Order)
                ),
                "cases": await session.scalar(
                    select(func.count()).select_from(ReturnCase)
                ),
                "evaluations": await session.scalar(
                    select(func.count()).select_from(Evaluation)
                ),
                "audit": await session.scalar(
                    select(func.count()).select_from(AuditEvent)
                ),
            }

    counts = asyncio.run(read_counts())

    assert counts == {
        "orders": 1,
        "cases": 1,
        "evaluations": 1,
        "audit": 1,
    }


def test_duplicate_case_id_is_rejected(client):
    payload = valid_payload()

    first = client.post("/returns/evaluate", json=payload)
    second = client.post("/returns/evaluate", json=payload)

    assert first.status_code == 200
    assert second.status_code == 409
