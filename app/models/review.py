import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class SpotReview(Base):
    __tablename__ = "spot_reviews"

    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spot_uid = Column(
        UUID(as_uuid=True), ForeignKey("spots.uid"), nullable=False, index=True
    )
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    rating = Column(Float, nullable=False)
    content = Column(String, nullable=True)
    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        CheckConstraint(
            "rating >= 0 AND rating <= 5", name="check_review_rating_range"
        ),
        UniqueConstraint("spot_uid", "user_id", name="uq_spot_user_review"),
    )
