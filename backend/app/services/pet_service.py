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

ActionType = Literal[
    "feed", "clean", "play", "sleep",
    "study", "train", "medicine", "clean_poop",
    "hatch", "graduate",
]

# Life stage thresholds in minutes since hatching
STAGE_THRESHOLDS = {
    "baby": 0,
    "child": 60,
    "teen": 360,
    "adult": 1440,
}


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
        "smarts": pet.smarts,
        "activity": pet.activity,
        "status": pet.status,
        "life_stage": pet.life_stage,
        "evolution_form": pet.evolution_form,
        "poop_count": pet.poop_count,
        "feed_tally": pet.feed_tally,
        "play_tally": pet.play_tally,
        "study_tally": pet.study_tally,
        "train_tally": pet.train_tally,
        "sick_tally": pet.sick_tally,
        "last_decay_at": normalize_dt(pet.last_decay_at).isoformat(),
        "created_at": normalize_dt(pet.created_at).isoformat(),
        "updated_at": normalize_dt(pet.updated_at).isoformat() if pet.updated_at else None,
    }


def refresh_status(pet: Pet) -> None:
    previous_status = pet.status
    if pet.health <= 0:
        pet.health = 0
        pet.status = "dead"
        return

    if pet.health < 30 or pet.hunger > 85 or pet.cleanliness < 20:
        pet.status = "sick"
        if previous_status != "sick":
            pet.sick_tally += 1
    else:
        pet.status = "alive"


def determine_evolution_form(pet: Pet) -> str:
    tallies = {
        "studious": pet.study_tally,
        "athletic": pet.train_tally,
        "cheerful": pet.play_tally,
    }
    highest = max(tallies.values())
    if pet.sick_tally > highest:
        return "wild"
    if highest == 0 or list(tallies.values()).count(highest) > 1:
        return "normal"
    return max(tallies, key=tallies.get)


def refresh_life_stage(pet: Pet) -> None:
    if pet.life_stage in {"egg", "graduated"} or pet.hatched_at is None:
        return

    elapsed_minutes = max(
        0,
        int((utc_now() - normalize_dt(pet.hatched_at)).total_seconds()) // 60,
    )

    if elapsed_minutes >= STAGE_THRESHOLDS["adult"]:
        pet.life_stage = "adult"
        pet.evolution_form = determine_evolution_form(pet)
    elif elapsed_minutes >= STAGE_THRESHOLDS["teen"]:
        pet.life_stage = "teen"
    elif elapsed_minutes >= STAGE_THRESHOLDS["child"]:
        pet.life_stage = "child"
    else:
        pet.life_stage = "baby"


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

    poop_reference = pet.last_poop_at or pet.hatched_at
    new_poops = 0
    if poop_reference is not None:
        poop_elapsed_minutes = max(
            0,
            int((now - normalize_dt(poop_reference)).total_seconds()) // 60,
        )
        new_poops = poop_elapsed_minutes // 180
    if new_poops:
        pet.poop_count = min(3, pet.poop_count + new_poops)
        pet.last_poop_at = normalize_dt(poop_reference) + timedelta(minutes=new_poops * 180)
    if pet.poop_count >= 3:
        pet.health = clamp(pet.health - elapsed_minutes)

    pet.last_decay_at = now
    refresh_status(pet)
    refresh_life_stage(pet)
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
        smarts=pet.smarts,
        activity=pet.activity,
        status=pet.status,
        life_stage=pet.life_stage,
        character_type=pet.character_type,
        evolution_form=pet.evolution_form,
        poop_count=pet.poop_count,
        feed_tally=pet.feed_tally,
        play_tally=pet.play_tally,
        study_tally=pet.study_tally,
        train_tally=pet.train_tally,
        hatched_at=normalize_dt(pet.hatched_at) if pet.hatched_at else None,
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


def write_through_pet_cache(pet_id: int, response: PetStateResponse) -> None:
    """Write-Through 패턴: DB 커밋 직후 캐시를 즉시 최신 상태로 갱신한다.
    캐시를 삭제하지 않고 덮어씌우므로, 동시 요청이 몰려도 캐시 미스가
    연쇄적으로 DB에 전달되는 Cache Stampede를 방지한다.
    """
    try:
        get_redis_client().set(
            get_pet_cache_key(pet_id),
            response.model_dump_json(),
            ex=timedelta(seconds=30),
        )
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
        get_redis_client().set(
            cache_key,
            response.model_dump_json(),
            ex=timedelta(seconds=30),
        )
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
) -> tuple[PetStateResponse, str]:
    pet = get_pet_or_404(db, pet_id)
    apply_decay(pet)

    if pet.status == "dead":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pet is dead")

    enforce_rate_limit(pet_id, action_type)

    before_state = pet_to_dict(pet)

    if action_type == "hatch":
        if pet.life_stage != "egg":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pet is already hatched")
        pet.life_stage = "baby"
        pet.hatched_at = utc_now()
        pet.last_poop_at = pet.hatched_at
        message = "알에서 깨어났어요!"
    elif action_type == "graduate":
        if pet.life_stage != "adult":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only an adult pet can graduate")
        pet.life_stage = "graduated"
        message = "펫을 무사히 보내주었어요."
    elif pet.life_stage == "egg":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Hatch the pet first")
    elif pet.life_stage == "graduated":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pet has graduated")

    elif action_type == "feed":
        pet.hunger = clamp(pet.hunger - 20)
        pet.happiness = clamp(pet.happiness + 3)
        pet.feed_tally += 1
        message = "밥을 맛있게 먹었어요."
    elif action_type == "clean":
        pet.cleanliness = clamp(pet.cleanliness + 25)
        pet.happiness = clamp(pet.happiness - 1)
        message = "몸이 깨끗해졌어요."
    elif action_type == "play":
        pet.happiness = clamp(pet.happiness + 15)
        pet.energy = clamp(pet.energy - 10)
        pet.hunger = clamp(pet.hunger + 5)
        pet.play_tally += 1
        message = "신나게 놀았어요."
    elif action_type == "sleep":
        pet.energy = clamp(pet.energy + 30)
        pet.hunger = clamp(pet.hunger + 8)
        message = "푹 자고 일어났어요."
    elif action_type == "study":
        pet.smarts = clamp(pet.smarts + 10)
        pet.energy = clamp(pet.energy - 8)
        pet.hunger = clamp(pet.hunger + 4)
        pet.study_tally += 1
        message = "공부해서 지능이 올랐어요."
    elif action_type == "train":
        pet.activity = clamp(pet.activity + 10)
        pet.energy = clamp(pet.energy - 12)
        pet.hunger = clamp(pet.hunger + 6)
        pet.train_tally += 1
        message = "운동해서 활동력이 올랐어요."
    elif action_type == "medicine":
        if pet.status != "sick":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pet is not sick")
        pet.health = clamp(pet.health + 30)
        pet.happiness = clamp(pet.happiness - 2)
        message = "약을 먹고 건강을 회복했어요."
    elif action_type == "clean_poop":
        if pet.poop_count == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="There is nothing to clean")
        pet.poop_count = 0
        pet.cleanliness = clamp(pet.cleanliness + 10)
        message = "주변을 깨끗하게 치웠어요."
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

    # Write-Through: 캐시 삭제 대신 즉시 갱신하여 Cache Stampede 방지
    response = build_pet_state_response(pet, cached=False)
    write_through_pet_cache(pet_id, response)
    return response, message
