import React, { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "../supabaseClient";

const AuthContext = createContext(null);

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const initializeAuth = async () => {
      const {
        data: { session },
      } = await supabase.auth.getSession();

      if (!mounted) return;

      if (session) {
        setUser(session.user);
        setToken(session.access_token);
      } else {
        setUser(null);
        setToken(null);
      }

      setLoading(false);
    };

    initializeAuth();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) {
        setUser(session.user);
        setToken(session.access_token);
      } else {
        setUser(null);
        setToken(null);
      }

      setLoading(false);
    });

    return () => {
      mounted = false;
      subscription.unsubscribe();
    };
  }, []);

  const login = async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (error) throw error;

    return data;
  };

  const register = async (email, password) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    });

    if (error) throw error;

    return data;
  };

  const loginGoogle = async () => {
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider: "google",
    });

    if (error) throw error;

    return data;
  };

  const logout = async () => {
    const { error } = await supabase.auth.signOut();

    if (error) throw error;
  };

  const getToken = async () => {
    const {
      data: { session },
    } = await supabase.auth.getSession();

    if (!session) {
      setToken(null);
      return null;
    }

    setUser(session.user);
    setToken(session.access_token);

    return session.access_token;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        loginGoogle,
        logout,
        getToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}