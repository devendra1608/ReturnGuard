from dataclasses import dataclass
# dataclass provides a simple way to represent structured records
from decimal import Decimal
#Decimal represents monetary amounts more safely then binary floating point
from enum import Enum

class RiskLevel(str,Enum):
  LOW = "low"
  MEDIUM = "medium"
  HIGH = "high"

class RefundOutcome(str,Enum):
  AUTO_APPROVE = "auto_approve"
  HUMAN_REVIEW = "human_review"
  REQUEST_INFORMATION = "request_information"
  INELIGIBLE = "ineligible"

#frozen=True makes the objects immutable after construction,reducing accidental modification during evaluation
@dataclass(frozen=True)
class ReturnRequest:
  case_id: str
  order_id: str
  order_amount: Decimal
  refund_amount: Decimal
  days_since_delivery: int
  return_window_days: int
  evidence_required: bool
  evidence_available: bool
  duplicate_request: bool
  previous_returns_90d: int
  delivery_status: str
  evidence_consistent: bool

@dataclass(frozen=True)
class RefundDecision:
  case_id: str
  outcome: RefundOutcome
  risk_level : RiskLevel
  reasons: tuple[str, ...]  