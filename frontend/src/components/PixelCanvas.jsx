import { useEffect, useRef } from "react";
import { PIXEL_SIZE } from "../sprites.js";
 
const LCD_BG = "#8bac6e";
const LCD_DOT = "#7a9d5f";
const PIXEL_COLOR = "#1a1a2e";
 
export default function PixelCanvas({ sprite, scale = 1 }) {
  const canvasRef = useRef(null);
  const ps = Math.round(PIXEL_SIZE * scale);
 
  useEffect(() => {
    if (!sprite || !canvasRef.current) return;
    const rows = sprite.length;
    const cols = sprite[0]?.length ?? 0;
    const canvas = canvasRef.current;
    canvas.width = cols * ps;
    canvas.height = rows * ps;
    const ctx = canvas.getContext("2d");
 
    // Draw LCD dot-matrix background
    ctx.fillStyle = LCD_BG;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (!sprite[r][c]) {
          ctx.fillStyle = LCD_DOT;
          const cx = c * ps + ps / 2;
          const cy = r * ps + ps / 2;
          ctx.beginPath();
          ctx.arc(cx, cy, ps * 0.15, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }
 
    // Draw dark pixels
    ctx.fillStyle = PIXEL_COLOR;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        if (sprite[r][c]) {
          ctx.fillRect(c * ps + 1, r * ps + 1, ps - 1, ps - 1);
        }
      }
    }
  }, [sprite, ps]);
 
  return (
    <canvas
      ref={canvasRef}
      style={{ imageRendering: "pixelated", display: "block" }}
    />
  );
}