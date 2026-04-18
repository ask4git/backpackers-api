from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.review import create_review, get_reviews_by_spot
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewListResponse, ReviewResponse

router = APIRouter(tags=["reviews"])


@router.post(
    "/spots/{spot_uid}/reviews",
    response_model=ReviewResponse,
    status_code=status.HTTP_201_CREATED,
)
async def write_review(
    spot_uid: UUID,
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        review = await create_review(
            db,
            spot_uid=spot_uid,
            user_id=current_user.id,
            rating=data.rating,
            content=data.content,
        )
    except IntegrityError as e:
        await db.rollback()
        if "uq_spot_user_review" in str(e.orig):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 이 스팟에 리뷰를 작성했습니다.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 스팟입니다.",
        )
    return review


@router.get("/spots/{spot_uid}/reviews", response_model=ReviewListResponse)
async def list_reviews(
    spot_uid: UUID,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    reviews, total, rating_avg = await get_reviews_by_spot(db, spot_uid, page, limit)
    return ReviewListResponse(
        items=reviews,
        total=total,
        rating_avg=round(rating_avg, 2),
    )
