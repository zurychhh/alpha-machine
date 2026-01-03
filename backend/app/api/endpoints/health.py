from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
import redis
from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    Verifies database and Redis connectivity.
    """
    health_status = {"status": "healthy", "database": "unknown", "redis": "unknown"}

    # Check database
    try:
        db.execute(text("SELECT 1"))
        health_status["database"] = "connected"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Check Redis
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        health_status["redis"] = "connected"
    except Exception as e:
        health_status["redis"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    return health_status
