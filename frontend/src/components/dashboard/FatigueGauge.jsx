import React from "react";

const STATE_COLORS = {
  Normal:   { stroke: "#10b981", glow: "0 0 20px #10b98166", label: "text-emerald-400" },
  Stressed: { stroke: "#f59e0b", glow: "0 0 20px #f59e0b66", label: "text-amber-400"   },
  Fatigued: { stroke: "#ef4444", glow: "0 0 20px #ef444466", label: "text-red-400"     },
  Unknown:  { stroke: "#6b7280", glow: "none",                label: "text-gray-400"    },
};

/**
 * FatigueGauge – animated SVG arc gauge
 * @param {number} score   0-100
 * @param {string} state   Normal | Stressed | Fatigued | Unknown
 * @param {number} size    diameter in px (default 200)
 */
export default function FatigueGauge({ score = 0, state = "Normal", size = 200 }) {
  const { stroke, glow } = STATE_COLORS[state] || STATE_COLORS.Unknown;

  const r   = (size / 2) * 0.78;
  const cx  = size / 2;
  const cy  = size / 2;
  const circumference = 2 * Math.PI * r;
  // Arc goes from -225° to 45° (270° sweep)
  const sweep    = 0.75;  // fraction of circle used
  const progress = Math.min(score, 100) / 100;
  const dashArr  = circumference * sweep;
  const dashOff  = dashArr * (1 - progress);

  return (
    <div className="relative flex flex-col items-center">
      <svg width={size} height={size} style={{ filter: `drop-shadow(${glow})` }}>
        {/* Background track */}
        <circle cx={cx} cy={cy} r={r}
          fill="none" stroke="#1e293b" strokeWidth={size * 0.07}
          strokeDasharray={`${circumference * sweep} ${circumference}`}
          strokeDashoffset={-circumference * 0.125}
          strokeLinecap="round"
          transform={`rotate(-225 ${cx} ${cy})`}
        />
        {/* Foreground arc */}
        <circle cx={cx} cy={cy} r={r}
          fill="none" stroke={stroke} strokeWidth={size * 0.07}
          strokeDasharray={`${dashArr} ${circumference}`}
          strokeDashoffset={dashOff - circumference * 0.125 * 0}
          strokeLinecap="round"
          transform={`rotate(-225 ${cx} ${cy})`}
          style={{ transition: "stroke-dashoffset 0.6s cubic-bezier(0.4,0,0.2,1), stroke 0.6s" }}
        />
        {/* Score text */}
        <text x={cx} y={cy - 6} textAnchor="middle"
          fontSize={size * 0.22} fontWeight="700" fill={stroke}
          style={{ transition: "fill 0.6s" }}>
          {Math.round(score)}
        </text>
        <text x={cx} y={cy + size * 0.12} textAnchor="middle"
          fontSize={size * 0.075} fill="#94a3b8">
          /100
        </text>
        <text x={cx} y={cy + size * 0.22} textAnchor="middle"
          fontSize={size * 0.085} fontWeight="600" fill={stroke}
          style={{ transition: "fill 0.6s" }}>
          {state}
        </text>
      </svg>
    </div>
  );
}
