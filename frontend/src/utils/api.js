import axios from "axios";
import { supabase } from "../supabaseClient";

const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || "http://localhost:8000/api/v1",
  timeout: 15000,
});

api.interceptors.request.use(async (config) => {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (err) => {
    const original = err.config;

    // Only attempt a refresh-and-retry once per request, and only on 401.
    if (err.response?.status === 401 && !original?._retriedAfterRefresh) {
      original._retriedAfterRefresh = true;

      try {
        const { data, error } = await supabase.auth.refreshSession();

        if (!error && data.session?.access_token) {
          original.headers.Authorization = `Bearer ${data.session.access_token}`;
          return api.request(original);
        }
      } catch {
        // Refresh failed - fall through to redirect below.
      }

      // Genuine authentication failure.
      window.location.href = "/login";
    }

    return Promise.reject(err);
  }
);

export default api;
