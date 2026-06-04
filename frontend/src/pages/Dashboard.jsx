import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { Activity, Eye, Wind, Zap, TrendingUp, Play } from "lucide-react";
import { useSession } from "../context/SessionContext";
import { useTheme } from "../context/ThemeContext";
import FatigueGauge from "../components/dashboard/FatigueGauge";
import PomodoroTimer from "../components/dashboard/PomodoroTimer";
import WellnessTipCard from "../components/dashboard/WellnessTipCard";
import BreathingExercise from "../components/dashboard/BreathingExercise";
import api from "../utils/api";

function StatCard({ icon: Icon, label, value, sub, color = "#6C63FF", dark }) {
  return (
    <div className={`rounded-2xl p-4 border ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
      <div className="flex items-start justify-between">
        <div>
          <p className={`text-xs font-medium ${dark ? "text-gray-400" : "text-gray-500"}`}>{label}</p>
          <p className="text-2xl font-bold mt-1" style={{ color }}>{value}</p>
          {sub && <p className={`text-xs mt-0.5 ${dark ? "text-gray-500" : "text-gray-400"}`}>{sub}</p>}
        </div>
        <div className="p-2 rounded-xl" style={{ background: color + "1a" }}>
          <Icon size={20} style={{ color }} />
        </div>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { fatigueScore, state, ear, mar, blinkCount, yawnCount, active, history } = useSession();
  const { dark } = useTheme();
  const navigate = useNavigate();
  const [weekly, setWeekly] = useState([]);
  const [showBreathing, setShowBreathing] = useState(false);

  useEffect(() => {
    api.get("/reports/weekly").then(r => setWeekly(r.data?.days || [])).catch(() => {});
  }, []);

  // Auto-suggest breathing when stressed/fatigued
  useEffect(() => {
    if (active && fatigueScore >= 35 && !showBreathing) {
      const timer = setTimeout(() => setShowBreathing(true), 3000);
      return () => clearTimeout(timer);
    }
  }, [state, active]); // eslint-disable-line

  const chartData = active
    ? history.slice(-60).map((h, i) => ({ t: i, score: h.score }))
    : weekly.map(d => ({ t: d.date?.slice(5), score: d.avg_fatigue }));

  return (
    <div className={`p-4 md:p-6 min-h-full ${dark ? "text-white" : "text-gray-900"}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className={`text-sm mt-0.5 ${dark ? "text-gray-400" : "text-gray-500"}`}>
            {active ? "Live monitoring active" : "Start a session to begin tracking"}
          </p>
        </div>
        <div className="flex items-center gap-2">
          {active && (
            <button onClick={() => setShowBreathing(b => !b)}
              className={`flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-medium border transition-colors
                ${dark ? "border-gray-700 text-gray-300 hover:bg-gray-800" : "border-gray-200 text-gray-600 hover:bg-gray-50"}`}>
              <Wind size={15} />
              Breathe
            </button>
          )}
          {!active && (
            <button onClick={() => navigate("/monitoring")}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold shadow-sm transition-colors">
              <Play size={16} />
              Start Session
            </button>
          )}
        </div>
      </div>

      {/* Breathing overlay */}
      {showBreathing && (
        <div className="mb-4">
          <BreathingExercise
            onClose={() => setShowBreathing(false)}
            dark={dark}
            autoStart={fatigueScore >= 35}
          />
        </div>
      )}

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-4">
        <div className={`rounded-2xl p-6 border flex flex-col items-center ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
          <h3 className={`text-sm font-semibold mb-4 self-start ${dark ? "text-gray-300" : "text-gray-600"}`}>Fatigue Score</h3>
          <FatigueGauge score={fatigueScore} state={state} size={180} />
          {!active && <p className="text-xs text-gray-400 mt-3">No active session</p>}
        </div>

        <div className={`lg:col-span-2 rounded-2xl p-5 border ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
          <h3 className={`text-sm font-semibold mb-4 ${dark ? "text-gray-300" : "text-gray-600"}`}>
            {active ? "Live Fatigue Timeline" : "Weekly Average Fatigue"}
          </h3>
          <ResponsiveContainer width="100%" height={170}>
            <LineChart data={chartData}>
              <XAxis dataKey="t" tick={{ fontSize: 11, fill: "#94a3b8" }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: "#94a3b8" }} width={28} />
              <Tooltip
                contentStyle={{ background: dark ? "#1e293b" : "#fff", border: "1px solid #334155", borderRadius: 8 }}
                labelStyle={{ color: "#94a3b8" }}
              />
              <ReferenceLine y={35} stroke="#f59e0b" strokeDasharray="4 4"
                label={{ value: "Stress", fill: "#f59e0b", fontSize: 10 }} />
              <ReferenceLine y={65} stroke="#ef4444" strokeDasharray="4 4"
                label={{ value: "Fatigue", fill: "#ef4444", fontSize: 10 }} />
              <Line type="monotone" dataKey="score" stroke="#6C63FF" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <StatCard icon={Eye}      label="Eye Openness (EAR)" value={ear.toFixed(3)}  sub="Normal > 0.22"  color="#6C63FF"  dark={dark} />
        <StatCard icon={Wind}     label="Mouth Ratio (MAR)"  value={mar.toFixed(3)}  sub="Yawn > 0.65"   color="#22d3ee"  dark={dark} />
        <StatCard icon={Activity} label="Blinks"             value={blinkCount}       sub="This session"  color="#10b981"  dark={dark} />
        <StatCard icon={Zap}      label="Yawns"              value={yawnCount}        sub="This session"  color="#f59e0b"  dark={dark} />
      </div>

      {/* Bottom grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <PomodoroTimer dark={dark} />

        {/* Weekly summary */}
        <div className={`rounded-2xl p-5 border ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp size={16} className="text-indigo-400" />
            <h3 className={`text-sm font-semibold ${dark ? "text-gray-300" : "text-gray-600"}`}>This Week</h3>
          </div>
          {weekly.length === 0 ? (
            <p className="text-sm text-gray-400">No data yet. Complete your first session!</p>
          ) : (
            <div className="space-y-2">
              {weekly.slice(-5).map(d => (
                <div key={d.date} className="flex items-center justify-between text-sm">
                  <span className={dark ? "text-gray-400" : "text-gray-500"}>{d.date?.slice(5)}</span>
                  <div className="flex items-center gap-3">
                    <div className="w-28 h-1.5 rounded-full bg-gray-200 dark:bg-gray-700">
                      <div className="h-full rounded-full transition-all"
                        style={{ width: `${d.avg_fatigue}%`, background: d.avg_fatigue >= 65 ? "#ef4444" : d.avg_fatigue >= 35 ? "#f59e0b" : "#10b981" }} />
                    </div>
                    <span className="font-mono text-xs w-8 text-right"
                      style={{ color: d.avg_fatigue >= 65 ? "#ef4444" : d.avg_fatigue >= 35 ? "#f59e0b" : "#10b981" }}>
                      {d.avg_fatigue}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Wellness tip */}
        <WellnessTipCard state={state} score={fatigueScore} dark={dark} />
      </div>
    </div>
  );
}
