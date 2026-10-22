from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

class ReturnEvaluationRequest(BaseModel):
  """Validated input for evaluating a return request."""
  model_config = ConfigDict(extra="forbid")

  case_id: str = Field(min_length=1,max_length=64)
  order_id: str = Field(min_length=1,max_length=64)

  order_amount: Decimal = Field(gt=0,max_digits=12,decimal_places=2)
  refund_amount: Decimal = Field(gt = 0, max_digits=12, decimal_places=2)

  days_since_delivery: int = Field(ge=0, le=3650)
  return_window_days: int = Field(ge=0,le=3650)

  evidence_required: bool
  evidence_available: bool
  duplicate_request: bool

  previous_returns_90d: int = Field(ge=0,le=1000)

  delivery_status: Literal[
    "delivered",
    "in_transit",
    "cancelled",
    "unknown",
  ]

  evidence_consistent: bool

  @model_validator(mode="after")
  def validate_refund_amount(self):
    if self.refund_amount > self.order_amount:
      raise ValueError(
        "refund amount cannot exceed order_amount"
      )
    return self


class ReturnEvaluationResponse(BaseModel):
  """Structured result of deterministic evaluation"""

  case_id: str
  outcome: str
  risk_level: str
  reasons: list[str]

class EvaluationHistoryItem(BaseModel):
    case_id: str
    outcome: str
    risk_level: str
    reasons: list[str]
    policy_version: str


class ReturnCaseDetail(BaseModel):
    case_id: str
    order_id: str
    refund_amount: Decimal
    days_since_delivery: int
    return_window_days: int
    evidence_required: bool
    evidence_available: bool
    duplicate_request: bool
    previous_returns_90d: int
    delivery_status: str
    evidence_consistent: bool
    evaluation: EvaluationHistoryItem

class ReturnReviewRequest(BaseModel):
   model_config = ConfigDict(extra="forbid")

   decision: Literal["approve","reject"]
   reason: str = Field(min_length=1,max_length=2000)

   @field_validator("reason")
   @classmethod
   def reason_must_not_be_blank(cls,value: str) -> str:
      if not value.strip():
         raise ValueError("Review reason cannot be blank")
      return value.strip()