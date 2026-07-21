import React, { useState, useEffect, useCallback, useRef } from "react";
import { createGuestUser, createPet, getPet, runAction, renamePet } from "./api/client.js";
import PixelCanvas from "./components/PixelCanvas.jsx";
import { getSprite, SPRITES, POOP, CHAR_NAMES, EVOLUTION_NAMES, STAGE_NAMES } from "./sprites.js";

const LCD_GREEN = "#8bac6e";
const LCD_DARK = "#0f380f";
const LCD_MID = "#306230";
const LCD_BORDER = "#5a7a3a";
const FONT = "'Courier New', monospace";

const FOOD_MENU = [
  { label: "사과", icon: "🍎", action: "feed" },
  { label: "빵", icon: "🍞", action: "feed" },
  { label: "버거", icon: "🍔", action: "feed" },
  { label: "케이크", icon: "🍰", action: "feed" },
  { label: "아이스크림", icon: "🍦", action: "feed" },
  { label: "닭다리", icon: "🍗", action: "feed" },
];

const ACTION_ICONS = [
  { id: "food", icon: "🍽️", label: "밥", type: "submenu" },
  { id: "clean", icon: "🛁", label: "씻기", type: "action", action: "clean" },
  { id: "study", icon: "📖", label: "공부", type: "action", action: "study" },
  { id: "train", icon: "⚾", label: "운동", type: "action", action: "train" },
  { id: "play", icon: "💡", label: "놀기", type: "action", action: "play" },
  { id: "medicine", icon: "💊", label: "약", type: "action", action: "medicine" },
  { id: "info", icon: "ℹ️", label: "정보", type: "info" },
];

function StatBar({ label, value }) {
  const filled = Math.round((value / 100) * 8);
  return (
    <div style={{ textAlign: "center", fontSize: 9, color: LCD_DARK, fontFamily: FONT }}>
      <div style={{ fontSize: 8, letterSpacing: 0.5, marginBottom: 2 }}>{label}</div>
      <div style={{ display: "flex", gap: 1, justifyContent: "center" }}>
        {Array.from({ length: 8 }, (_, i) => (
          <div
            key={i}
            style={{
              width: 5,
              height: 5,
              background: i < filled ? LCD_DARK : "transparent",
              border: `1px solid ${LCD_DARK}`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

function LcdScreen({ children, style }) {
  return (
    <div
      style={{
        background: LCD_GREEN,
        border: `3px solid ${LCD_MID}`,
        borderRadius: 4,
        padding: "10px 6px",
        position: "relative",
        ...style,
      }}
    >
      {children}
    </div>
  );
}

function PixelBtn({ onClick, disabled, children, style }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      style={{
        background: "#ccc",
        border: "2px solid #555",
        borderRadius: 6,
        padding: "4px 10px",
        fontFamily: FONT,
        fontSize: 12,
        cursor: disabled ? "not-allowed" : "pointer",
        opacity: disabled ? 0.5 : 1,
        ...style,
      }}
    >
      {children}
    </button>
  );
}

function WelcomeScreen({ onStart }) {
  const [nickname, setNickname] = useState("");
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
      <div style={{ fontFamily: FONT, fontSize: 14, color: LCD_DARK, fontWeight: "bold" }}>
        HATCH
      </div>
      <div style={{ fontFamily: FONT, fontSize: 10, color: LCD_MID }}>
        닉네임을 입력하세요
      </div>
      <input
        value={nickname}
        onChange={(e) => setNickname(e.target.value)}
        placeholder="닉네임"
        style={{
          background: LCD_GREEN,
          border: `1px solid ${LCD_DARK}`,
          padding: "4px 8px",
          fontFamily: FONT,
          fontSize: 12,
          color: LCD_DARK,
          width: 140,
          textAlign: "center",
        }}
      />
      <PixelBtn onClick={() => onStart(nickname)} disabled={!nickname.trim()}>
        시작
      </PixelBtn>
    </div>
  );
}

function EggScreen({ pet, onHatch, loading }) {
  const [cracking, setCracking] = useState(false);

  function handleTap() {
    if (loading || cracking) return;
    setCracking(true);
    setTimeout(() => {
      onHatch();
      setCracking(false);
    }, 600);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8 }}>
      <div
        style={{
          fontFamily: FONT,
          fontSize: 15,
          color: LCD_DARK,
          fontWeight: "bold",
          letterSpacing: 1,
        }}
      >
        Tap to Hatch
      </div>
      <div
        onClick={handleTap}
        style={{ cursor: "pointer", transform: cracking ? "scale(1.05)" : "scale(1)", transition: "transform 0.1s" }}
      >
        <PixelCanvas sprite={cracking ? SPRITES.egg_crack : SPRITES.egg} scale={2.8} />
      </div>
    </div>
  );
}

function NamingScreen({ pet, onName }) {
  const [name, setName] = useState("");
  const charName = CHAR_NAMES[pet.character_type] ?? "친구";
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
      <PixelCanvas sprite={getSprite(pet)} scale={2} />
      <div style={{ fontFamily: FONT, fontSize: 11, color: LCD_DARK, textAlign: "center" }}>
        {charName}이(가) 태어났어요!<br />이름을 지어주세요
      </div>
      <input
        value={name}
        onChange={(e) => setName(e.target.value)}
        maxLength={10}
        placeholder="이름"
        style={{
          background: LCD_GREEN,
          border: `1px solid ${LCD_DARK}`,
          padding: "4px 8px",
          fontFamily: FONT,
          fontSize: 13,
          color: LCD_DARK,
          width: 130,
          textAlign: "center",
        }}
      />
      <PixelBtn onClick={() => onName(name)} disabled={!name.trim()}>
        확인
      </PixelBtn>
    </div>
  );
}

function GraduateScreen({ pet, onNewGame }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
      <div style={{ fontFamily: FONT, fontSize: 13, color: LCD_DARK, fontWeight: "bold" }}>
        잘 자랐어요!
      </div>
      <PixelCanvas sprite={getSprite(pet)} scale={2} />
      <div style={{ fontFamily: FONT, fontSize: 10, color: LCD_MID, textAlign: "center", lineHeight: 1.6 }}>
        {pet.name} ({EVOLUTION_NAMES[pet.evolution_form] ?? pet.evolution_form})<br />
        행복하게 살아줘!
      </div>
      <PixelBtn onClick={onNewGame}>새 게임</PixelBtn>
    </div>
  );
}

function DeadScreen({ pet, onNewGame }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 10 }}>
      <div style={{ fontFamily: FONT, fontSize: 11, color: LCD_DARK, fontWeight: "bold" }}>
        무지개 다리...
      </div>
      <div style={{ fontSize: 32 }}>💀</div>
      <div style={{ fontFamily: FONT, fontSize: 10, color: LCD_MID, textAlign: "center" }}>
        {pet.name}이(가) 하늘나라로 갔어요.
      </div>
      <PixelBtn onClick={onNewGame}>새 게임</PixelBtn>
    </div>
  );
}

