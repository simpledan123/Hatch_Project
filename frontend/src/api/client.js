const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.detail || "요청에 실패했습니다.");
  }
  return data;
}

export async function createGuestUser(nickname) {
  return request("/api/users/guest", {
    method: "POST",
    body: JSON.stringify({ nickname }),
  });
}

export async function createPet({ userId, name, species }) {
  return request("/api/pets", {
    method: "POST",
    body: JSON.stringify({
      user_id: userId,
      name,
      species,
    }),
  });
}

export async function getPet(petId) {
  return request(`/api/pets/${petId}`);
}

export async function runAction(petId, actionType) {
  return request(`/api/pets/${petId}/actions/${actionType}`, {
    method: "POST",
  });
}
