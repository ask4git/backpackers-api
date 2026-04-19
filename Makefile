# =============================================================================
# Backpackers API - Makefile
# =============================================================================

.PHONY: help dev dev-prod up down logs shell \
        tunnel tunnel-close \
        migrate migrate-down migrate-create migrate-history migrate-current \
        migrate-prod \
        lint lint-fix format test \
        build push deploy status ls-logs images secret-gen

SERVICE_NAME  := backpackers-api
REGION        := ap-northeast-2
IMAGE_TAG     := backpackers-api:amd64
PLATFORM      := linux/amd64

help:           ## 사용 가능한 명령어 목록 출력
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'

# ── 로컬 개발 ─────────────────────────────────────────────────────────────────

BASTION_IP     := 43.203.210.117
BASTION_KEY    ?= ~/.ssh/backpackers-api-lightsail-bastion-ssh-key.pem

dev:            ## 로컬에서 uvicorn 직접 실행 (hot reload, .env.local)
	@test -f .env.local || (echo "Error: .env.local 없음. .env.local.example 참고" && exit 1)
	ENV_FILE=.env.local uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-devel:      ## devel 환경으로 로컬 서버 실행 (.env.devel)
	@test -f .env.devel || (echo "Error: .env.devel 없음" && exit 1)
	ENV_FILE=.env.devel uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-prod:       ## prod DB에 연결해서 로컬 서버 실행 (.env.prod, make tunnel 먼저 실행)
	@test -f .env.prod || (echo "Error: .env.prod 없음. .env.prod.example 참고" && exit 1)
	ENV_FILE=.env.prod uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# ── SSH 터널 (prod DB) ────────────────────────────────────────────────────────

PROD_DB_REMOTE_PORT := 5432  # RDS 실제 포트 (고정)

tunnel:         ## SSH 터널 열기 (백그라운드, prod DB → localhost)
	@test -f .env.prod || (echo "Error: .env.prod 없음. .env.prod.example 참고" && exit 1)
	$(eval RDS_HOST := $(shell grep '^RDS_HOST=' .env.prod | cut -d= -f2 | tr -d '[:space:]'))
	$(eval PROD_DB_PORT := $(shell grep '^DB_PORT=' .env.prod | cut -d= -f2 | tr -d '[:space:]'))
	@test -n "$(RDS_HOST)" || (echo "Error: .env.prod에 RDS_HOST가 없습니다." && exit 1)
	@echo "터널 열기: localhost:$(PROD_DB_PORT) → $(RDS_HOST):$(PROD_DB_REMOTE_PORT)"
	ssh -i $(BASTION_KEY) -L $(PROD_DB_PORT):$(RDS_HOST):$(PROD_DB_REMOTE_PORT) ubuntu@$(BASTION_IP) -N -f
	@echo "터널 열림. 종료: make tunnel-close"

tunnel-close:   ## SSH 터널 종료
	@pkill -f "ssh.*5435" && echo "터널 종료됨" || echo "실행 중인 터널 없음"

up:             ## docker-compose로 DB + API 실행 (마이그레이션 포함)
	docker compose up -d
	@echo "API: http://localhost:8000"
	@echo "Docs: http://localhost:8000/docs"

down:           ## docker-compose 정지 및 볼륨 제거
	docker compose down -v

logs:           ## docker-compose API 로그 실시간 출력
	docker compose logs -f api

shell:          ## 실행 중인 API 컨테이너에 bash 접속
	docker compose exec api bash

# ── DB 마이그레이션 ───────────────────────────────────────────────────────────

migrate:        ## alembic upgrade head 실행 (.env.local 기준)
	@test -f .env.local || (echo "Error: .env.local 없음. .env.local.example 참고" && exit 1)
	ENV_FILE=.env.local uv run alembic upgrade head

migrate-down:   ## alembic downgrade -1 (한 단계 롤백)
	uv run alembic downgrade -1

migrate-create: ## 새 마이그레이션 파일 생성 (make migrate-create MSG="설명")
	@test -n "$(MSG)" || (echo "Usage: make migrate-create MSG='description'" && exit 1)
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate-history: ## 마이그레이션 히스토리 조회
	uv run alembic history --verbose

migrate-current: ## 현재 적용된 마이그레이션 버전 확인
	uv run alembic current

