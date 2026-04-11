from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, camping_spots

app = FastAPI(
    title="Backpackers API",
    description="국립공원·캠핑장 정보 플랫폼 API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(camping_spots.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok"}
