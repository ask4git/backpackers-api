from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import auth, camping_spots

app = FastAPI(
    title="Backpackers API",
    description="국립공원·캠핑장 정보 플랫폼 API",
    version="0.1.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(camping_spots.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "environment": settings.ENVIRONMENT}
