import React, { useState } from "react";
import { createGuestUser, createPet, getPet, runAction } from "./api/client.js";
import PetStatBar from "./components/PetStatBar.jsx";

const actions = ["feed", "clean", "play", "sleep"];

export default function App() {
  const [nickname, setNickname] = useState("");
  const [user, setUser] = useState(null);
  const [petName, setPetName] = useState("테스트1");
  const [species, setSpecies] = useState("tama");
  const [pet, setPet] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("서비스를 시작해보세요.");
  const [error, setError] = useState("");

  async function handleCreateUser() {
    setLoading(true);
    setError("");
    try {
      const createdUser = await createGuestUser(nickname);
      setUser(createdUser);
      setMessage(`게스트 사용자 생성 완료: ${createdUser.nickname}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleCreatePet() {
    if (!user) return;
    setLoading(true);
    setError("");
    try {
      const createdPet = await createPet({
        userId: user.id,
        name: petName,
        species,
      });
      setPet(createdPet);
      setMessage(`펫 생성 완료: ${createdPet.name}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function refreshPet() {
    if (!pet) return;
    setLoading(true);
    setError("");
    try {
      const latestPet = await getPet(pet.id);
      setPet(latestPet);
      setMessage(latestPet.cached ? "캐시된 상태를 불러왔습니다." : "최신 상태를 불러왔습니다.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleAction(actionType) {
    if (!pet) return;
    setLoading(true);
    setError("");
    try {
      const result = await runAction(pet.id, actionType);
      setPet(result.pet);
      setMessage(result.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f9fafb",
        color: "#111827",
        padding: "40px 20px",
        fontFamily: "Arial, sans-serif",
      }}
    >
      <div
        style={{
          maxWidth: "760px",
          margin: "0 auto",
          background: "white",
          borderRadius: "20px",
          padding: "28px",
          boxShadow: "0 12px 32px rgba(0,0,0,0.08)",
        }}
      >
        <h1 style={{ marginTop: 0 }}>Tamagotchi Service MVP</h1>
        <p style={{ lineHeight: 1.6 }}>
          테스트 프로젝트
        </p>

        <section style={{ marginTop: "28px" }}>
          <h2>1. 게스트 사용자 생성</h2>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <input
              value={nickname}
              onChange={(e) => setNickname(e.target.value)}
              placeholder="닉네임 입력"
              style={{ padding: "10px 12px", minWidth: "220px", borderRadius: "10px", border: "1px solid #d1d5db" }}
            />
            <button
              onClick={handleCreateUser}
              disabled={loading || !nickname.trim()}
              style={{ padding: "10px 16px", borderRadius: "10px", border: "none", cursor: "pointer" }}
            >
              사용자 생성
            </button>
          </div>
          {user && <p>현재 사용자: {user.nickname} (ID: {user.id})</p>}
        </section>

        <section style={{ marginTop: "28px" }}>
          <h2>2. 펫 생성</h2>
          <div style={{ display: "flex", gap: "12px", flexWrap: "wrap" }}>
            <input
              value={petName}
              onChange={(e) => setPetName(e.target.value)}
              placeholder="펫 이름"
              style={{ padding: "10px 12px", minWidth: "180px", borderRadius: "10px", border: "1px solid #d1d5db" }}
            />
            <input
              value={species}
              onChange={(e) => setSpecies(e.target.value)}
              placeholder="종류"
              style={{ padding: "10px 12px", minWidth: "140px", borderRadius: "10px", border: "1px solid #d1d5db" }}
            />
            <button
              onClick={handleCreatePet}
              disabled={loading || !user}
              style={{ padding: "10px 16px", borderRadius: "10px", border: "none", cursor: "pointer" }}
            >
              펫 생성
            </button>
          </div>
        </section>

        <section style={{ marginTop: "28px" }}>
          <h2>3. 펫 상태</h2>
          {!pet ? (
            <p>아직 펫이 없습니다.</p>
          ) : (
            <div style={{ border: "1px solid #e5e7eb", borderRadius: "16px", padding: "20px" }}>
              <p><strong>{pet.name}</strong> / {pet.species}</p>
              <p>상태: {pet.status}</p>
              <PetStatBar label="배고픔" value={pet.hunger} />
              <PetStatBar label="청결도" value={pet.cleanliness} />
              <PetStatBar label="행복도" value={pet.happiness} />
              <PetStatBar label="에너지" value={pet.energy} />
              <PetStatBar label="건강" value={pet.health} />

              <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", marginTop: "16px" }}>
                <button onClick={refreshPet} disabled={loading} style={{ padding: "10px 14px", borderRadius: "10px", border: "none", cursor: "pointer" }}>
                  상태 새로고침
                </button>
                {actions.map((action) => (
                  <button
                    key={action}
                    onClick={() => handleAction(action)}
                    disabled={loading}
                    style={{ padding: "10px 14px", borderRadius: "10px", border: "none", cursor: "pointer" }}
                  >
                    {action}
                  </button>
                ))}
              </div>
            </div>
          )}
        </section>

        <section style={{ marginTop: "24px" }}>
          <h2>4. 상태 메시지</h2>
          <p>{message}</p>
          {error && <p style={{ color: "#b91c1c" }}>{error}</p>}
        </section>
      </div>
    </div>
  );
}
