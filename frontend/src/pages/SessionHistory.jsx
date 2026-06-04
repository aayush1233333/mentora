import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Download, Trash2, Clock, BarChart2, Calendar, RefreshCw } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { useSessionHistory } from "../hooks/useSessionHistory";
import api from "../utils/api";

function SessionRow({ session, dark, onDelete, onExport }) {
  const started = new Date(session.started_at * 1000);
  const duration = session.ended_at
    ? Math.round((session.ended_at - session.started_at) / 60)
    : null;
  const score = session.avg_fatigue ?? 0;
  const stateColor = score >= 65 ? "#ef4444" : score >= 35 ? "#f59e0b" : "#10b981";
  const stateLabel = score >= 65 ? "Fatigued" : score >= 35 ? "Stressed" : "Normal";

  return (
    <tr className={`border-t group ${dark ? "border-gray-800 hover:bg-gray-800/30" : "border-gray-100 hover:bg-gray-50"} transition-colors`}>
      <td className="px-4 py-3">
        <div className={`text-sm font-medium ${dark ? "text-gray-200" : "text-gray-800"}`}>
          {started.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })}
        </div>
        <div className="text-xs text-gray-400">
          {started.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}
        </div>
      </td>
      <td className="px-4 py-3">
        {duration !== null ? (
          <span className={`text-sm ${dark ? "text-gray-300" : "text-gray-600"}`}>{duration} min</span>
        ) : (
          <span className="text-xs text-gray-400 italic">In progress</span>
        )}
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="w-20 h-1.5 rounded-full bg-gray-200 dark:bg-gray-700">
            <div className="h-full rounded-full" style={{ width: `${score}%`, background: stateColor }} />
          </div>
          <span className="text-sm font-mono font-bold" style={{ color: stateColor }}>{score}</span>
        </div>
      </td>
      <td className="px-4 py-3">
        <span className="text-xs px-2 py-0.5 rounded-full font-medium"
          style={{ background: stateColor + "20", color: stateColor }}>
          {stateLabel}
        </span>
      </td>
      <td className="px-4 py-3">
        <span className={`text-xs font-mono ${dark ? "text-gray-400" : "text-gray-500"}`}>
          {session.frame_count ?? "—"} frames
        </span>
      </td>
      <td className="px-4 py-3">
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button onClick={() => onExport(session.session_id)}
            title="Export PDF"
            className={`p-1.5 rounded-lg ${dark ? "hover:bg-gray-700 text-gray-400" : "hover:bg-gray-200 text-gray-500"} transition-colors`}>
            <Download size={14} />
          </button>
          <button onClick={() => onDelete(session.session_id)}
            title="Delete session"
            className="p-1.5 rounded-lg hover:bg-red-500/20 text-red-400 transition-colors">
            <Trash2 size={14} />
          </button>
        </div>
      </td>
    </tr>
  );
}

export default function SessionHistory() {
  const { dark } = useTheme();
  const { sessions, loading, error, refresh, deleteSession } = useSessionHistory(50);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const navigate = useNavigate();

  const handleExport = async (sessionId) => {
    try {
      const res = await api.get(`/report?session_id=${sessionId}&format=pdf`, { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a");
      a.href = url;
      a.download = `mentora_report_${sessionId.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch { /* show toast in prod */ }
  };

  const handleDelete = async (sessionId) => {
    if (confirmDelete === sessionId) {
      await deleteSession(sessionId);
      setConfirmDelete(null);
    } else {
      setConfirmDelete(sessionId);
      setTimeout(() => setConfirmDelete(null), 3000);
    }
  };

  const totalMinutes = sessions.reduce((a, s) => {
    if (!s.ended_at) return a;
    return a + Math.round((s.ended_at - s.started_at) / 60);
  }, 0);
  const avgScore = sessions.length
    ? Math.round(sessions.reduce((a, s) => a + (s.avg_fatigue ?? 0), 0) / sessions.length)
    : 0;

  return (
    <div className={`p-4 md:p-6 min-h-full ${dark ? "text-white" : "text-gray-900"}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold">Session History</h1>
          <p className={`text-sm mt-0.5 ${dark ? "text-gray-400" : "text-gray-500"}`}>
            All your past monitoring sessions
          </p>
        </div>
        <button onClick={refresh} disabled={loading}
          className={`p-2 rounded-xl border transition-colors ${dark ? "border-gray-700 hover:bg-gray-800 text-gray-400" : "border-gray-200 hover:bg-gray-50 text-gray-500"}`}>
          <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3 mb-6">
        {[
          { icon: Calendar, label: "Total sessions",  value: sessions.length,      color: "#6C63FF" },
          { icon: Clock,    label: "Total focus time", value: `${totalMinutes} min`, color: "#22d3ee" },
          { icon: BarChart2,label: "Avg fatigue score",value: `${avgScore}/100`,    color: avgScore >= 65 ? "#ef4444" : avgScore >= 35 ? "#f59e0b" : "#10b981" },
        ].map(({ icon: Icon, label, value, color }) => (
          <div key={label} className={`rounded-2xl p-4 border ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
            <div className="flex items-center gap-2 mb-1">
              <Icon size={13} style={{ color }} />
              <span className={`text-xs ${dark ? "text-gray-400" : "text-gray-500"}`}>{label}</span>
            </div>
            <p className="text-xl font-bold" style={{ color }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Table */}
      <div className={`rounded-2xl border overflow-hidden ${dark ? "bg-gray-900 border-gray-800" : "bg-white border-gray-200"} shadow-sm`}>
        {loading ? (
          <div className="p-12 text-center">
            <RefreshCw size={24} className="animate-spin text-indigo-400 mx-auto mb-3" />
            <p className="text-sm text-gray-400">Loading sessions…</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center">
            <p className="text-sm text-red-400">{error}</p>
            <button onClick={refresh} className="mt-3 text-sm text-indigo-400 hover:text-indigo-300">Try again</button>
          </div>
        ) : sessions.length === 0 ? (
          <div className="p-12 text-center">
            <BarChart2 size={36} className="mx-auto mb-3 text-gray-300" strokeWidth={1} />
            <p className={`text-sm font-medium ${dark ? "text-gray-300" : "text-gray-600"}`}>No sessions yet</p>
            <p className="text-xs text-gray-400 mt-1 mb-4">Start monitoring to record your first session.</p>
            <button onClick={() => navigate("/monitoring")}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-semibold transition-colors">
              Start Monitoring
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className={dark ? "bg-gray-800/50" : "bg-gray-50"}>
                  {["Date", "Duration", "Avg Score", "State", "Frames", "Actions"].map(h => (
                    <th key={h} className={`px-4 py-3 text-left text-xs font-semibold ${dark ? "text-gray-400" : "text-gray-500"}`}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {sessions.map(s => (
                  <SessionRow key={s.session_id} session={s} dark={dark}
                    onExport={handleExport}
                    onDelete={handleDelete}
                  />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Delete confirmation notice */}
      {confirmDelete && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 px-4 py-3 rounded-xl bg-red-600 text-white text-sm font-medium shadow-xl flex items-center gap-3 z-50">
          <Trash2 size={15} />
          Click delete again to confirm — this cannot be undone
        </div>
      )}
    </div>
  );
}
