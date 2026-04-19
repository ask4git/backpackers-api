"""
src_01 데이터 → spots + spot_business_info 테이블 임포트

실행 (1회성):
    # 로컬 DB
    ENV_FILE=.env.local uv run python -m scripts.oneoff.import_src01

    # prod DB (make tunnel 먼저 실행)
    ENV_FILE=.env.prod uv run python -m scripts.oneoff.import_src01

중복 방지: title + address 조합이 이미 존재하면 스킵
"""

import asyncio
import json
import ssl
import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models.spot import Spot, SpotBusinessInfo

SPOTS_PATH = Path(
    "/Users/ask4git/CursorProjects/backpackers-etl"
    "/data/master/src_01/raw/spots_src_01_temp.json"
)
BIZ_PATH = Path(
    "/Users/ask4git/CursorProjects/backpackers-etl"
    "/data/master/src_01/raw/spots_business_info_src_01_temp.json"
)


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


def _build_biz(row: dict, spot_uid) -> SpotBusinessInfo | None:
    if not any(row.get(f) for f in row):
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
    for p in (SPOTS_PATH, BIZ_PATH):
        if not p.exists():
            print(f"파일을 찾을 수 없습니다: {p}")
            sys.exit(1)

    spots_data = json.loads(SPOTS_PATH.read_text(encoding="utf-8"))
    biz_data = json.loads(BIZ_PATH.read_text(encoding="utf-8"))

    if len(spots_data) != len(biz_data):
        print(f"레코드 수 불일치: spots={len(spots_data)}, biz={len(biz_data)}")
        sys.exit(1)

    print(f"총 {len(spots_data)}개 레코드 로드")

    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE

    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args={"ssl": ssl_ctx},
    )
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    spots = [_build_spot(row) for row in spots_data]

    async with session_factory() as db:
        db.add_all(spots)
        await db.flush()  # spot uid 확보

        biz_list = [
            biz for spot, row in zip(spots, biz_data)
            if (biz := _build_biz(row, spot.uid)) is not None
        ]
        db.add_all(biz_list)
        await db.commit()

    await engine.dispose()
    print(f"완료 — spots: {len(spots)}개, business_info: {len(biz_list)}개 삽입")


if __name__ == "__main__":
    asyncio.run(run())
