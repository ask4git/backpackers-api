from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import SpotReview
from app.models.spot import Spot


async def create_review(
    db: AsyncSession,
    spot_uid: UUID,
    user_id: UUID,
    rating: float,
    content: str | None,
) -> SpotReview:
    review = SpotReview(
        spot_uid=spot_uid,
        user_id=user_id,
        rating=rating,
        content=content,
    )
    db.add(review)
    await db.flush()
    await _refresh_spot_rating(db, spot_uid)
    await db.commit()
    await db.refresh(review)
    return review


async def get_reviews_by_spot(
    db: AsyncSession,
    spot_uid: UUID,
    page: int,
    limit: int,
) -> tuple[list[SpotReview], int, float]:
    base = select(SpotReview).where(SpotReview.spot_uid == spot_uid)

    total_result = await db.execute(select(func.count()).select_from(base.subquery()))
    total = total_result.scalar() or 0

    avg_result = await db.execute(
        select(func.avg(SpotReview.rating)).where(SpotReview.spot_uid == spot_uid)
    )
    rating_avg = float(avg_result.scalar() or 0.0)

    offset = (page - 1) * limit
    result = await db.execute(
        base.order_by(SpotReview.created_at.desc()).offset(offset).limit(limit)
    )
    reviews = list(result.scalars().all())

    return reviews, total, rating_avg


async def _refresh_spot_rating(db: AsyncSession, spot_uid: UUID) -> None:
    result = await db.execute(
        select(
            func.avg(SpotReview.rating),
            func.count(SpotReview.uid),
        ).where(SpotReview.spot_uid == spot_uid)
    )
    row = result.one()
    avg = float(row[0] or 0.0)
    count = row[1]

    await db.execute(
        update(Spot)
        .where(Spot.uid == spot_uid)
        .values(rating_avg=avg, review_count=count)
    )
