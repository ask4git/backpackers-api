import math
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.camping_spot import create_spot_report, get_spot_by_id, get_spots
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.camping_spot import (
    AmenityEnum,
    CampingSpotDetail,
    CampingSpotSummary,
    LocationSchema,
    PaginatedSpotsResponse,
    RegionEnum,
    SpotReportCreate,
    SpotReportResponse,
)

router = APIRouter(prefix="/spots", tags=["camping-spots"])


@router.get("", response_model=PaginatedSpotsResponse)
async def list_spots(
    q: Optional[str] = Query(None, description="이름·설명·태그 검색"),
    region: Optional[RegionEnum] = Query(None),
    amenities: Optional[list[AmenityEnum]] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    spots, total = await get_spots(db, q=q, region=region, amenities=amenities, page=page, limit=limit)

    items = [
        CampingSpotSummary(
            id=spot.id,
            name=spot.name,
            location=LocationSchema(lat=spot.lat, lng=spot.lng, address=spot.address, region=spot.region),
            amenities=spot.amenities or [],
            tags=spot.tags or [],
            rating=spot.rating,
            review_count=spot.review_count,
            status=spot.status,
            thumbnail_image=(spot.images[0] if spot.images else None),
        )
        for spot in spots
    ]

    return PaginatedSpotsResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
        total_pages=math.ceil(total / limit) if total > 0 else 0,
    )


@router.get("/{spot_id}", response_model=CampingSpotDetail)
async def get_spot(spot_id: UUID, db: AsyncSession = Depends(get_db)):
    spot = await get_spot_by_id(db, spot_id)
    if not spot:
        raise HTTPException(status_code=404, detail="캠핑장을 찾을 수 없습니다.")

    return CampingSpotDetail(
        id=spot.id,
        name=spot.name,
        description=spot.description,
        location=LocationSchema(lat=spot.lat, lng=spot.lng, address=spot.address, region=spot.region),
        amenities=spot.amenities or [],
        tags=spot.tags or [],
        images=spot.images or [],
        source=spot.source,
        status=spot.status,
        rating=spot.rating,
        review_count=spot.review_count,
        created_at=spot.created_at,
        updated_at=spot.updated_at,
    )


@router.post("/report", response_model=SpotReportResponse, status_code=status.HTTP_201_CREATED)
async def report_spot(
    data: SpotReportCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    report = await create_spot_report(
        db,
        name=data.name,
        description=data.description,
        lat=data.lat,
        lng=data.lng,
        address=data.address,
        amenities=[a.value for a in data.amenities],
        images=data.images,
        reporter_contact=data.reporter_contact,
    )
    return SpotReportResponse(
        id=report.id,
        name=report.name,
        description=report.description,
        lat=report.lat,
        lng=report.lng,
        address=report.address,
        amenities=report.amenities or [],
        images=report.images or [],
        reporter_contact=report.reporter_contact,
        status=report.status,
        created_at=report.created_at,
    )
