"use client";

import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import {
  ApiError,
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

// Whether this browser might hold a session. The refresh cookie is httpOnly *and*
// belongs to the API's origin, so client JavaScript cannot see it — and asking
// anyway costs a guaranteed 401 on every anonymous page load. This is only a
// hint: `null` means "not asked yet", so a first visit still probes once, and a
// definitive 401 records "0" so later visits stay quiet.
const SESSION_HINT_KEY = "nordvik.session";
const SESSION_HINT_NONE = "0";
const SESSION_HINT_PRESENT = "1";

function readSessionHint(): string | null {
  try {
    return window.localStorage.getItem(SESSION_HINT_KEY);
  } catch {
    return null; // Storage unavailable — probe rather than assume signed out.
  }
}

function writeSessionHint(hint: string): void {
  try {
    window.localStorage.setItem(SESSION_HINT_KEY, hint);
  } catch {
    // Storage unavailable; the next load simply probes again.
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  const applyAccessToken = useCallback(async (token: string) => {
    writeSessionHint(SESSION_HINT_PRESENT);
    setAccessToken(token);
    setUser(await fetchMe(token));
  }, []);

  useEffect(() => {
    let active = true;

    // The hint check sits inside the async body so the effect never calls
    // setState synchronously (`react-hooks/set-state-in-effect`).
    const restoreSession = async () => {
      if (readSessionHint() === SESSION_HINT_NONE) {
        return null; // Asked before; this browser had no session then.
      }
      const tokens = await refreshSession();
      if (tokens === null) {
        writeSessionHint(SESSION_HINT_NONE);
        return null; // The API answered 204: this browser has no session.
      }
      const me = await fetchMe(tokens.access_token);
      writeSessionHint(SESSION_HINT_PRESENT);
      return { tokens, me };
    };

    restoreSession()
      .then((session) => {
        if (!active || session === null) return;
        setAccessToken(session.tokens.access_token);
        setUser(session.me);
      })
      .catch((error: unknown) => {
        // Only a definitive 401 means the session is gone. A network blip must
        // not clear the hint, or a flaky connection would sign the user out of
        // the UI on the next load.
        if (error instanceof ApiError && error.status === 401) {
          writeSessionHint(SESSION_HINT_NONE);
        }
      })
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
    writeSessionHint(SESSION_HINT_NONE);
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
