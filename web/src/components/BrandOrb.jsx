import { useEffect, useRef } from "react";
import "./BrandOrb.css";

const GLYPH = [
  "0111110",
  "1100000",
  "1100000",
  "0111110",
  "0000011",
  "0000011",
  "0111110",
];

function logoPoints() {
  const points = [];
  const rows = GLYPH.length;
  const cols = GLYPH[0].length;
  for (let row = 0; row < rows; row += 1) {
    for (let col = 0; col < cols; col += 1) {
      if (GLYPH[row][col] === "1") {
        points.push({
          x: (col / (cols - 1) - 0.5) * 1.3,
          y: (row / (rows - 1) - 0.5) * 1.3,
          phase: (row * cols + col) * 0.19,
        });
      }
    }
  }
  return points;
}

function spherePoints() {
  const points = [];
  const steps = 15;
  for (let row = 0; row < steps; row += 1) {
    const y = (row / (steps - 1)) * 2 - 1;
    const radius = Math.sqrt(Math.max(0, 1 - y * y));
    for (let col = 0; col < steps; col += 1) {
      const angle = (col / steps) * Math.PI * 2 + (row % 2) * 0.13;
      points.push({
        x: Math.cos(angle) * radius,
        y,
        z: Math.sin(angle) * radius,
      });
    }
  }
  return points;
}

const LOGO_POINTS = logoPoints();
const SPHERE_POINTS = spherePoints();

export default function BrandOrb({
  className = "",
  label = "DevOps Sentinel activity",
  size = "medium",
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return undefined;
    const context = canvas.getContext("2d");
    if (!context) return undefined;

    let frame = 0;
    let visible = true;
    let width = 0;
    let height = 0;
    let dpr = 1;
    let pulse = 0;
    let pointer = { x: 0, y: 0, active: false };
    let targetPointer = { x: 0, y: 0, active: false };
    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const observer = new IntersectionObserver(([entry]) => {
      visible = entry?.isIntersecting ?? true;
    });

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      width = Math.max(1, rect.width);
      height = Math.max(1, rect.height);
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const setPointer = (event) => {
      const rect = canvas.getBoundingClientRect();
      targetPointer = {
        x: ((event.clientX - rect.left) / rect.width - 0.5) * 2,
        y: ((event.clientY - rect.top) / rect.height - 0.5) * 2,
        active: true,
      };
    };
    const leave = () => {
      targetPointer = { ...targetPointer, active: false };
    };
    const click = () => {
      pulse = 1;
    };

    const draw = (time) => {
      if (!visible) {
        frame = requestAnimationFrame(draw);
        return;
      }
      const t = time / 1000;
      const motion = reducedMotion.matches ? 0 : t;
      pointer.x += (targetPointer.x - pointer.x) * 0.08;
      pointer.y += (targetPointer.y - pointer.y) * 0.08;
      pointer.active = targetPointer.active;
      pulse *= reducedMotion.matches ? 0.82 : 0.94;
      context.clearRect(0, 0, width, height);

      const radius = Math.min(width, height) * 0.34;
      const cx = width / 2;
      const cy = height / 2;
      const glow = context.createRadialGradient(
        cx,
        cy,
        radius * 0.15,
        cx,
        cy,
        radius * 1.35,
      );
      glow.addColorStop(0, "rgba(140, 255, 155, 0.16)");
      glow.addColorStop(0.55, "rgba(75, 185, 122, 0.07)");
      glow.addColorStop(1, "rgba(5, 7, 8, 0)");
      context.fillStyle = glow;
      context.fillRect(0, 0, width, height);

      const rotation = motion * 0.42 + pointer.x * 0.25;
      for (const point of SPHERE_POINTS) {
        const angle = Math.atan2(point.z, point.x) + rotation;
        const x =
          Math.cos(angle) * Math.sqrt(point.x * point.x + point.z * point.z);
        const z =
          Math.sin(angle) * Math.sqrt(point.x * point.x + point.z * point.z);
        const depth = (z + 1) / 2;
        const wobble = Math.sin(motion * 2 + point.y * 4) * 0.012;
        const px = cx + (x + pointer.x * 0.045) * radius;
        const py = cy + (point.y + wobble + pointer.y * 0.045) * radius;
        const dot = Math.max(0.7, 1.05 + depth * 1.65);
        context.globalAlpha = 0.08 + depth * 0.42;
        context.fillStyle = depth > 0.66 ? "#c6ffd0" : "#56b878";
        context.beginPath();
        context.arc(px, py, dot, 0, Math.PI * 2);
        context.fill();
      }

      for (const point of LOGO_POINTS) {
        const drift = Math.sin(motion * 2.4 + point.phase) * 0.018;
        const px = cx + (point.x + pointer.x * 0.08) * radius;
        const py = cy + (point.y + drift + pointer.y * 0.08) * radius;
        const dot = 2.1 + pulse * 1.4;
        context.globalAlpha = 0.74 + Math.sin(motion * 2 + point.phase) * 0.12;
        context.fillStyle = "#d8ffdc";
        context.shadowColor = "rgba(140, 255, 155, 0.9)";
        context.shadowBlur = 7 + pulse * 8;
        context.beginPath();
        context.arc(px, py, dot, 0, Math.PI * 2);
        context.fill();
        context.shadowBlur = 0;
      }
      context.globalAlpha = 1;
      frame = requestAnimationFrame(draw);
    };

    observer.observe(canvas);
    resize();
    window.addEventListener("resize", resize);
    canvas.addEventListener("pointermove", setPointer);
    canvas.addEventListener("pointerleave", leave);
    canvas.addEventListener("click", click);
    frame = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("resize", resize);
      canvas.removeEventListener("pointermove", setPointer);
      canvas.removeEventListener("pointerleave", leave);
      canvas.removeEventListener("click", click);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={`brand-orb brand-orb-${size} ${className}`.trim()}
      role="img"
      aria-label={label}
    />
  );
}
