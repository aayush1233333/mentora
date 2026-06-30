import React, { createContext, useContext, useReducer, useRef } from "react";
import api from "../utils/api";
import { auth } from "../utils/firebase";

const SessionContext = createContext(null);
export const useSession = () => useContext(SessionContext);

const init = {
  sessionId:    null,
  active:       false,
  fatigueScore: 0,
  state:        "Normal",
  ear:          0,
  mar:          0,
  headPitch:    0,
  headYaw:      0,
  blinkCount:   0,
  yawnCount:    0,
  history:      [],   // [{t, score, state}]
  wsRef:        null,
};

function reducer(s, { type, payload }) {
  switch (type) {
    case "START":  return { ...s, ...payload, active: true, history: [] };
    case "FRAME":  return {
      ...s,
      fatigueScore: payload.fatigue_score,
      state:        payload.state,
      ear:          payload.ear,
      mar:          payload.mar,
      headPitch:    payload.head_pitch ?? 0,
      headYaw:      payload.head_yaw ?? 0,
      blinkCount:   payload.blink_count,
      yawnCount:    payload.yawn_count,
      history: [...s.history.slice(-299), { t: Date.now(), score: payload.fatigue_score, state: payload.state }],
    };
    case "END":    return { ...init };
    default:       return s;
  }
}

export function SessionProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, init);
  const wsRef = useRef(null);

  const startSession = async () => {
    const res = await api.post("/start-session", {});
    const { session_id } = res.data;
    dispatch({ type: "START", payload: { sessionId: session_id } });

    // ── Open WebSocket with Firebase ID token for authentication ─────────────
    // The backend expects: ws://host/ws/{session_id}?token=<firebase-id-token>
    // We fetch a fresh token here so it isn't stale by the time the server
    // verifies it. Falls back to an empty string in dev (stub auth active).
    let token = "";
    try {
      if (auth.currentUser) {
        token = await auth.currentUser.getIdToken();
      }
    } catch (e) {
      console.warn("Could not fetch ID token for WebSocket auth:", e);
    }

    const baseWsUrl = process.env.REACT_APP_WS_URL || "ws://localhost:8000";
    const wsUrl = `${baseWsUrl}/ws/${session_id}?token=${encodeURIComponent(token)}`;
    wsRef.current = new WebSocket(wsUrl);
    wsRef.current.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "frame_result") dispatch({ type: "FRAME", payload: data });
    };
    wsRef.current.onerror = (e) => {
      console.error("WebSocket error:", e);
    };
    return session_id;
  };

  const sendFrame = async (b64, sessionId) => {
    try {
      const res = await api.post("/process-frame", {
        session_id: sessionId || state.sessionId,
        frame_b64:  b64,
        timestamp:  Date.now() / 1000,
      });
      dispatch({ type: "FRAME", payload: res.data });
      return res.data;
    } catch { return null; }
  };

  const endSession = async () => {
    if (wsRef.current) wsRef.current.close();
    if (state.sessionId) await api.post("/end-session", { session_id: state.sessionId });
    dispatch({ type: "END" });
  };

  return (
    <SessionContext.Provider value={{ ...state, startSession, sendFrame, endSession }}>
      {children}
    </SessionContext.Provider>
  );
}
