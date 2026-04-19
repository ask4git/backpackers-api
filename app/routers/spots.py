from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.crud.spot import get_regions, get_spot_by_uid, search_spots
from app.schemas.spot import (
    RegionCity,
    RegionListResponse,
    SpotDetail,
    SpotSearchResponse,
)

router = APIRouter(prefix="/spots", tags=["spots"])


@router.get("", response_model=SpotSearchResponse)
async def list_spots(
    q: str | None = Query(None, description="캠핑장 이름 또는 주소 검색"),
    province: str | None = Query(None, description="도/특별시/광역시 (1depth 지역 필터)"),
    city: str | None = Query(None, description="시/군/구 (2depth 지역 필터)"),
    amenities: list[str] = Query(default=[], description="편의시설 필터 (복수 선택, AND 조건)"),
    sort: str = Query("rating", description="정렬 기준: rating | review_count | name"),
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 항목 수"),
    db: AsyncSession = Depends(get_db),
):
    spots, total = await search_spots(
        db,
        q=q,
        province=province,
        city=city,
        amenities=amenities if amenities else None,
        page=page,
        limit=limit,
        sort=sort,
    )
    total_pages = (total + limit - 1) // limit if total > 0 else 0
    return SpotSearchResponse(
        items=spots,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages,
    )


@router.get("/regions", response_model=RegionListResponse)
async def list_regions(db: AsyncSession = Depends(get_db)):
    """지역 필터 드롭다운용 province → cities 계층 목록 반환"""
    rows = await get_regions(db)
    grouped: dict[str, list[str]] = {}
    for province, city in rows:
        grouped.setdefault(province, []).append(city)
    regions = [
        RegionCity(province=prov, cities=cities)
        for prov, cities in sorted(grouped.items())
    ]
    return RegionListResponse(regions=regions)


@router.get("/{spot_uid}", response_model=SpotDetail)
async def get_spot(
    spot_uid: UUID,
    db: AsyncSession = Depends(get_db),
):
    spot = await get_spot_by_uid(db, spot_uid)
    if not spot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="존재하지 않는 캠핑장입니다.",
        )
    return spot
