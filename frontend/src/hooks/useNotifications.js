import { useEffect, useRef, useCallback } from "react";
import { requestFCMToken, onForegroundMessage } from "../utils/firebase";

const COOLDOWN_MS = 5 * 60 * 1000; // 5 minutes between alerts

/**
 * useNotifications – requests FCM permission, registers token, handles
 * foreground push messages, and triggers local browser notifications
 * based on fatigue score thresholds.
 */
export function useNotifications(fatigueScore, state) {
  const lastAlertRef   = useRef({ state: null, ts: 0 });

  // Request notification permission + FCM token on mount
  useEffect(() => {
    if (!("Notification" in window)) return;
    Notification.requestPermission().then(async (perm) => {
      if (perm === "granted") {
        const token = await requestFCMToken();
        if (token) {
          // Store token in backend / Firestore (optional)
          console.debug("FCM token:", token);
        }
      }
    });
  }, []);

  // Handle foreground FCM messages
  useEffect(() => {
    const unsub = onForegroundMessage((payload) => {
      const { title, body } = payload?.notification || {};
      if (title) {
        new Notification(title, { body, icon: "/logo192.png" });
      }
    });
    return () => typeof unsub === "function" && unsub();
  }, []);

  // Local threshold-based alerts
  const maybeAlert = useCallback(() => {
    if (!("Notification" in window) || Notification.permission !== "granted") return;

    const now  = Date.now();
    const last = lastAlertRef.current;

    if (state === "Fatigued" && fatigueScore >= 65 && last.state !== "Fatigued") {
      if (now - last.ts > COOLDOWN_MS) {
        new Notification("⚠️  High Fatigue Detected – Mentora", {
          body: `Fatigue score: ${fatigueScore.toFixed(0)}/100. Please take a proper break.`,
          icon: "/logo192.png",
        });
        lastAlertRef.current = { state: "Fatigued", ts: now };
      }
    } else if (state === "Stressed" && fatigueScore >= 35 && last.state !== "Stressed") {
      if (now - last.ts > COOLDOWN_MS) {
        new Notification("😤  Stress Building – Mentora", {
          body: `Score: ${fatigueScore.toFixed(0)}/100. Try a 4-7-8 breathing exercise.`,
          icon: "/logo192.png",
        });
        lastAlertRef.current = { state: "Stressed", ts: now };
      }
    } else if (state === "Normal") {
      lastAlertRef.current = { state: "Normal", ts: now };
    }
  }, [fatigueScore, state]);

  useEffect(() => {
    maybeAlert();
  }, [maybeAlert]);
}