function GameScreen({ pet, onAction, loading, message, onGraduate }) {
  const [subMenu, setSubMenu] = useState(null);

  const isSick = pet.status === "sick";
  const hasPoops = pet.poop_count > 0;
  const isAdult = pet.life_stage === "adult";

  const visibleActions = ACTION_ICONS.filter((a) => {
    if (a.id === "medicine") return isSick;
    return true;
  });

  function handleActionBtn(item) {
    if (item.type === "submenu") setSubMenu(item.id);
    else if (item.type === "action") onAction(item.action);
    else if (item.type === "info") setSubMenu("info");
  }

  const poopSprites = Array.from({ length: Math.min(pet.poop_count, 3) });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(6, 1fr)",
          gap: 2,
          borderBottom: `2px solid ${LCD_MID}`,
          paddingBottom: 6,
          marginBottom: 6,
        }}
      >
        <StatBar label="배고픔" value={100 - pet.hunger} />
        <StatBar label="청결" value={pet.cleanliness} />
        <StatBar label="지능" value={pet.smarts} />
        <StatBar label="활동" value={pet.activity} />
        <StatBar label="에너지" value={pet.energy} />
        <StatBar label="행복" value={pet.happiness} />
      </div>

      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "flex-end",
          gap: 8,
          minHeight: 100,
          padding: "4px 0 8px",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 2, alignSelf: "flex-end" }}>
          {poopSprites.map((_, i) => (
            <PixelCanvas key={i} sprite={POOP} scale={1.2} />
          ))}
        </div>

        <div style={{ position: "relative" }}>
          {isSick && (
            <div
              style={{
                position: "absolute",
                top: -18,
                left: "50%",
                transform: "translateX(-50%)",
                fontFamily: FONT,
                fontSize: 9,
                color: LCD_DARK,
                background: LCD_GREEN,
                padding: "1px 4px",
                border: `1px solid ${LCD_DARK}`,
                whiteSpace: "nowrap",
              }}
            >
              아파요...
            </div>
          )}
          <PixelCanvas sprite={getSprite(pet)} scale={2.2} />
          <div style={{ textAlign: "center", fontFamily: FONT, fontSize: 9, color: LCD_DARK, marginTop: 2 }}>
            {pet.name} · {STAGE_NAMES[pet.life_stage] ?? pet.life_stage}
          </div>
        </div>

        {isAdult && (
          <div style={{ alignSelf: "flex-end", marginBottom: 4 }}>
            <PixelBtn onClick={onGraduate} disabled={loading} style={{ fontSize: 9, padding: "2px 6px" }}>
              보내기
            </PixelBtn>
          </div>
        )}
      </div>

      <div
        style={{
          fontFamily: FONT,
          fontSize: 9,
          color: LCD_MID,
          textAlign: "center",
          minHeight: 14,
          marginBottom: 4,
          borderTop: `1px solid ${LCD_BORDER}`,
          paddingTop: 3,
        }}
      >
        {message}
      </div>

      {subMenu === "food" && (
        <div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: 4,
              borderTop: `1px solid ${LCD_BORDER}`,
              paddingTop: 6,
            }}
          >
            {FOOD_MENU.map((f) => (
              <button
                key={f.label}
                onClick={() => { onAction(f.action); setSubMenu(null); }}
                disabled={loading}
                style={{
                  background: "transparent",
                  border: `1px solid ${LCD_DARK}`,
                  borderRadius: 3,
                  padding: "4px 2px",
                  fontFamily: FONT,
                  fontSize: 11,
                  cursor: "pointer",
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 2,
                  color: LCD_DARK,
                }}
              >
                <span style={{ fontSize: 16 }}>{f.icon}</span>
                <span style={{ fontSize: 8 }}>{f.label}</span>
              </button>
            ))}
          </div>
          <div style={{ textAlign: "center", marginTop: 4 }}>
            <PixelBtn onClick={() => setSubMenu(null)} style={{ fontSize: 9, padding: "2px 8px" }}>
              취소
            </PixelBtn>
          </div>
        </div>
      )}

      {subMenu === "info" && (
        <div
          style={{
            borderTop: `1px solid ${LCD_BORDER}`,
            paddingTop: 6,
            fontFamily: FONT,
            fontSize: 9,
            color: LCD_DARK,
            lineHeight: 1.8,
          }}
        >
          <div>종류: {CHAR_NAMES[pet.character_type]}</div>
          <div>단계: {STAGE_NAMES[pet.life_stage]}</div>
          <div>형태: {EVOLUTION_NAMES[pet.evolution_form] ?? "-"}</div>
          <div>💩 {pet.poop_count}개</div>
          <div style={{ marginTop: 4 }}>
            공부 {pet.study_tally} · 운동 {pet.train_tally} · 놀기 {pet.play_tally}
          </div>
          {hasPoops && (
            <div style={{ marginTop: 4 }}>
              <PixelBtn
                onClick={() => { onAction("clean_poop"); setSubMenu(null); }}
                disabled={loading}
                style={{ fontSize: 9, padding: "2px 8px" }}
              >
                💩 치우기
              </PixelBtn>
            </div>
          )}
          <div style={{ textAlign: "center", marginTop: 4 }}>
            <PixelBtn onClick={() => setSubMenu(null)} style={{ fontSize: 9, padding: "2px 8px" }}>
              닫기
            </PixelBtn>
          </div>
        </div>
      )}

      {!subMenu && (
        <div
          style={{
            display: "flex",
            justifyContent: "space-around",
            borderTop: `2px solid ${LCD_MID}`,
            paddingTop: 6,
            marginTop: 2,
          }}
        >
          {visibleActions.map((item) => (
            <button
              key={item.id}
              onClick={() => handleActionBtn(item)}
              disabled={loading}
              title={item.label}
              style={{
                background: "transparent",
                border: "none",
                cursor: loading ? "not-allowed" : "pointer",
                fontSize: 18,
                padding: "2px 4px",
                opacity: loading ? 0.5 : 1,
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 1,
              }}
            >
              <span>{item.icon}</span>
              <span style={{ fontFamily: FONT, fontSize: 7, color: LCD_DARK }}>{item.label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function App() {
  const [screen, setScreen] = useState("welcome");
  const [user, setUser] = useState(null);
  const [pet, setPet] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const pollRef = useRef(null);

  useEffect(() => {
    if (screen !== "game" || !pet) return;
    pollRef.current = setInterval(async () => {
      try {
        const latest = await getPet(pet.id);
        setPet(latest);
        if (latest.status === "dead") {
          setScreen("dead");
          clearInterval(pollRef.current);
        }
      } catch (_) {}
    }, 30000);
    return () => clearInterval(pollRef.current);
  }, [screen, pet?.id]);

  async function handleStart(nickname) {
    setLoading(true);
    try {
      const u = await createGuestUser(nickname || "트레이너");
      setUser(u);
      const p = await createPet({ userId: u.id, name: "알", species: "tama" });
      setPet(p);
      setScreen("egg");
    } catch (e) {
      setMessage(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleHatch() {
    if (!pet) return;
    setLoading(true);
    try {
      const res = await runAction(pet.id, "hatch");
      setPet(res.pet);
      setMessage(res.message);
      setScreen("naming");
    } catch (e) {
      setMessage(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleName(name) {
    if (!pet) return;
    setLoading(true);
    try {
      const updated = await renamePet(pet.id, name);
      setPet(updated);
      setScreen("game");
      setMessage(`${name}이(가) 세상에 나왔어요!`);
    } catch (e) {
      setPet((prev) => ({ ...prev, name }));
      setScreen("game");
      setMessage(`${name}이(가) 세상에 나왔어요!`);
    } finally {
      setLoading(false);
    }
  }

  async function handleAction(actionType) {
    if (!pet || loading) return;
    setLoading(true);
    try {
      const res = await runAction(pet.id, actionType);
      setPet(res.pet);
      setMessage(res.message);
      if (res.pet.status === "dead") setScreen("dead");
    } catch (e) {
      setMessage(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGraduate() {
    if (!pet || loading) return;
    setLoading(true);
    try {
      const res = await runAction(pet.id, "graduate");
      setPet(res.pet);
      setMessage(res.message);
      setScreen("graduate");
    } catch (e) {
      setMessage(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleNewGame() {
    if (!user) { setScreen("welcome"); return; }
    setLoading(true);
    try {
      const p = await createPet({ userId: user.id, name: "알", species: "tama" });
      setPet(p);
      setScreen("egg");
      setMessage("");
    } catch (e) {
      setMessage(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#4a6741",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
      }}
    >
      <div
        style={{
          width: 260,
          background: "#c8c8b4",
          borderRadius: 24,
          padding: "16px 12px 20px",
          boxShadow: "0 8px 32px rgba(0,0,0,0.5), inset 0 2px 4px rgba(255,255,255,0.3)",
          border: "3px solid #9a9a88",
        }}
      >
        <LcdScreen style={{ marginBottom: 12 }}>
          {screen === "welcome" && <WelcomeScreen onStart={handleStart} />}
          {screen === "egg" && pet && <EggScreen pet={pet} onHatch={handleHatch} loading={loading} />}
          {screen === "naming" && pet && <NamingScreen pet={pet} onName={handleName} />}
          {screen === "game" && pet && (
            <GameScreen
              pet={pet}
              onAction={handleAction}
              loading={loading}
              message={message}
              onGraduate={handleGraduate}
            />
          )}
          {screen === "graduate" && pet && <GraduateScreen pet={pet} onNewGame={handleNewGame} />}
          {screen === "dead" && pet && <DeadScreen pet={pet} onNewGame={handleNewGame} />}
        </LcdScreen>

        <div style={{ display: "flex", justifyContent: "center", gap: 10, marginTop: 6 }}>
          <button
            onClick={() => { if (screen === "game") handleAction("sleep"); }}
            style={{
              width: 32, height: 32, borderRadius: "50%",
              background: "#888", border: "2px solid #555",
              cursor: "pointer", fontFamily: FONT, fontSize: 9, color: "#fff",
            }}
          >
            ZZ
          </button>
          {screen === "egg" && (
            <button
              onClick={handleHatch}
              disabled={loading}
              style={{
                padding: "6px 18px", borderRadius: 6,
                background: "#666", border: "2px solid #333",
                color: "#fff", fontFamily: FONT, fontSize: 11, cursor: "pointer",
              }}
            >
              SELECT
            </button>
          )}
          {screen === "game" && pet?.poop_count > 0 && (
            <button
              onClick={() => handleAction("clean_poop")}
              disabled={loading}
              style={{
                padding: "6px 10px", borderRadius: 6,
                background: "#666", border: "2px solid #333",
                color: "#fff", fontFamily: FONT, fontSize: 10, cursor: "pointer",
              }}
            >
              💩치우기
            </button>
          )}
        </div>

        <div style={{ display: "flex", justifyContent: "center", marginTop: 8 }}>
          <div
            style={{
              width: 8, height: 8, borderRadius: "50%",
              background: loading ? "#fbbf24" : pet?.status === "sick" ? "#ef4444" : "#22c55e",
              boxShadow: `0 0 6px ${loading ? "#fbbf24" : pet?.status === "sick" ? "#ef4444" : "#22c55e"}`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
