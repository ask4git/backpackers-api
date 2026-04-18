from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: float = Field(..., ge=0, le=5, description="별점 (0~5)")
    content: str | None = None


class ReviewResponse(BaseModel):
    uid: UUID
    spot_uid: UUID
    user_id: UUID
    rating: float
    content: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    rating_avg: float
