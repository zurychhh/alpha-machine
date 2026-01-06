from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.endpoints import health, market, sentiment, data, signals, backtest, telegram, learning

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["health"])
app.include_router(market.router, prefix=f"{settings.API_V1_STR}/market", tags=["market"])
app.include_router(sentiment.router, prefix=f"{settings.API_V1_STR}/sentiment", tags=["sentiment"])
app.include_router(data.router, prefix=f"{settings.API_V1_STR}/data", tags=["data"])
app.include_router(signals.router, prefix=f"{settings.API_V1_STR}/signals", tags=["signals"])
app.include_router(backtest.router, prefix=f"{settings.API_V1_STR}/backtest", tags=["backtest"])
app.include_router(telegram.router, prefix=f"{settings.API_V1_STR}/telegram", tags=["telegram"])
app.include_router(learning.router, prefix=f"{settings.API_V1_STR}/learning", tags=["learning"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {"name": settings.PROJECT_NAME, "version": settings.VERSION, "docs": "/docs"}