migrate-devel:  ## devel DB에 alembic upgrade head 실행
	@test -f .env.devel || (echo "Error: .env.devel 없음" && exit 1)
	ENV_FILE=.env.devel uv run alembic upgrade head

migrate-prod:   ## prod DB에 alembic upgrade head 실행 (make tunnel 먼저 실행)
	@test -f .env.prod || (echo "Error: .env.prod 없음. .env.prod.example 참고" && exit 1)
	ENV_FILE=.env.prod uv run alembic upgrade head

# ── 코드 품질 ─────────────────────────────────────────────────────────────────

lint:           ## ruff로 린트 검사
	uv run ruff check app/ alembic/

lint-fix:       ## ruff로 자동 수정
	uv run ruff check --fix app/ alembic/

format:         ## ruff format으로 코드 포맷
	uv run ruff format app/ alembic/

test:           ## pytest 실행
	uv run pytest -v

# ── 빌드 & 배포 ───────────────────────────────────────────────────────────────

build:          ## linux/amd64 Docker 이미지 빌드
	docker build --platform $(PLATFORM) -t $(IMAGE_TAG) .
	@echo "Build complete: $(IMAGE_TAG)"

push: build     ## Lightsail에 이미지 push (build 포함)
	@echo "Pushing $(IMAGE_TAG) to Lightsail..."
	aws lightsail push-container-image \
	  --region $(REGION) \
	  --service-name $(SERVICE_NAME) \
	  --label $(SERVICE_NAME) \
	  --image $(IMAGE_TAG)
	@echo ""
	@echo "Push complete. 위에 출력된 이미지 태그를 확인하세요."
	@echo "배포: make deploy LIGHTSAIL_IMAGE=':$(SERVICE_NAME).$(SERVICE_NAME).N'"

deploy:         ## Lightsail 배포 실행 (LIGHTSAIL_IMAGE 환경변수 필요)
	@test -n "$(LIGHTSAIL_IMAGE)" || \
	  (echo "Usage: make deploy LIGHTSAIL_IMAGE=':backpackers-api.backpackers-api.N'" && exit 1)
	@test -f .env || (echo "Error: .env 파일이 없습니다." && exit 1)
	@echo "Deploying $(LIGHTSAIL_IMAGE) to $(SERVICE_NAME)..."
	@CONTAINERS=$$(uv run python scripts/make_deploy_config.py "$(LIGHTSAIL_IMAGE)") && \
	aws lightsail create-container-service-deployment \
	  --region $(REGION) \
	  --service-name $(SERVICE_NAME) \
	  --containers "$$CONTAINERS" \
	  --public-endpoint '{"containerName":"$(SERVICE_NAME)","containerPort":8000,"healthCheck":{"path":"/health","intervalSeconds":10,"timeoutSeconds":5,"successCodes":"200","unhealthyThreshold":2,"healthyThreshold":2}}'
	@echo "배포 요청 완료. 'make status'로 상태를 확인하세요."

status:         ## Lightsail 서비스 상태 및 최신 배포 확인
	@echo "=== Container Service Status ==="
	@aws lightsail get-container-services \
	  --region $(REGION) \
	  --service-name $(SERVICE_NAME) \
	  --query 'containerServices[0].{State:state,URL:url,Scale:scale}' \
	  --output table
	@echo ""
	@echo "=== Latest Deployment ==="
	@aws lightsail get-container-service-deployments \
	  --region $(REGION) \
	  --service-name $(SERVICE_NAME) \
	  --query 'deployments[0].{State:state,Created:createdAt,Version:version}' \
	  --output table

ls-logs:        ## Lightsail 컨테이너 최근 로그 조회 (최근 100줄)
	aws lightsail get-container-log \
	  --region $(REGION) \
	  --service-name $(SERVICE_NAME) \
	  --container-name $(SERVICE_NAME) \
	  --output json \
	| jq -r '.logEvents[] | "\(.createdAt) \(.message)"' | tail -100

images:         ## Lightsail에 등록된 이미지 목록
	aws lightsail get-container-images \
	  --region $(REGION) \
	  --service-name $(SERVICE_NAME) \
	  --query 'containerImages[*].{Image:image,Created:createdAt}' \
	  --output table

secret-gen:     ## 안전한 SECRET_KEY 생성
	@echo "New SECRET_KEY:"
	@openssl rand -hex 32
