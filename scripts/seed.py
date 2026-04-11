"""
더미 캠핑장 데이터 시드 스크립트
실행: python -m scripts.seed
"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.core.config import settings
from app.models.camping_spot import CampingSpot

SEED_SPOTS = [
    {
        "name": "설악산 국립공원 한계령 야영장",
        "description": "설악산의 웅장한 경관을 배경으로 한 야영장. 울산바위와 공룡능선이 가까워 등산객에게 인기가 높다. 계곡 옆에 위치해 여름철 피서지로도 각광받는다.",
        "lat": 38.1192,
        "lng": 128.4661,
        "address": "강원특별자치도 인제군 북면 한계리",
        "region": "강원",
        "amenities": ["toilet", "parking", "water", "trash"],
        "tags": ["국립공원", "등산", "계곡", "단풍"],
        "images": [],
        "source": "public_data",
        "status": "verified",
        "rating": 4.7,
        "review_count": 312,
    },
    {
        "name": "지리산 국립공원 달궁 야영장",
        "description": "지리산 노고단과 반야봉 등 주요 봉우리로의 접근이 편리한 야영장. 넓은 평지에 잘 정비된 시설을 갖추고 있으며, 사계절 내내 아름다운 풍경을 자랑한다.",
        "lat": 35.3603,
        "lng": 127.5233,
        "address": "전라북도 남원시 산내면 부운리",
        "region": "전북",
        "amenities": ["toilet", "parking", "water", "shower", "trash"],
        "tags": ["국립공원", "등산", "가족캠핑", "지리산"],
        "images": [],
        "source": "public_data",
        "status": "verified",
        "rating": 4.5,
        "review_count": 248,
    },
    {
        "name": "한라산 국립공원 어리목 야영장",
        "description": "한라산 서쪽 어리목 탐방로 입구에 위치한 야영장. 울창한 제주 원시림 속에 자리잡고 있으며, 백록담으로 향하는 등산의 출발점으로 활용된다.",
        "lat": 33.3927,
        "lng": 126.4749,
        "address": "제주특별자치도 제주시 해안동",
        "region": "제주",
        "amenities": ["toilet", "parking", "water", "trash"],
        "tags": ["국립공원", "한라산", "등산", "제주"],
        "images": [],
        "source": "public_data",
        "status": "verified",
        "rating": 4.8,
        "review_count": 421,
    },
    {
        "name": "북한산 국립공원 우이동 야영장",
        "description": "서울 근교에서 가장 접근성이 좋은 야영장 중 하나. 도봉산과 북한산 능선 조망이 훌륭하며, 대중교통으로도 쉽게 접근할 수 있어 주말 캠핑객에게 인기다.",
        "lat": 37.6617,
        "lng": 127.0147,
        "address": "서울특별시 강북구 우이동",
        "region": "서울",
        "amenities": ["toilet", "parking", "water", "trash"],
        "tags": ["국립공원", "서울근교", "당일치기", "북한산"],
        "images": [],
        "source": "public_data",
        "status": "verified",
        "rating": 4.2,
        "review_count": 186,
    },
    {
        "name": "덕유산 국립공원 삿갓재 야영장",
        "description": "향적봉 아래 고지대에 위치한 야영장. 겨울철 설경이 특히 아름답고, 무주 리조트와 가까워 스키와 등산을 함께 즐길 수 있다.",
        "lat": 35.8636,
        "lng": 127.7421,
        "address": "전라북도 무주군 설천면 삼공리",
        "region": "전북",
        "amenities": ["toilet", "parking", "water", "fire_pit", "trash"],
        "tags": ["국립공원", "덕유산", "겨울산행", "설경"],
        "images": [],
        "source": "public_data",
        "status": "verified",
        "rating": 4.4,
        "review_count": 134,
    },
    {
        "name": "태안해안 국립공원 만리포 캠핑장",
        "description": "서해안 최대 해수욕장 중 하나인 만리포와 인접한 캠핑장. 일몰이 아름답기로 유명하며, 여름철 해수욕과 캠핑을 동시에 즐길 수 있다.",
        "lat": 36.7781,
        "lng": 126.3012,
        "address": "충청남도 태안군 소원면 만리포길",
        "region": "충남",
        "amenities": ["toilet", "parking", "water", "shower", "fire_pit", "trash"],
        "tags": ["해변", "일몰", "여름캠핑", "서해"],
        "images": [],
        "source": "public_data",
        "status": "verified",
        "rating": 4.3,
        "review_count": 297,
    },
    {
        "name": "오대산 국립공원 진고개 야영장",
        "description": "오대산 비로봉과 동대산 사이 진고개에 위치. 원시림 분위기가 강하게 남아 있으며, 월정사까지 이어지는 전나무 숲길이 캠핑의 낭만을 더한다.",
        "lat": 37.7683,
        "lng": 128.5714,
        "address": "강원특별자치도 평창군 진부면 오대산로",
        "region": "강원",
        "amenities": ["toilet", "parking", "water", "trash"],
        "tags": ["국립공원", "전나무숲", "오대산", "조용한"],
        "images": [],
        "source": "public_data",
        "status": "verified",
        "rating": 4.6,
        "review_count": 178,
    },
    {
        "name": "주왕산 국립공원 주방천 야영장",
        "description": "기암절벽과 폭포로 유명한 주왕산 계곡 옆에 자리한 야영장. 물소리를 들으며 잠들 수 있는 계곡 캠핑의 진수를 경험할 수 있다.",
        "lat": 36.3929,
        "lng": 129.1604,
        "address": "경상북도 청송군 부동면 상의리",
        "region": "경북",
        "amenities": ["toilet", "parking", "water", "trash"],
        "tags": ["국립공원", "계곡", "기암절벽", "주왕산"],
        "images": [],
        "source": "public_data",
        "status": "verified",
        "rating": 4.5,
        "review_count": 203,
    },
]


async def seed():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        for data in SEED_SPOTS:
            spot = CampingSpot(**data)
            db.add(spot)
        await db.commit()
        print(f"✓ {len(SEED_SPOTS)}개 캠핑장 데이터 삽입 완료")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
