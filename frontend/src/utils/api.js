import axios from "axios";
import { auth } from "./firebase";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1",
  timeout: 15000,
});

api.interceptors.request.use(async (config) => {
  const user = auth.currentUser;
  if (user) {
    const token = await user.getIdToken();
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (r) => r,
  async (err) => {
    const original = err.config;

    // Only attempt a refresh-and-retry once per request, and only on 401.
    if (err.response?.status === 401 && !original?._retriedAfterRefresh) {
      original._retriedAfterRefresh = true;

      // auth.currentUser can be momentarily null during the Firebase auth
      // state initialization race (before onAuthStateChanged fires), even
      // though the user is actually still logged in. Don't redirect to
      // login on that basis alone — try a forced token refresh first.
      if (auth.currentUser) {
        try {
          const freshToken = await auth.currentUser.getIdToken(true);
          original.headers.Authorization = `Bearer ${freshToken}`;
          return api.request(original);
        } catch {
          // Refresh itself failed — fall through to redirect below.
        }
      }

      // No user, or refresh failed: this is a genuine auth failure.
      window.location.href = "/login";
    }

    return Promise.reject(err);
  }
);

export default api;
