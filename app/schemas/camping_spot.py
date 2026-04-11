import math
from datetime import datetime
from enum import Enum
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel


class AmenityEnum(str, Enum):
    toilet = "toilet"
    parking = "parking"
    water = "water"
    shower = "shower"
    fire_pit = "fire_pit"
    trash = "trash"


class RegionEnum(str, Enum):
    seoul = "서울"
    gyeonggi = "경기"
    gangwon = "강원"
    chungbuk = "충북"
    chungnam = "충남"
    jeonbuk = "전북"
    jeonnam = "전남"
    gyeongbuk = "경북"
    gyeongnam = "경남"
    jeju = "제주"


class LocationSchema(BaseModel):
    lat: float
    lng: float
    address: str
    region: str


class CampingSpotSummary(BaseModel):
    id: UUID
    name: str
    location: LocationSchema
    amenities: list[str]
    tags: list[str]
    rating: float
    review_count: int
    status: str
    thumbnail_image: Optional[str] = None


class CampingSpotDetail(BaseModel):
    id: UUID
    name: str
    description: str
    location: LocationSchema
    amenities: list[str]
    tags: list[str]
    images: list[str]
    source: Literal["public_data", "user_report"]
    status: Literal["verified", "pending", "rejected"]
    rating: float
    review_count: int
    created_at: datetime
    updated_at: datetime


class SpotReportCreate(BaseModel):
    name: str
    description: str
    lat: float
    lng: float
    address: str
    amenities: list[AmenityEnum] = []
    images: list[str] = []
    reporter_contact: Optional[str] = None


class SpotReportResponse(BaseModel):
    id: UUID
    name: str
    description: str
    lat: float
    lng: float
    address: str
    amenities: list[str]
    images: list[str]
    reporter_contact: Optional[str]
    status: str
    created_at: datetime


class PaginatedSpotsResponse(BaseModel):
    items: list[CampingSpotSummary]
    total: int
    page: int
    limit: int
    total_pages: int
