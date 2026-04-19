import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    Float,
    ForeignKey,
    Integer,
    String,
    DateTime,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Spot(Base):
    __tablename__ = "spots"

    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False, index=True)
    address = Column(String, nullable=True)
    address_detail = Column(String, nullable=True)
    region_province = Column(String, nullable=True, index=True)  # 도
    region_city = Column(String, nullable=True, index=True)  # 시군구
    postal_code = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website_url = Column(String, nullable=True)
    booking_url = Column(String, nullable=True)
    description = Column(String, nullable=True)
    tagline = Column(String, nullable=True)
    features = Column(String, nullable=True)  # 특징 (gocamping 원문)
    category = Column(
        ARRAY(String), nullable=True
    )  # 캠핑장 유형 (TENT_SITE, GLAMPING 등)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    altitude = Column(Float, nullable=True)
    # geom: PostGIS GEOMETRY — geoalchemy2 설치 후 추가 예정
    total_area_m2 = Column(Float, nullable=True)  # 총 면적(㎡)
    unit_count = Column(Integer, nullable=True)  # 야영동 개수
    is_fee_required = Column(Boolean, nullable=True)  # 야영료 징수 여부
    is_pet_allowed = Column(Boolean, nullable=True)  # 반려동물 출입 여부
    has_liability_insurance = Column(Boolean, nullable=True)  # 배상책임보험 가입 여부
    pet_policy = Column(String, nullable=True)  # 반려동물 정책
    has_equipment_rental = Column(ARRAY(String), nullable=True)  # 대여 가능 장비 목록
    themes = Column(ARRAY(String), nullable=True)  # 테마환경
    fire_pit_type = Column(String, nullable=True)  # 화로대 타입
    amenities = Column(ARRAY(String), nullable=True)  # 부대시설
    nearby_facilities = Column(ARRAY(String), nullable=True)  # 주변 이용 가능 시설
    camp_sight_type = Column(
        String, nullable=True
    )  # 바닥 타입 (파쇄석/흙/잔디/데크 등)
    rating_avg = Column(
        Float, nullable=False, default=0.0, index=True
    )  # 평균 별점 (리뷰 생성 시 갱신)
    review_count = Column(
        Integer, nullable=False, default=0
    )  # 리뷰 수 (리뷰 생성 시 갱신)

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    business_info = relationship(
        "SpotBusinessInfo", back_populates="spot", uselist=False
    )


class SpotBusinessInfo(Base):
    __tablename__ = "spot_business_info"

    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    spot_uid = Column(
        UUID(as_uuid=True), ForeignKey("spots.uid"), nullable=False, index=True
    )
    business_reg_no = Column(String, nullable=True)  # 사업자번호
    tourism_business_reg_no = Column(String, nullable=True)  # 관광사업자번호
    business_type = Column(String, nullable=True)  # 사업주체
    operation_type = Column(String, nullable=True)  # 운영주체
    operating_agency = Column(String, nullable=True)  # 운영기관
    operating_status = Column(String, nullable=True, index=True)  # 운영상태
    national_park_no = Column(Integer, nullable=True)  # 국립공원관리번호
    national_park_office_code = Column(String, nullable=True)  # 공원사무소코드
    national_park_serial_no = Column(String, nullable=True)  # 일련번호
    national_park_category_code = Column(String, nullable=True)  # 분류코드
    licensed_at = Column(Date, nullable=True)  # 인허가일자

    created_at = Column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    spot = relationship("Spot", back_populates="business_info")
