from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.redis_service import is_redis_available

router = APIRouter()


@router.get("/live")
def live() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def ready(response: Response) -> dict:
    db_ok = False
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    redis_ok = is_redis_available()
    overall_ok = db_ok and redis_ok

    if not overall_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ok" if overall_ok else "degraded",
        "database": db_ok,
        "redis": redis_ok,
    }