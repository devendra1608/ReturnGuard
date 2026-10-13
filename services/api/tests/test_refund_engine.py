
from dataclasses import replace
from decimal import Decimal

import pytest

from app.refund_domain import RefundOutcome, RiskLevel, ReturnRequest
from app.refund_engine import evaluate_return


@pytest.fixture
def valid_request() -> ReturnRequest:
    return ReturnRequest(
        case_id="RET-000001",
        order_id="ORD-000001",
        order_amount=Decimal("1500.00"),
        refund_amount=Decimal("1500.00"),
        days_since_delivery=5,
        return_window_days=30,
        evidence_required=False,
        evidence_available=True,
        duplicate_request=False,
        previous_returns_90d=1,
        delivery_status="delivered",
        evidence_consistent=True,
    )


def test_eligible_return_is_auto_approved(valid_request):
    decision = evaluate_return(valid_request)

    assert decision.outcome == RefundOutcome.AUTO_APPROVE
    assert decision.risk_level == RiskLevel.LOW


def test_expired_return_is_ineligible(valid_request):
    request = replace(valid_request, days_since_delivery=45)

    decision = evaluate_return(request)

    assert decision.outcome == RefundOutcome.INELIGIBLE


def test_duplicate_request_requires_review(valid_request):
    request = replace(valid_request, duplicate_request=True)

    decision = evaluate_return(request)

    assert decision.outcome == RefundOutcome.HUMAN_REVIEW
    assert decision.risk_level == RiskLevel.HIGH


def test_missing_required_evidence_requests_information(valid_request):
    request = replace(
        valid_request,
        evidence_required=True,
        evidence_available=False,
    )

    decision = evaluate_return(request)

    assert decision.outcome == RefundOutcome.REQUEST_INFORMATION


def test_contradictory_evidence_requires_review(valid_request):
    request = replace(valid_request, evidence_consistent=False)

    decision = evaluate_return(request)

    assert decision.outcome == RefundOutcome.HUMAN_REVIEW


def test_high_value_return_requires_review(valid_request):
    request = replace(
        valid_request,
        order_amount=Decimal("15000.00"),
        refund_amount=Decimal("15000.00"),
    )

    decision = evaluate_return(request)

    assert decision.outcome == RefundOutcome.HUMAN_REVIEW


def test_refund_cannot_exceed_order_amount(valid_request):
    request = replace(
        valid_request,
        refund_amount=Decimal("2000.00"),
    )

    with pytest.raises(ValueError):
        evaluate_return(request)
