import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Float, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY

from app.core.database import Base


class CampingSpot(Base):
    __tablename__ = "camping_spots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    address = Column(String, nullable=False)
    region = Column(String, nullable=False, index=True)
    amenities = Column(ARRAY(String), nullable=False, default=list)
    tags = Column(ARRAY(String), nullable=False, default=list)
    images = Column(ARRAY(String), nullable=False, default=list)
    # "public_data" | "user_report"
    source = Column(String, nullable=False, default="public_data")
    # "verified" | "pending" | "rejected"
    status = Column(String, nullable=False, default="pending", index=True)
    rating = Column(Float, nullable=False, default=0.0)
    review_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class SpotReport(Base):
    __tablename__ = "spot_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    address = Column(String, nullable=False)
    amenities = Column(ARRAY(String), nullable=False, default=list)
    images = Column(ARRAY(String), nullable=False, default=list)
    reporter_contact = Column(String, nullable=True)
    # 항상 "pending" 으로 생성
    status = Column(String, nullable=False, default="pending")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
