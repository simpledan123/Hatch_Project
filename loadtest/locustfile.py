import random
import time

from locust import HttpUser, between, task


CARE_ACTIONS = ("feed", "clean", "play", "sleep", "study", "train")


class HatchUser(HttpUser):
    """각 가상 사용자가 자신의 펫을 만든 뒤 조회와 케어 요청을 반복한다."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        suffix = f"{time.time_ns()}-{random.randint(1000, 9999)}"
        user_response = self.client.post(
            "/api/users/guest",
            json={"nickname": f"load-user-{suffix}"},
            name="POST /api/users/guest [setup]",
        )
        user_response.raise_for_status()

        pet_response = self.client.post(
            "/api/pets",
            json={
                "user_id": user_response.json()["id"],
                "name": f"load-pet-{suffix}",
                "species": "tama",
            },
            name="POST /api/pets [setup]",
        )
        pet_response.raise_for_status()
        self.pet_id = pet_response.json()["id"]

        hatch_response = self.client.post(
            f"/api/pets/{self.pet_id}/actions/hatch",
            name="POST /api/pets/:id/actions/hatch [setup]",
        )
        hatch_response.raise_for_status()

    @task(3)
    def read_pet_state(self) -> None:
        self.client.get(
            f"/api/pets/{self.pet_id}",
            name="GET /api/pets/:id",
        )

    @task(2)
    def perform_care_action(self) -> None:
        action = random.choice(CARE_ACTIONS)
        self.client.post(
            f"/api/pets/{self.pet_id}/actions/{action}",
            name="POST /api/pets/:id/actions/:action",
        )
