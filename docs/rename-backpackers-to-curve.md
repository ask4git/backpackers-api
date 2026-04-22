# 프로젝트 이름 변경: backpackers → curve

**작업일**: 2026-04-23  
**브랜치**: `rename/backpackers-to-curve`

---

## 개요

프로젝트 전체에 흩어져 있던 `backpackers` 문자열을 `curve`로 통일했습니다.  
코드·설정·CI 파일 대상이며, 실제 AWS 인프라(RDS DB명, Lightsail 서비스명)는 별도 작업이 필요합니다.

---

## 변경 파일 목록

| 파일 | 변경 내용 |
|------|-----------|
| `pyproject.toml` | `name = "backpackers-api"` → `"curve-api"` |
| `app/main.py` | FastAPI title `"Backpackers API"` → `"Curve API"`, sqladmin title `"Backpackers 어드민"` → `"Curve 어드민"` |
| `Makefile` | `SERVICE_NAME := backpackers-api` → `curve-api`, `IMAGE_TAG := backpackers-api:amd64` → `curve-api:amd64`, deploy 사용법 문구 |
| `.github/workflows/deploy.yml` | `SERVICE_NAME: backpackers-api` → `curve-api` |
| `docker-compose.yml` | `POSTGRES_DB: backpackers` → `curve` (로컬 개발 DB) |
| `alembic.ini` | `sqlalchemy.url` DB명 `backpackers` → `curve` (로컬 마이그레이션용) |
| `scripts/make_deploy_config.py` | containers JSON 키 `"backpackers-api"` → `"curve-api"`, 주석 |
| `.env.local.example` | `DB_NAME=backpackers` → `DB_NAME=curve` |

---

## 미변경 항목 (인프라 수준 — 별도 작업 필요)

### 1. GitHub 레포지토리 이름
현재: `backpackers-api`  
변경 방법: GitHub → Repository → Settings → Repository name → `curve-api`  
> ⚠ 이름 변경 시 기존 clone URL이 redirect되지만, 팀원이 있다면 로컬 remote URL 업데이트 필요

```bash
git remote set-url origin git@github.com:ask4git/curve-api.git
```

### 2. AWS Lightsail 컨테이너 서비스
현재 서비스명: `backpackers-api`  
> Lightsail 컨테이너 서비스는 **이름 변경 불가** — 새 서비스를 생성하고 기존 서비스를 삭제해야 합니다.

절차:
1. AWS 콘솔 → Lightsail → Create container service → 이름: `curve-api`
2. Lightsail Managed DB 동일 리전에 연결
3. `make push`로 이미지 push (SERVICE_NAME=curve-api 이미 반영됨)
4. `make deploy LIGHTSAIL_IMAGE=:curve-api.curve-api.N`
5. 헬스체크 통과 확인 후 기존 `backpackers-api` 서비스 삭제

### 3. RDS 데이터베이스 / 유저
현재: DB명 `backpackers`, 유저 `backpackers_user`  
> 현재 `.env.prod`의 실제 접속 정보이므로 변경 시 운영 중단 발생

변경이 필요한 경우:
1. 새 DB 및 유저 생성 (Lightsail Managed DB 콘솔)
2. `pg_dump` / `pg_restore`로 데이터 이전
3. `.env.prod` 및 GitHub Actions secrets 업데이트
4. Lightsail 배포 환경변수 업데이트

---

## 로컬 환경 재설정 (docker-compose DB명 변경 대응)

`docker-compose.yml`의 `POSTGRES_DB`가 `curve`로 바뀌었으므로,  
기존 로컬 볼륨을 그대로 사용하면 DB를 못 찾을 수 있습니다.

```bash
# 기존 볼륨 삭제 후 재생성
make down        # docker compose down -v
make up          # docker compose up -d
make migrate     # alembic upgrade head
```

> `.env.local`의 `DB_NAME`도 `curve`로 변경 필요 (`.env.local.example` 참고)
