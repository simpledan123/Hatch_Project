from fastapi import APIRouter

from app.api.routes import health, pets, users

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
