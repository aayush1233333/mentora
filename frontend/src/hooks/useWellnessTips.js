import { useState, useEffect, useCallback } from "react";
import api from "../utils/api";

/**
 * useWellnessTips – fetches a single contextual wellness tip
 * that auto-refreshes when the user's state changes.
 *
 * @param {string} state   - "Normal" | "Stressed" | "Fatigued"
 * @param {number} score   - current fatigue score 0-100
 * @param {number} debounceMs - delay before fetching after state change (default 2000ms)
 */
export function useWellnessTip(state = "Normal", score = 0, debounceMs = 2000) {
  const [tip,     setTip]     = useState(null);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState(null);

  const fetchTip = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/api/v1/wellness/tip?state=${encodeURIComponent(state)}&score=${score}`);
      setTip(res.data);
    } catch (e) {
      setError(e.message);
      // Fallback tip so the UI always has something to show
      setTip({
        icon:  "💡",
        title: "Stay mindful",
        body:  "Check in with how your body feels. Short pauses protect your mental energy over the course of a day.",
        urgent: false,
      });
    } finally {
      setLoading(false);
    }
  }, [state, score]);

  // Debounced auto-refresh on state change
  useEffect(() => {
    const timer = setTimeout(fetchTip, debounceMs);
    return () => clearTimeout(timer);
  }, [state]); // eslint-disable-line react-hooks/exhaustive-deps

  // Immediate first load
  useEffect(() => { fetchTip(); }, []); // eslint-disable-line

  return { tip, loading, error, refresh: fetchTip };
}

/**
 * useWellnessTipsBatch – fetches multiple tips at once for a tips carousel.
 */
export function useWellnessTipsBatch(state = "Normal", n = 3) {
  const [tips,    setTips]    = useState([]);
  const [loading, setLoading] = useState(false);

  const fetch = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/wellness/tips?state=${encodeURIComponent(state)}&n=${n}`);
      setTips(res.data?.tips || []);
    } catch {
      setTips([]);
    } finally {
      setLoading(false);
    }
  }, [state, n]);

  useEffect(() => { fetch(); }, [state]); // eslint-disable-line

  return { tips, loading, refresh: fetch };
}
