"""
gocamping_campsites.json → spots + spot_business_info 테이블 임포트

실행 (1회성):
    ENV_FILE=.env.local uv run python -m scripts.import_gocamping

중복 방지: title + address 조합이 이미 존재하면 스킵
"""

import asyncio
import json
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.spot import Spot, SpotBusinessInfo

DATA_PATH = Path(__file__).parent.parent.parent / "backpackers-etl" / "data" / "gocamping_campsites.json"


def _build_spot(row: dict) -> Spot:
    return Spot(
        title=row["title"],
        tagline=row.get("tagline") or None,
        description=row.get("description") or None,
        features=row.get("features") or None,
        category=row.get("category") or None,
        address=row.get("address") or None,
        address_detail=row.get("address_detail") or None,
        region_province=row.get("region_province") or None,
        region_city=row.get("region_city") or None,
        postal_code=row.get("postal_code") or None,
        phone=row.get("phone") or None,
        website_url=row.get("website_url") or None,
        booking_url=row.get("booking_url") or None,
        total_area_m2=row.get("total_area_m2"),
        has_liability_insurance=row.get("has_liability_insurance"),
        amenities=row.get("amenities") or None,
    )


def _build_business_info(row: dict, spot_uid) -> SpotBusinessInfo | None:
    fields = ("business_reg_no", "tourism_business_reg_no", "business_type",
              "operation_type", "operating_agency", "operating_status")
    if not any(row.get(f) for f in fields):
        return None
    return SpotBusinessInfo(
        spot_uid=spot_uid,
        business_reg_no=row.get("business_reg_no") or None,
        tourism_business_reg_no=row.get("tourism_business_reg_no") or None,
        business_type=row.get("business_type"),
        operation_type=row.get("operation_type") or None,
        operating_agency=row.get("operating_agency") or None,
        operating_status=row.get("operating_status") or None,
    )


async def run() -> None:
    if not DATA_PATH.exists():
        print(f"파일을 찾을 수 없습니다: {DATA_PATH}")
        sys.exit(1)

    data: list[dict] = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    print(f"총 {len(data)}개 레코드 로드")

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    inserted = skipped = 0

    async with session_factory() as db:
        for row in data:
            title = row.get("title", "").strip()
            address = row.get("address", "").strip()

            # 중복 체크
            exists = await db.scalar(
                select(Spot.uid).where(Spot.title == title, Spot.address == address)
            )
            if exists:
                skipped += 1
                continue

            spot = _build_spot(row)
            db.add(spot)
            await db.flush()  # uid 확보

            biz = _build_business_info(row, spot.uid)
            if biz:
                db.add(biz)

            inserted += 1

        await db.commit()

    await engine.dispose()
    print(f"완료 — 삽입: {inserted}개 / 스킵(중복): {skipped}개")


if __name__ == "__main__":
    asyncio.run(run())
