---                                                                                                                                                         
  1. 프로젝트 개요                                                                                                                                            
                                                                                                                                                            
  Claude가 이 API의 목적과 도메인을 이해하도록.
  - 목적: 국립공원·캠핑장 정보 제공 플랫폼 (POC)                                                                                                              
  - 스택: FastAPI + PostgreSQL + SQLAlchemy(async) + Alembic                                                                                                  
  - 인증: JWT (python-jose), 패스워드 해싱 (passlib/bcrypt)                                                                                                   
                                                                                                                                                              
  ---                                                                                                                                                         
  2. 아키텍처 레이어 규칙                                                                                                                                   
                                                                                                                                                              
  이 프로젝트는 routers → crud → models 의존 구조를 유지하고 있습니다. Claude가 코드 추가 시 레이어를 섞지 않도록 명시.                                     
  - routers/: HTTP 요청/응답, 의존성 주입만                                                                                                                   
  - crud/: DB 쿼리 로직만 (비즈니스 로직 없음)                                                                                                              
  - schemas/: Pydantic 입출력 모델                                                                                                                            
  - models/: SQLAlchemy ORM 모델                                                                                                                              
  - core/: 설정, DB 연결, 보안 유틸                                                                                                                           
                                                                                                                                                              
  ---                                                                                                                                                         
  3. 개발 환경 실행 방법                                                                                                                                    
                                                                                                                                                              
  Claude가 "어떻게 실행하나요?" 물어보지 않고 바로 쓸 수 있게.                                                                                              
  docker compose up -d          # PostgreSQL 실행                                                                                                             
  alembic upgrade head          # 마이그레이션 적용
  uvicorn app.main:app --reload # 서버 실행                                                                                                                   
                                                                                                                                                              
  ---
  4. 마이그레이션 규칙                                                                                                                                        
                                                                                                                                                            
  모델 변경 시 Claude가 자동으로 마이그레이션 파일을 생성하도록.
  - 모델 변경 시 항상 alembic revision --autogenerate 실행                                                                                                    
  - alembic/versions/ 파일을 직접 수정하지 말 것          
                                                                                                                                                              
  ---                                                                                                                                                         
  5. 코딩 컨벤션                                                                                                                                              
                                                                                                                                                              
  - 에러 메시지는 한국어                                                                                                                                    
  - 비동기(async/await) 패턴 유지                                                                                                                             
  - 새 라우터 추가 시 app/main.py에 include_router 등록                                                                                                       
  - .env 파일의 값을 코드에 하드코딩 금지

  ---
  6. 명령어 실행 규칙

  - 모든 Python 명령은 uv run으로 실행 (예: uv run alembic, uv run pytest)
  - 자주 쓰는 명령은 Makefile로 래핑돼 있으므로 make 명령 우선 사용

  | 작업 | 명령 |
  |------|------|
  | 로컬 서버 실행 | make dev |
  | 마이그레이션 적용 | make migrate |
  | 마이그레이션 생성 | make migrate-create MSG="설명" |
  | 린트 검사 | make lint |
  | 린트 자동 수정 | make lint-fix |
  | 포맷 | make format |
  | 테스트 | make test |

  ---
  7. 환경 구분

  - .env.local: 로컬 개발 (make dev)
  - .env.devel: devel 환경 (make dev-devel / make migrate-devel)
  - .env.prod: prod DB 접근 (make tunnel 먼저 실행 후 make dev-prod / make migrate-prod)

  ---
  8. Git 브랜치 규칙

  - main에 직접 push 금지
  - 브랜치 네이밍: feature/description, fix/description

  ---
  9. 코드 품질

  - 코드 변경 후 반드시 make lint 실행
  - 커밋 전 make format으로 포맷 통일

  ---