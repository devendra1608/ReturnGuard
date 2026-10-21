
import pytest

from app.refund_domain import RefundOutcome
from app.review_domain import (
    CaseStatus,
    ReviewDecision,
    apply_review,
    initial_case_status,
)


@pytest.mark.parametrize(
    ("outcome", "expected_status"),
    [
        (RefundOutcome.AUTO_APPROVE, CaseStatus.AUTO_APPROVED),
        (RefundOutcome.HUMAN_REVIEW, CaseStatus.PENDING_REVIEW),
        (
            RefundOutcome.REQUEST_INFORMATION,
            CaseStatus.INFORMATION_REQUESTED,
        ),
        (RefundOutcome.INELIGIBLE, CaseStatus.INELIGIBLE),
    ],
)
def test_initial_status_matches_evaluation(outcome, expected_status):
    assert initial_case_status(outcome) == expected_status


def test_pending_review_can_be_approved():
    status = apply_review(
        CaseStatus.PENDING_REVIEW,
        ReviewDecision.APPROVE,
        "Evidence reviewed and return conditions satisfied",
    )
    assert status == CaseStatus.APPROVED


def test_pending_review_can_be_rejected():
    status = apply_review(
        CaseStatus.PENDING_REVIEW,
        ReviewDecision.REJECT,
        "Evidence does not satisfy the return policy",
    )
    assert status == CaseStatus.REJECTED


@pytest.mark.parametrize("reason", ["", "   ", "\t"])
def test_review_requires_a_reason(reason):
    with pytest.raises(ValueError, match="reason"):
        apply_review(
            CaseStatus.PENDING_REVIEW,
            ReviewDecision.APPROVE,
            reason,
        )


@pytest.mark.parametrize(
    "status",
    [
        CaseStatus.INFORMATION_REQUESTED,
        CaseStatus.AUTO_APPROVED,
        CaseStatus.APPROVED,
        CaseStatus.REJECTED,
        CaseStatus.INELIGIBLE,
    ],
)
def test_only_pending_review_cases_can_be_reviewed(status):
    with pytest.raises(ValueError, match="pending review"):
        apply_review(
            status,
            ReviewDecision.APPROVE,
            "Review attempted",
        )
