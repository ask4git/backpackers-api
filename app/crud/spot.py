from uuid import UUID

from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.spot import Spot


async def search_spots(
    db: AsyncSession,
    q: str | None,
    province: str | None,
    city: str | None,
    amenities: list[str] | None,
    page: int,
    limit: int,
    sort: str,
) -> tuple[list[Spot], int]:
    stmt = select(Spot)

    if q:
        stmt = stmt.where(
            or_(
                Spot.title.ilike(f"%{q}%"),
                Spot.address.ilike(f"%{q}%"),
            )
        )

    if province:
        stmt = stmt.where(Spot.region_province == province)

    if city:
        stmt = stmt.where(Spot.region_city == city)

    if amenities:
        # PostgreSQL ARRAY @> : amenities 컬럼이 요청한 모든 항목을 포함해야 함
        stmt = stmt.where(
            Spot.amenities.op("@>")(cast(amenities, ARRAY(String)))
        )

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    if sort == "review_count":
        stmt = stmt.order_by(Spot.review_count.desc())
    elif sort == "name":
        stmt = stmt.order_by(Spot.title.asc())
    else:  # 기본값: rating
        stmt = stmt.order_by(Spot.rating_avg.desc())

    offset = (page - 1) * limit
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    return list(result.scalars().all()), total


async def get_spot_by_uid(db: AsyncSession, spot_uid: UUID) -> Spot | None:
    result = await db.execute(select(Spot).where(Spot.uid == spot_uid))
    return result.scalar_one_or_none()


async def get_regions(db: AsyncSession) -> list[tuple[str, str]]:
    result = await db.execute(
        select(Spot.region_province, Spot.region_city)
        .where(
            Spot.region_province.isnot(None),
            Spot.region_city.isnot(None),
        )
        .distinct()
        .order_by(Spot.region_province, Spot.region_city)
    )
    return result.all()
