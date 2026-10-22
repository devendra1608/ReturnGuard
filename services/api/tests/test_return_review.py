import asyncio
from sqlalchemy import select

from app.main import app
from app.models import AuditEvent,Evaluation,ReviewRecord,ReturnCase

def pending_review_payload()-> dict:
  """Create a return request that should require human review."""
  return{
    "case_id": "review-case-001",
    "order_id": "review-order-001",
    "order_amount": "2500.00",
    "refund_amount": "500.00",
    "days_since_delivery": 3,
    "return_window_days": 30,
    "evidence_required": False,
    "evidence_available": True,
    "duplicate_request": False,
    "previous_returns_90d":0,
    "delivery_status": "delivered",
    "evidence_consistent": False,
  }

def create_pending_case(client):
  response = client.post(
    "/returns/evaluate",
    json=pending_review_payload(),
  )
  assert response.status_code == 200
  assert response.json()["outcome"] == "human_review"

def test_reviewer_can_approve_pending_case(client):
  create_pending_case(client)

  response = client.post(
    "/returns/review-case-001/review",
    json={
      "decision": "approve",
      "reason": "Evidence was veriied by the reviewer."
    },
  )

  assert response.status_code == 200
  assert response.json()["status"] == "approved"

def test_reviewer_can_reject_pending_case(client):
  create_pending_case(client)

  response = client.post(
    "/returns/review-case-001/review",
    json={
      "decision":"reject",
      "reason": "the submitted evidence does not support the claim.",
    },
  )

  assert response.status_code == 200
  assert response.json()["status"] == "rejected"

def test_review_persists_review_record_audit_event(client):
    create_pending_case(client)

    response = client.post(
        "/returns/review-case-001/review",
        json={
            "decision": "approve",
            "reason": "Order evidence verified.",
        },
    )
    assert response.status_code == 200

    async def read_records():
        factory = app.state.test_session_factory

        async with factory() as session:
            case = await session.get(
                ReturnCase, "review-case-001"
            )

            reviews = (
                await session.scalars(
                    select(ReviewRecord).where(
                        ReviewRecord.case_id == "review-case-001"
                    )
                )
            ).all()

            audits = (
                await session.scalars(
                    select(AuditEvent).where(
                        AuditEvent.case_id == "review-case-001"
                    )
                )
            ).all()

            return case.status, list(reviews), list(audits)

    status, reviews, audits = asyncio.run(read_records())

    # Verify the case status.
    assert status == "approved"

    # Verify the review record.
    assert len(reviews) == 1
    assert reviews[0].decision == "approve"
    assert reviews[0].reason == "Order evidence verified."
    assert reviews[0].reviewer_id

    # One audit event comes from evaluation,
    # and another comes from the review.
    assert len(audits) == 2

    review_audits = [
        event
        for event in audits
        if event.event_type == "return_reviewed"
    ]

    assert len(review_audits) == 1
    assert review_audits[0].actor == reviews[0].reviewer_id
    assert review_audits[0].details["decision"] == "approve"
    assert review_audits[0].details["new_status"] == "approved"


def test_review_of_unknown_case_returns_404(client):
  response = client.post(
    "/returns/does-not-exist/review",
    json={
      "decision":"approve",
      "reason": "Test review."
    }
  )
  assert response.status_code == 404


def test_review_cannot_be_submitted_twice(client):
  create_pending_case(client)

  first = client.post(
    "/returns/review-case-001/review",
    json={
      "decision":"approve",
      "reason":"Evidence verified.",
    },
  )

  second = client.post(
    "/returns/review-case-001/review",
    json={
      "decision":"reject",
      "reason": "Trying to change the previous decision.",
    },
  )

  assert first.status_code == 200
  assert second.status_code == 409

def test_invalid_review_decision_is_rejected(client):
  create_pending_case(client)

  response = client.post(
    "/returns/review-case-001/review",
    json={
      "decision":"maybe",
      "reason": "Unclear decision."
    },
  )

  assert response.status_code == 422

def test_empty_review_reason_is_rejected(client):
    create_pending_case(client)

    response = client.post(
        "/returns/review-case-001/review",
        json={
            "decision": "approve",
            "reason": "   ",
        },
    )

    assert response.status_code in (400, 422)
