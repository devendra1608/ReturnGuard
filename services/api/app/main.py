from fastapi import FastAPI
from app.refund_domain import ReturnRequest
from app.refund_engine import evaluate_return
from app.schemas.returns import (
  ReturnEvaluationRequest,
  ReturnEvaluationResponse
)

app = FastAPI(
  title="ReturnGuard API",
  description="Governed e-commerce return and refund review system",
  version="0.2.0",
)

@app.get("/health",tags=["Health"])
async def health_check() -> dict[str,str]:
  """Report whether the API process is responding"""
  return {
    "status" : "ok",
    "service" : "returnguard-api",
  }

@app.post(
    "/returns/evaluate",
    response_model=ReturnEvaluationResponse,
    tags=["Returns"],
)
async def evaluate_return_endpoint(
    payload: ReturnEvaluationRequest,
) -> ReturnEvaluationResponse:
    request = ReturnRequest(
        case_id=payload.case_id,
        order_id=payload.order_id,
        order_amount=payload.order_amount,
        refund_amount=payload.refund_amount,
        days_since_delivery=payload.days_since_delivery,
        return_window_days=payload.return_window_days,
        evidence_required=payload.evidence_required,
        evidence_available=payload.evidence_available,
        duplicate_request=payload.duplicate_request,
        previous_returns_90d=payload.previous_returns_90d,
        delivery_status=payload.delivery_status,
        evidence_consistent=payload.evidence_consistent,
    )

    decision = evaluate_return(request)

    return ReturnEvaluationResponse(
       case_id=decision.case_id,
       outcome=decision.outcome.value,
       risk_level=decision.risk_level.value,
       reasons=list(decision.reasons),
    )