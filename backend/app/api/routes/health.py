from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import SessionLocal
from app.services.redis_service import is_redis_available

router = APIRouter()


@router.get("/live")
def live() -> dict:
    return {"status": "ok"}


@router.get("/ready")
def ready() -> dict:
    db_ok = False
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    redis_ok = is_redis_available()
    return {
        "status": "ok" if db_ok and redis_ok else "degraded",
        "database": db_ok,
        "redis": redis_ok,
    }
