import logging
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import api_router
from app.core.config import get_settings
from app.db.base import Base
from app.db.session import engine
from app.models import pet, pet_action_log, user  # noqa: F401

settings = get_settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics")


@app.middleware("http")
async def add_request_id_and_log(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
    logging.info(
        "request_id=%s method=%s path=%s status=%s elapsed_ms=%s",
        request_id, request.method, request.url.path, response.status_code, elapsed_ms,
    )
    response.headers["X-Request-ID"] = request_id
    return response


def _migrate_pets_table() -> None:
    new_columns = [
        ("smarts", "INTEGER NOT NULL DEFAULT 50"),
        ("activity", "INTEGER NOT NULL DEFAULT 50"),
        ("life_stage", "VARCHAR(20) NOT NULL DEFAULT 'egg'"),
        ("character_type", "INTEGER NOT NULL DEFAULT 0"),
        ("evolution_form", "VARCHAR(20) NOT NULL DEFAULT 'normal'"),
        ("poop_count", "INTEGER NOT NULL DEFAULT 0"),
        ("feed_tally", "INTEGER NOT NULL DEFAULT 0"),
        ("play_tally", "INTEGER NOT NULL DEFAULT 0"),
        ("study_tally", "INTEGER NOT NULL DEFAULT 0"),
        ("train_tally", "INTEGER NOT NULL DEFAULT 0"),
        ("hatched_at", "TIMESTAMP WITH TIME ZONE"),
    ]
    with engine.connect() as conn:
        for col_name, col_def in new_columns:
            try:
                conn.execute(
                    __import__("sqlalchemy").text(
                        f"ALTER TABLE pets ADD COLUMN IF NOT EXISTS {col_name} {col_def}"
                    )
                )
                conn.commit()
            except Exception:
                conn.rollback()


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    _migrate_pets_table()


@app.get("/")
def root() -> dict:
    return {"message": "Tamagotchi Service API is running"}


app.include_router(api_router, prefix="/api")
