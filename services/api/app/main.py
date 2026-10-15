from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import AuditEvent, Evaluation, Order, ReturnCase
from app.refund_domain import ReturnRequest
from app.refund_engine import evaluate_return
from app.schemas.returns import (
    ReturnEvaluationRequest,
    ReturnEvaluationResponse,
)

app = FastAPI(
    title="ReturnGuard API",
    description="Governed e-commerce return and refund review system",
    version="0.3.0",
)


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "returnguard-api"}


@app.post(
    "/returns/evaluate",
    response_model=ReturnEvaluationResponse,
    tags=["Returns"],
)
async def evaluate_return_endpoint(
    payload: ReturnEvaluationRequest,
    session: AsyncSession = Depends(get_session),
) -> ReturnEvaluationResponse:

    # Keep the existing domain engine as the decision authority.
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

    # Save the request, evaluation and audit event atomically.
    # If any write fails, the entire transaction is rolled back.
    async with session.begin():
        existing_case = await session.get(
            ReturnCase, payload.case_id
        )

        if existing_case is not None:
            raise HTTPException(
                status_code=409,
                detail="A return case with this case_id already exists",
            )

        order = await session.get(Order, payload.order_id)

        if order is None:
            order = Order(
                order_id=payload.order_id,
                order_amount=payload.order_amount,
                delivery_status=payload.delivery_status,
            )
            session.add(order)
            await session.flush()
        elif order.order_amount != payload.order_amount:
            raise HTTPException(
                status_code=409,
                detail="The supplied order amount does not match the stored order",
            )

        return_case = ReturnCase(
            case_id=payload.case_id,
            order_id=payload.order_id,
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
        session.add(return_case)
        await session.flush()

        evaluation = Evaluation(
            case_id=decision.case_id,
            outcome=decision.outcome.value,
            risk_level=decision.risk_level.value,
            reasons=list(decision.reasons),
            policy_version="demo-v1",
        )
        session.add(evaluation)

        audit_event = AuditEvent(
            case_id=decision.case_id,
            event_type="return_evaluated",
            actor="system",
            details={
                "outcome": decision.outcome.value,
                "risk_level": decision.risk_level.value,
                "policy_version": "demo-v1",
            },
        )
        session.add(audit_event)

    # The transaction has committed before we return the response.
    return ReturnEvaluationResponse(
        case_id=decision.case_id,
        outcome=decision.outcome.value,
        risk_level=decision.risk_level.value,
        reasons=list(decision.reasons),
    )