import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    func,
    Text,
    Uuid
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    order_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    delivery_status: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )



class ReturnCase(Base):
    __tablename__ = "return_cases"

    case_id: Mapped[str] = mapped_column(
        String(64), primary_key=True
    )
    order_id: Mapped[str] = mapped_column(
        ForeignKey("orders.order_id"), nullable=False, index=True
    )
    refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    days_since_delivery: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    return_window_days: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    evidence_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
    evidence_available: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
    duplicate_request: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
    previous_returns_90d: Mapped[int] = mapped_column(
        Integer, nullable=False
    )
    delivery_status: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    evidence_consistent: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="pending_review",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )



class Evaluation(Base):
    __tablename__ = "evaluations"

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[str] = mapped_column(
        ForeignKey("return_cases.case_id"), nullable=False, index=True
    )
    outcome: Mapped[str] = mapped_column(
        String(32), nullable=False
    )
    risk_level: Mapped[str] = mapped_column(
        String(16), nullable=False
    )
    reasons: Mapped[list[str]] = mapped_column(
        JSON, nullable=False
    )
    policy_version: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    event_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[str | None] = mapped_column(
        ForeignKey("return_cases.case_id"),
        nullable=True,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )
    actor: Mapped[str] = mapped_column(
        String(128), nullable=False
    )
    details: Mapped[dict[str, object]] = mapped_column(
        JSON, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

class ReviewRecord(Base):
    __tablename__ = "review_records"

    review_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        primary_key = True,
        default = uuid.uuid4,
    )    
    case_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("return_cases.case_id"),
        nullable=False,
        index=True,
    )

    reviewer_id: Mapped[str] = mapped_column(
        String(128),
        nullable = False,
    )
    decision: Mapped[str] = mapped_column(
        String(16),
        nullable = False,
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable = False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
