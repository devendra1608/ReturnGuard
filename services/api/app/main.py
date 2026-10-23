from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select,update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import AuditEvent, Evaluation, Order, ReturnCase, ReviewRecord
from app.refund_domain import ReturnRequest
from app.refund_engine import evaluate_return
from app.schemas.returns import (
    ReturnEvaluationRequest,
    ReturnEvaluationResponse,
    EvaluationHistoryItem,
    ReturnCaseDetail,
    ReturnReviewRequest
)
from app.review_domain import (
    initial_case_status,
    CaseStatus,
    ReviewDecision,
    apply_review,
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
            status=initial_case_status(decision.outcome).value,
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

@app.get("/returns/{case_id}/evaluations")
async def get_evaluation_history(
    case_id: str,
    session: AsyncSession = Depends(get_session),
) -> list[EvaluationHistoryItem]:
    return_case = await session.get(ReturnCase, case_id)

    if return_case is None:
        raise HTTPException(
            status_code=404,
            detail="Return case not found",
        )

    result = await session.scalars(
        select(Evaluation)
        .where(Evaluation.case_id == case_id)
        .order_by(Evaluation.created_at.desc(),Evaluation.evaluation_id.desc())
    )

    evaluations = result.all()

    return[
        EvaluationHistoryItem(
            case_id=evaluation.case_id,
            outcome=evaluation.outcome,
            risk_level=evaluation.risk_level,
            reasons=evaluation.reasons,
            policy_version=evaluation.policy_version,
        )
        for evaluation in evaluations
    ]

@app.get("/returns/{case_id}")
async def get_return_case(
    case_id: str,
    session: AsyncSession = Depends(get_session),
) -> ReturnCaseDetail:
    return_case = await session.get(ReturnCase, case_id)

    if return_case is None:
        raise HTTPException(
            status_code=404,
            detail="Return case not found",
        )

    latest_evaluation = await session.scalar(
        select(Evaluation)
        .where(Evaluation.case_id == case_id)
        .order_by(Evaluation.created_at.desc(), Evaluation.evaluation_id.desc())
        .limit(1)
    )

    if latest_evaluation is None:
        raise HTTPException(
            status_code=500,
            detail="Return case has no recorded evaluation",
        )

    return ReturnCaseDetail(
        case_id=return_case.case_id,
        order_id=return_case.order_id,
        refund_amount=return_case.refund_amount,
        days_since_delivery=return_case.days_since_delivery,
        return_window_days=return_case.return_window_days,
        evidence_required=return_case.evidence_required,
        evidence_available=return_case.evidence_available,
        duplicate_request=return_case.duplicate_request,
        previous_returns_90d=return_case.previous_returns_90d,
        delivery_status=return_case.delivery_status,
        evidence_consistent=return_case.evidence_consistent,
        evaluation=EvaluationHistoryItem(
            case_id=latest_evaluation.case_id,
            outcome=latest_evaluation.outcome,
            risk_level=latest_evaluation.risk_level,
            reasons=latest_evaluation.reasons,
            policy_version=latest_evaluation.policy_version,
        ),
    )

@app.post("/returns/{case_id}/review")
async def review_return(
    case_id: str,
    payload: ReturnReviewRequest,
    session: AsyncSession = Depends(get_session),
):
    # 1. Check that the case exists.
    case = await session.get(ReturnCase, case_id)

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Return case not found",
        )

    # 2. Validate the requested decision and reason.
    try:
        new_status = apply_review(
            current_status=CaseStatus(case.status),
            decision=ReviewDecision(payload.decision),
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    previous_status = case.status

    # 3. Atomically claim the case.
    # The update succeeds only if the case is still pending_review.
    try:
        result = await session.execute(
            update(ReturnCase)
            .where(
                ReturnCase.case_id == case_id,
                ReturnCase.status == CaseStatus.PENDING_REVIEW.value,
            )
            .values(status=new_status.value)
        )

        if result.rowcount != 1:
            # Another request may have reviewed the case already.
            await session.rollback()

            existing_case = await session.get(ReturnCase, case_id)

            if existing_case is None:
                raise HTTPException(
                    status_code=404,
                    detail="Return case not found",
                )

            raise HTTPException(
                status_code=409,
                detail="Return case is no longer pending review",
            )

        # 4. Prepare the review and audit records.
        # Temporary development identity only.
        reviewer_id = "local-development-reviewer"

        session.add(
            ReviewRecord(
                case_id=case_id,
                reviewer_id=reviewer_id,
                decision=payload.decision,
                reason=payload.reason,
            )
        )

        session.add(
            AuditEvent(
                case_id=case_id,
                event_type="return_reviewed",
                actor=reviewer_id,
                details={
                    "decision": payload.decision,
                    "reason": payload.reason,
                    "previous_status": previous_status,
                    "new_status": new_status.value,
                },
            )
        )

        # 5. Commit the status change and both records together.
        await session.commit()

    except HTTPException:
        raise
    except Exception:
        await session.rollback()
        raise

    return {
        "case_id": case_id,
        "status": new_status.value,
    }