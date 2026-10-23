
import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.db import get_session
from app.main import app
from app.models import (
    AuditEvent,
    Base,
    Evaluation,
    Order,
    ReturnCase,
    ReviewRecord,
)


POSTGRES_TEST_URL = os.getenv("RETURNGUARD_POSTGRES_TEST_URL")

pytestmark = pytest.mark.skipif(
    not POSTGRES_TEST_URL,
    reason="Set RETURNGUARD_POSTGRES_TEST_URL to enable PostgreSQL integration tests",
)


def test_concurrent_reviews_allow_exactly_one_winner():
    assert POSTGRES_TEST_URL is not None

    if not POSTGRES_TEST_URL.startswith("postgresql+psycopg://"):
        pytest.fail(
            "RETURNGUARD_POSTGRES_TEST_URL must use "
            "postgresql+psycopg:// and point to the dedicated test database"
        )

    async def scenario():
        engine = create_async_engine(
            POSTGRES_TEST_URL,
            pool_size=5,
            max_overflow=2,
            pool_pre_ping=True,
        )
        session_factory = async_sessionmaker(
            engine,
            expire_on_commit=False,
        )

        async def override_get_session():
            async with session_factory() as session:
                yield session

        previous_overrides = app.dependency_overrides.copy()
        app.dependency_overrides[get_session] = override_get_session

        suffix = uuid.uuid4().hex[:12]
        case_id = f"pg-concurrency-{suffix}"
        order_id = f"pg-order-{suffix}"

        transport = httpx.ASGITransport(app=app)

        try:
            # Create a real pending case through the API.
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://test",
            ) as client:
                create_response = await client.post(
                    "/returns/evaluate",
                    json={
                        "case_id": case_id,
                        "order_id": order_id,
                        "order_amount": "2500.00",
                        "refund_amount": "500.00",
                        "days_since_delivery": 3,
                        "return_window_days": 30,
                        "evidence_required": False,
                        "evidence_available": True,
                        "duplicate_request": False,
                        "previous_returns_90d": 0,
                        "delivery_status": "delivered",
                        "evidence_consistent": False,
                    },
                )

                assert create_response.status_code == 200, (
                    create_response.status_code,
                    create_response.text,
                )
                assert create_response.json()["outcome"] == "human_review"

                # Both requests target the same pending case.
                async def submit_review(decision: str):
                    return await client.post(
                        f"/returns/{case_id}/review",
                        json={
                            "decision": decision,
                            "reason": f"Concurrent test: {decision}",
                        },
                    )

                responses = await asyncio.gather(
                    submit_review("approve"),
                    submit_review("reject"),
                )

            statuses = sorted(response.status_code for response in responses)
            assert statuses == [200, 409], [
                (response.status_code, response.text)
                for response in responses
            ]

            async with session_factory() as session:
                case = await session.get(ReturnCase, case_id)

                review_count = await session.scalar(
                    select(func.count())
                    .select_from(ReviewRecord)
                    .where(ReviewRecord.case_id == case_id)
                )

                review_audit_count = await session.scalar(
                    select(func.count())
                    .select_from(AuditEvent)
                    .where(
                        AuditEvent.case_id == case_id,
                        AuditEvent.event_type == "return_reviewed",
                    )
                )

                reviews = (
                    await session.scalars(
                        select(ReviewRecord).where(
                            ReviewRecord.case_id == case_id
                        )
                    )
                ).all()

                assert case is not None
                assert case.status in {"approved", "rejected"}
                assert review_count == 1
                assert review_audit_count == 1
                assert len(reviews) == 1

                # The final status must agree with the winning decision.
                expected_status = {
                    "approve": "approved",
                    "reject": "rejected",
                }[reviews[0].decision]
                assert case.status == expected_status

        finally:
            # Restore the app's previous dependency configuration.
            app.dependency_overrides.clear()
            app.dependency_overrides.update(previous_overrides)

            # Delete only the records created by this test.
            async with session_factory() as session:
                try:
                    await session.execute(
                        delete(AuditEvent).where(
                            AuditEvent.case_id == case_id
                        )
                    )
                    await session.execute(
                        delete(ReviewRecord).where(
                            ReviewRecord.case_id == case_id
                        )
                    )
                    await session.execute(
                        delete(Evaluation).where(
                            Evaluation.case_id == case_id
                        )
                    )
                    await session.execute(
                        delete(ReturnCase).where(
                            ReturnCase.case_id == case_id
                        )
                    )
                    await session.execute(
                        delete(Order).where(Order.order_id == order_id)
                    )
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await engine.dispose()

    asyncio.run(
    scenario(),
    loop_factory=asyncio.SelectorEventLoop,
  )
