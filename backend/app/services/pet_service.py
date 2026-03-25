from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy.orm import Session

from app.models.pet import Pet
from app.models.pet_action_log import PetActionLog
from app.schemas.pet import PetStateResponse
from app.services.redis_service import get_redis_client

ActionType = Literal["feed", "clean", "play", "sleep"]


def clamp(value: int, minimum: int = 0, maximum: int = 100) -> int:
    return max(minimum, min(value, maximum))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_dt(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def pet_to_dict(pet: Pet) -> dict:
    return {
        "id": pet.id,
        "user_id": pet.user_id,
        "name": pet.name,
        "species": pet.species,
        "hunger": pet.hunger,
        "cleanliness": pet.cleanliness,
        "happiness": pet.happiness,
        "energy": pet.energy,
        "health": pet.health,
        "status": pet.status,
        "last_decay_at": normalize_dt(pet.last_decay_at).isoformat(),
        "created_at": normalize_dt(pet.created_at).isoformat(),
        "updated_at": normalize_dt(pet.updated_at).isoformat() if pet.updated_at else None,
    }


def refresh_status(pet: Pet) -> None:
    if pet.health <= 0:
        pet.health = 0
        pet.status = "dead"
        return

    if pet.health < 30 or pet.hunger > 85 or pet.cleanliness < 20:
        pet.status = "sick"
    else:
        pet.status = "alive"


def apply_decay(pet: Pet) -> Pet:
    if pet.status == "dead":
        return pet

    now = utc_now()
    last_decay_at = normalize_dt(pet.last_decay_at)
    elapsed_seconds = max(0, int((now - last_decay_at).total_seconds()))
    elapsed_minutes = elapsed_seconds // 60

    if elapsed_minutes <= 0:
        return pet

    pet.hunger = clamp(pet.hunger + elapsed_minutes * 2)
    pet.cleanliness = clamp(pet.cleanliness - elapsed_minutes)
    pet.energy = clamp(pet.energy - elapsed_minutes)
    pet.happiness = clamp(pet.happiness - (elapsed_minutes // 2))

    if pet.hunger >= 90:
        pet.health = clamp(pet.health - elapsed_minutes * 2)
    if pet.cleanliness <= 10:
        pet.health = clamp(pet.health - elapsed_minutes)
    if pet.energy <= 5:
        pet.health = clamp(pet.health - elapsed_minutes)

    pet.last_decay_at = now
    refresh_status(pet)
    return pet


def build_pet_state_response(pet: Pet, *, cached: bool = False) -> PetStateResponse:
    return PetStateResponse(
        id=pet.id,
        user_id=pet.user_id,
        name=pet.name,
        species=pet.species,
        hunger=pet.hunger,
        cleanliness=pet.cleanliness,
        happiness=pet.happiness,
        energy=pet.energy,
        health=pet.health,
        status=pet.status,
        last_decay_at=normalize_dt(pet.last_decay_at),
        created_at=normalize_dt(pet.created_at),
        updated_at=normalize_dt(pet.updated_at) if pet.updated_at else None,
        cached=cached,
    )


def get_pet_or_404(db: Session, pet_id: int) -> Pet:
    pet = db.get(Pet, pet_id)
    if not pet:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pet not found")
    return pet


def get_pet_cache_key(pet_id: int) -> str:
    return f"pet:state:{pet_id}"


def invalidate_pet_cache(pet_id: int) -> None:
    try:
        get_redis_client().delete(get_pet_cache_key(pet_id))
    except RedisError:
        pass


def get_pet_state(db: Session, pet_id: int) -> PetStateResponse:
    cache_key = get_pet_cache_key(pet_id)

    try:
        cached_json = get_redis_client().get(cache_key)
        if cached_json:
            return PetStateResponse.model_validate_json(cached_json).model_copy(update={"cached": True})
    except RedisError:
        pass

    pet = get_pet_or_404(db, pet_id)
    apply_decay(pet)
    db.add(pet)
    db.commit()
    db.refresh(pet)

    response = build_pet_state_response(pet, cached=False)

    try:
        get_redis_client().setex(cache_key, timedelta(seconds=30), response.model_dump_json())
    except RedisError:
        pass

    return response


def enforce_rate_limit(pet_id: int, action_type: ActionType) -> None:
    key = f"rl:pet:{pet_id}:action:{action_type}"
    redis_client = get_redis_client()

    try:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, 10)
        if count > 3:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many repeated actions. Please wait a few seconds.",
            )
    except RedisError:
        # Redis unavailable 시 서비스 자체는 계속 동작
        return


def perform_action(
    db: Session,
    pet_id: int,
    action_type: ActionType,
    request_id: str,
) -> PetStateResponse:
    pet = get_pet_or_404(db, pet_id)
    apply_decay(pet)

    if pet.status == "dead":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pet is dead")

    enforce_rate_limit(pet_id, action_type)

    before_state = pet_to_dict(pet)

    if action_type == "feed":
        pet.hunger = clamp(pet.hunger - 20)
        pet.happiness = clamp(pet.happiness + 3)
    elif action_type == "clean":
        pet.cleanliness = clamp(pet.cleanliness + 25)
        pet.happiness = clamp(pet.happiness - 1)
    elif action_type == "play":
        pet.happiness = clamp(pet.happiness + 15)
        pet.energy = clamp(pet.energy - 10)
        pet.hunger = clamp(pet.hunger + 5)
    elif action_type == "sleep":
        pet.energy = clamp(pet.energy + 30)
        pet.hunger = clamp(pet.hunger + 8)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid action")

    refresh_status(pet)

    after_state = pet_to_dict(pet)
    db.add(
        PetActionLog(
            pet_id=pet.id,
            action_type=action_type,
            before_state_json=before_state,
            after_state_json=after_state,
            request_id=request_id,
        )
    )
    db.add(pet)
    db.commit()
    db.refresh(pet)

    invalidate_pet_cache(pet_id)
    return build_pet_state_response(pet)
