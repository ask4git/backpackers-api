import math
from uuid import UUID

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.camping_spot import CampingSpot, SpotReport
from app.schemas.camping_spot import AmenityEnum, RegionEnum


async def get_spots(
    db: AsyncSession,
    q: str | None,
    region: RegionEnum | None,
    amenities: list[AmenityEnum] | None,
    page: int,
    limit: int,
) -> tuple[list[CampingSpot], int]:
    query = select(CampingSpot).where(CampingSpot.status == "verified")

    if q:
        query = query.where(
            or_(
                CampingSpot.name.ilike(f"%{q}%"),
                CampingSpot.description.ilike(f"%{q}%"),
                CampingSpot.tags.any(q),
            )
        )

    if region:
        query = query.where(CampingSpot.region == region.value)

    if amenities:
        for amenity in amenities:
            query = query.where(CampingSpot.amenities.contains([amenity.value]))

    total_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = total_result.scalar() or 0

    offset = (page - 1) * limit
    query = query.order_by(CampingSpot.rating.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    spots = list(result.scalars().all())

    return spots, total


async def get_spot_by_id(db: AsyncSession, spot_id: UUID) -> CampingSpot | None:
    result = await db.execute(select(CampingSpot).where(CampingSpot.id == spot_id))
    return result.scalar_one_or_none()


async def create_spot_report(
    db: AsyncSession,
    name: str,
    description: str,
    lat: float,
    lng: float,
    address: str,
    amenities: list[str],
    images: list[str],
    reporter_contact: str | None,
) -> SpotReport:
    report = SpotReport(
        name=name,
        description=description,
        lat=lat,
        lng=lng,
        address=address,
        amenities=amenities,
        images=images,
        reporter_contact=reporter_contact,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report
