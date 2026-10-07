"use client";

import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import {
  type CurrentUser,
  fetchMe,
  loginUser,
  logoutUser,
  refreshSession,
  registerUser,
} from "@/lib/api";

export type AuthState = {
  user: CurrentUser | null;
  accessToken: string | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  const applyAccessToken = useCallback(async (token: string) => {
    setAccessToken(token);
    setUser(await fetchMe(token));
  }, []);

  useEffect(() => {
    let active = true;
    refreshSession()
      .then(async (tokens) => {
        const me = await fetchMe(tokens.access_token);
        if (!active) return;
        setAccessToken(tokens.access_token);
        setUser(me);
      })
      .catch(() => undefined)
      .finally(() => {
        if (active) setReady(true);
      });
    return () => {
      active = false;
    };
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await loginUser({ email, password });
      await applyAccessToken(tokens.access_token);
    },
    [applyAccessToken],
  );

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      const tokens = await registerUser({ email, password, full_name: fullName });
      await applyAccessToken(tokens.access_token);
    },
    [applyAccessToken],
  );

  const logout = useCallback(async () => {
    await logoutUser();
    setAccessToken(null);
    setUser(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({ user, accessToken, ready, login, register, logout }),
    [user, accessToken, ready, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
