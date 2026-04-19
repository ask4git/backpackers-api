from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SpotSummary(BaseModel):
    uid: UUID
    title: str
    address: str | None = None
    region_province: str | None = None
    region_city: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    category: list[str] | None = None
    amenities: list[str] | None = None
    themes: list[str] | None = None
    is_pet_allowed: bool | None = None
    is_fee_required: bool | None = None
    rating_avg: float
    review_count: int

    model_config = {"from_attributes": True}


class SpotDetail(SpotSummary):
    description: str | None = None
    tagline: str | None = None
    features: str | None = None
    phone: str | None = None
    website_url: str | None = None
    booking_url: str | None = None
    nearby_facilities: list[str] | None = None
    fire_pit_type: str | None = None
    camp_sight_type: str | None = None
    has_equipment_rental: list[str] | None = None
    total_area_m2: float | None = None
    unit_count: int | None = None
    created_at: datetime
    updated_at: datetime


class SpotSearchResponse(BaseModel):
    items: list[SpotSummary]
    total: int
    page: int
    limit: int
    total_pages: int


class RegionCity(BaseModel):
    province: str
    cities: list[str]


class RegionListResponse(BaseModel):
    regions: list[RegionCity]
