import React, { useState, useEffect, useCallback } from "react";
import { RefreshCw, Wind } from "lucide-react";
import api from "../../utils/api";

export default function WellnessTipCard({ state, score, dark }) {
  const [tip,     setTip]     = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchTip = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/wellness/tip?state=${state}&score=${score}`);
      setTip(res.data);
    } catch {
      setTip({
        icon:  "💡",
        title: "Stay mindful",
        body:  "Take a moment to check in with how you're feeling. Small pauses throughout the day protect your mental energy.",
      });
    } finally {
      setLoading(false);
    }
  }, [state, score]);

  // Fetch on state change (with debounce so we don't spam on every frame)
  useEffect(() => {
    const timer = setTimeout(fetchTip, 2000);
    return () => clearTimeout(timer);
  }, [state]); // eslint-disable-line

  // Initial load
  useEffect(() => { fetchTip(); }, []); // eslint-disable-line

  const urgentBorder = tip?.urgent
    ? "border-red-500/60"
    : dark ? "border-gray-800" : "border-gray-200";

  return (
    <div className={`rounded-2xl p-4 border ${urgentBorder} ${dark ? "bg-gray-900" : "bg-white"} shadow-sm`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-indigo-600/20">
            <Wind size={14} className="text-indigo-400" />
          </div>
          <span className={`text-xs font-semibold ${dark ? "text-gray-300" : "text-gray-600"}`}>
            Wellness tip
          </span>
          {tip?.urgent && (
            <span className="text-xs px-1.5 py-0.5 rounded-full bg-red-500/10 text-red-400 font-medium">
              Urgent
            </span>
          )}
        </div>
        <button
          onClick={fetchTip}
          disabled={loading}
          className={`p-1.5 rounded-lg transition-colors ${loading ? "opacity-40" : ""} ${dark ? "hover:bg-gray-800 text-gray-400" : "hover:bg-gray-100 text-gray-500"}`}>
          <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
        </button>
      </div>

      {tip ? (
        <div>
          <div className="flex items-start gap-2">
            <span className="text-lg leading-none mt-0.5" style={{ fontSize: 18 }}>{tip.icon}</span>
            <div>
              <p className={`text-sm font-medium ${dark ? "text-white" : "text-gray-800"}`}>
                {tip.title}
              </p>
              <p className={`text-xs mt-1 leading-relaxed ${dark ? "text-gray-400" : "text-gray-500"}`}>
                {tip.body}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex gap-2 animate-pulse">
          <div className={`w-6 h-6 rounded-md ${dark ? "bg-gray-800" : "bg-gray-100"}`} />
          <div className="flex-1 space-y-2">
            <div className={`h-3 rounded ${dark ? "bg-gray-800" : "bg-gray-100"} w-3/4`} />
            <div className={`h-3 rounded ${dark ? "bg-gray-800" : "bg-gray-100"} w-full`} />
            <div className={`h-3 rounded ${dark ? "bg-gray-800" : "bg-gray-100"} w-2/3`} />
          </div>
        </div>
      )}
    </div>
  );
}
