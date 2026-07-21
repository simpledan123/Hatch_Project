import time

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_hatch_and_care_actions(client):
    nickname = f"test-user-{time.time_ns()}"
    user_response = client.post("/api/users/guest", json={"nickname": nickname})
    assert user_response.status_code == 201

    pet_response = client.post(
        "/api/pets",
        json={"user_id": user_response.json()["id"], "name": "알", "species": "tama"},
    )
    assert pet_response.status_code == 201
    pet_id = pet_response.json()["id"]

    hatch_response = client.post(f"/api/pets/{pet_id}/actions/hatch")
    assert hatch_response.status_code == 200
    assert hatch_response.json()["pet"]["life_stage"] == "baby"

    study_response = client.post(f"/api/pets/{pet_id}/actions/study")
    assert study_response.status_code == 200
    assert study_response.json()["pet"]["smarts"] == 60
    assert study_response.json()["pet"]["study_tally"] == 1

    train_response = client.post(f"/api/pets/{pet_id}/actions/train")
    assert train_response.status_code == 200
    assert train_response.json()["pet"]["activity"] == 60
    assert train_response.json()["pet"]["train_tally"] == 1

    for action in ("feed", "clean", "play", "sleep"):
        action_response = client.post(f"/api/pets/{pet_id}/actions/{action}")
        assert action_response.status_code == 200
        assert action_response.json()["action_type"] == action


def test_care_action_requires_hatching(client):
    nickname = f"test-user-{time.time_ns()}"
    user_response = client.post("/api/users/guest", json={"nickname": nickname})
    pet_response = client.post(
        "/api/pets",
        json={"user_id": user_response.json()["id"], "name": "알", "species": "tama"},
    )

    response = client.post(f"/api/pets/{pet_response.json()['id']}/actions/feed")
    assert response.status_code == 400
    assert response.json()["detail"] == "Hatch the pet first"
