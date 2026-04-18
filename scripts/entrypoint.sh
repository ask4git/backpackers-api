#!/bin/bash
set -e

echo "=== Backpackers API Startup ==="

# DB 연결 대기
echo "[1/3] Waiting for database connection..."
uv run python - <<'PYEOF'
import asyncio
import asyncpg
import os
import sys

async def wait_for_db(retries=10, delay=3):
    for attempt in range(1, retries + 1):
        try:
            conn = await asyncpg.connect(
                host=os.environ["DB_HOST"],
                port=int(os.environ.get("DB_PORT", "5432")),
                user=os.environ["DB_USER"],
                password=os.environ["DB_PASSWORD"],
                database=os.environ["DB_NAME"],
            )
            await conn.close()
            print(f"  DB connected (attempt {attempt})")
            return
        except Exception as e:
            print(f"  Attempt {attempt}/{retries} failed: {e}")
            if attempt == retries:
                print("  DB connection failed after all retries")
                sys.exit(1)
            await asyncio.sleep(delay)

asyncio.run(wait_for_db())
PYEOF

# Alembic 마이그레이션
echo "[2/3] Running database migrations..."
uv run alembic upgrade head
echo "  Migrations complete"

# 앱 시작
echo "[3/3] Starting FastAPI application..."
exec uv run uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1
