import { useState, useEffect, useCallback } from "react";
import api from "../utils/api";

/**
 * useSessionHistory – fetches the user's past sessions from the API.
 * @param {number} limit  Max sessions to fetch (default 20)
 */
export function useSessionHistory(limit = 20) {
  const [sessions,  setSessions]  = useState([]);
  const [loading,   setLoading]   = useState(true);
  const [error,     setError]     = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.get(`/api/v1/sessions?limit=${limit}`);
      setSessions(res.data?.sessions || []);
    } catch (e) {
      setError(e.message || "Failed to load sessions");
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => { fetch(); }, [fetch]);

  const deleteSession = useCallback(async (sessionId) => {
    await api.delete(`/api/v1/sessions/${sessionId}`);
    setSessions(prev => prev.filter(s => s.session_id !== sessionId));
  }, []);

  return { sessions, loading, error, refresh: fetch, deleteSession };
}
