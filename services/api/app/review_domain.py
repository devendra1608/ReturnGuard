from enum import Enum
from app.refund_domain import RefundOutcome

class CaseStatus(str,Enum):
  PENDING_REVIEW = "pending_review"
  INFORMATION_REQUESTED = "information_requested"
  AUTO_APPROVED = "auto_approved"
  APPROVED = "approved"
  REJECTED = "rejected"
  INELIGIBLE = "ineligible"

class ReviewDecision(str,Enum):
  APPROVE = "approve"
  REJECT = "reject"


def initial_case_status(outcome: RefundOutcome) -> CaseStatus:
  """Map an evaluation outcome to the initial lifecycle status."""
  mapping = {
    RefundOutcome.AUTO_APPROVE: CaseStatus.AUTO_APPROVED,
    RefundOutcome.HUMAN_REVIEW: CaseStatus.PENDING_REVIEW,
    RefundOutcome.REQUEST_INFORMATION: CaseStatus.INFORMATION_REQUESTED,
    RefundOutcome.INELIGIBLE : CaseStatus.INELIGIBLE,
  }

  return mapping[outcome]

def apply_review(
    current_status: CaseStatus,
    decision: ReviewDecision,
    reason: str,
)-> CaseStatus:
  """Apply a human review decision to a case awaiting review."""
  if current_status != CaseStatus.PENDING_REVIEW:
    raise ValueError("Only cases pending review can be approved or rejected")

  if not reason.strip():
    raise ValueError("A non-empty review reason is required")

  if decision == ReviewDecision.APPROVE:
    return CaseStatus.APPROVED

  if decision == ReviewDecision.REJECT:
    return CaseStatus.REJECTED

  raise ValueError("Unsupported review decision")