import React from "react";

export default function PetStatBar({ label, value }) {
  return (
    <div style={{ marginBottom: "10px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "4px" }}>
        <strong>{label}</strong>
        <span>{value}</span>
      </div>
      <div style={{ background: "#e5e7eb", borderRadius: "8px", height: "12px", overflow: "hidden" }}>
        <div
          style={{
            width: `${Math.max(0, Math.min(100, value))}%`,
            height: "100%",
            background: "#111827",
          }}
        />
      </div>
    </div>
  );
}
