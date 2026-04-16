# Backpackers API — 배포 진행 기록

## 프로젝트 개요

| 항목 | 내용 |
|------|------|
| 프로젝트명 | Backpackers API |
| 설명 | 국립공원·캠핑장 정보 플랫폼 API |
| 스택 | FastAPI · PostgreSQL 16 · SQLAlchemy (async) · Alembic |
| 배포 환경 | AWS Lightsail (서울, ap-northeast-2) |
| API URL | https://backpackers-api.8x8077g16h76j.ap-northeast-2.cs.amazonlightsail.com |

---

## 작업 1. DB 모델 리뷰 (`app/models/user.py`)

### 발견된 이슈

| 위험도 | 이슈 |
|--------|------|
| 중 | `String` 컬럼에 length 미지정 (`email`, `hashed_password`, `name`) |
| 중 | `created_at` / `updated_at` 에 `server_default` 미사용 (Python default만 적용) |
| 하 | `created_at` / `updated_at` 에 `nullable=False` 미설정 |
| 하 | `created_at` 인덱스 미설정 (빈번한 정렬·필터 시 고려 필요) |

### 양호한 항목
- `DateTime(timezone=True)` 사용 — timezone 설정 정상
- `email` 컬럼 `index=True` 적용
- 현재 관계(relationship) 없어 N+1 및 FK 인덱스 이슈 없음

---

## 작업 2. AWS Lightsail 배포

### 2-1. Dockerfile 작성

프로젝트 루트에 `Dockerfile` 생성 (linux/amd64 대응).

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

> Mac M-시리즈(ARM)에서 빌드 시 `--platform linux/amd64` 옵션 필수

### 2-2. AWS 인프라 구성 (CLI)

```bash
# Container Service 생성
aws lightsail create-container-service \
  --service-name backpackers-api \
  --power nano \
  --scale 1 \
  --region ap-northeast-2

# PostgreSQL 16 Managed Database 생성
aws lightsail create-relational-database \
  --relational-database-name backpackers-db \
  --availability-zone ap-northeast-2a \
  --relational-database-blueprint-id postgres_16 \
  --relational-database-bundle-id micro_2_0 \
  --master-database-name backpackers \
  --master-username backpackers_user \
  --no-publicly-accessible \
  --region ap-northeast-2
```

| 리소스 | 이름 | 플랜 |
|--------|------|------|
| Container Service | backpackers-api | nano |
| Managed Database | backpackers-db | micro_2_0 (PostgreSQL 16) |

### 2-3. 이미지 빌드 & 푸시

```bash
# amd64로 빌드
docker build --platform linux/amd64 -t backpackers-api:amd64 .

# Lightsail 레지스트리에 푸시
aws lightsail push-container-image \
  --region ap-northeast-2 \
  --service-name backpackers-api \
  --label backpackers-api \
  --image backpackers-api:amd64
```

> `lightsailctl` 플러그인 별도 설치 필요: `brew install aws/tap/lightsailctl`

등록된 이미지 태그: `:backpackers-api.backpackers-api.1`

### 2-4. 컨테이너 배포

환경변수 포함 배포 실행:

| 환경변수 | 값 |
|----------|----|
| `DATABASE_URL` | `postgresql+asyncpg://backpackers_user:***@<host>:5432/backpackers` |
| `SECRET_KEY` | (임시값 — 운영 전 교체 필요) |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` |

헬스체크 경로: `GET /health`

### 2-5. Alembic 마이그레이션

Lightsail Managed DB는 외부 접근 기본 차단이므로, 마이그레이션 시 임시 공개 접근 허용 후 실행:

```bash
# 임시 공개 접근 허용
aws lightsail update-relational-database \
  --relational-database-name backpackers-db --publicly-accessible

# 마이그레이션 실행
DATABASE_URL="..." alembic upgrade head

# 공개 접근 재차단
aws lightsail update-relational-database \
  --relational-database-name backpackers-db --no-publicly-accessible
```

> `alembic/env.py` 수정 사항: `%` 문자 포함 URL이 configparser 충돌 발생 → `.replace("%", "%%")` 처리 추가

---

## 현재 인프라 구성

```
AWS 서울 리전 (ap-northeast-2)
├── Lightsail Container Service: backpackers-api
│     └── 환경변수 DATABASE_URL로 내부망 통신
│
└── Lightsail Managed Database: backpackers-db
      ├── PostgreSQL 16
      ├── 외부 접근: 차단
      └── 컨테이너 서비스와 내부 네트워크로 연결
```

---

## 배포 결과

| 항목 | 상태 |
|------|------|
| `GET /health` | `{"status": "ok"}` ✅ |
| `GET /docs` | 200 ✅ |
| DB 마이그레이션 | 완료 ✅ |
| DB 외부 접근 차단 | 완료 ✅ |

---

## 남은 작업 (TODO)

- [ ] `SECRET_KEY` 운영용 강력한 키로 교체 (`openssl rand -hex 32`)
- [ ] `allow_origins=["*"]` → 실제 프론트엔드 도메인으로 교체
- [ ] 커스텀 도메인 연결 (Lightsail → Route 53 또는 외부 DNS)
- [ ] `String` 컬럼 length 지정 및 `server_default` 적용 (DB 모델 개선)
- [ ] CI/CD 파이프라인 구성 (GitHub Actions 등)
