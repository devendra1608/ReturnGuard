from decimal import Decimal
from app.refund_domain import (
  RefundDecision,
  RefundOutcome,
  ReturnRequest,
  RiskLevel
)

def evaluate_return(request: ReturnRequest)-> RefundDecision:
  """Evaluate a return using deterministic demonstration rules"""

  reasons: list[str] = []
  risk = RiskLevel.LOW

  #Validate data before making a policy decision
  if not request.case_id or not request.order_id:
    raise ValueError("Case ID and order ID are required")

  if request.order_amount <= Decimal("0"):
    raise ValueError("Order amount must be positive")

  if request.refund_amount <= Decimal("0"):
    raise ValueError("Refund amount must be positive")

  if request.refund_amount > request.order_amount:
    raise ValueError("Refund amount cannot exceed order amount")

  if request.days_since_delivery < 0:
    raise ValueError("Days since delivery cannot be negative")

  if request.return_window_days < 0:
    raise ValueError("Return window days cannot be negative")

  if request.previous_returns_90d < 0:
    raise ValueError("Previous return count cannot be negative")

  #Incomplete delivery data should not be treated as proof that return is fraudulent or ineligible
  if request.delivery_status != "delivered":
    return RefundDecision(
      case_id=request.case_id,
      outcome=RefundOutcome.HUMAN_REVIEW,
      risk_level=RiskLevel.MEDIUM,
      reasons=("Delivery status requires verification",),
    )

  # Missing evidence should prompt information gathering first.
  if request.evidence_required and not request.evidence_available:
    return RefundDecision(
      case_id=request.case_id,
      outcome=RefundOutcome.REQUEST_INFORMATION,
      risk_level=RiskLevel.LOW,
      reasons=("Required evidence is missing",),
    )

  # Contradictions and duplicates requires investigation
  if not request.evidence_consistent:
    reasons.append("Evidence conflicts with the return claim")
    risk = RiskLevel.HIGH

  if request.duplicate_request:
    reasons.append("Duplicate return request detected")
    risk = RiskLevel.HIGH

  if risk == RiskLevel.HIGH:
    return RefundDecision(
      case_id=request.case_id,
      outcome=RefundOutcome.HUMAN_REVIEW,
      risk_level=risk,
      reasons=tuple(reasons),
    ) 

  # the fictional demonstration policy uses a configurable return window supplied with each request
  if request.days_since_delivery > request.return_window_days:
    return RefundDecision(
      case_id=request.case_id,
      outcome=RefundOutcome.INELIGIBLE,
      risk_level=RiskLevel.LOW,
      reasons=("Return window has expired",),
    )

  # Illustrative thresholds, to be moved into configuration
  if request.refund_amount > Decimal("10000"):
    return RefundDecision(
      case_id=request.case_id,
      outcome=RefundOutcome.HUMAN_REVIEW,
      risk_level=RiskLevel.MEDIUM,
      reasons=("Refund amount exceeds the auto-approval limit",),
    )

  if request.previous_returns_90d >= 8:
    return RefundDecision(
      case_id=request.case_id,
      outcome=RefundOutcome.HUMAN_REVIEW,
      risk_level=RiskLevel.MEDIUM,
      reasons=("Return frequency requires review",),
    )

  return RefundDecision(
    case_id=request.case_id,
    outcome=RefundOutcome.AUTO_APPROVE,
    risk_level=RiskLevel.LOW,
    reasons=("Return satisfies demonstration policy",),
  )   
  