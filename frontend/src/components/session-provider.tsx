"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  useSyncExternalStore,
  type ReactNode,
} from "react";

import { logout as endSession, renewSession } from "@/api/auth";
import { getSession, subscribeToSession, type SessionUser } from "@/lib/session";

/**
 * The session as React sees it (`US-2.3`).
 *
 * The state itself lives in `lib/session.ts`; this reads it through `useSyncExternalStore` so a
 * sign-in or sign-out re-renders the header without the token being copied into component state,
 * where it would drift.
 *
 * Three states rather than two, because "no token yet" and "no session" are different things on
 * first paint. The access token only exists in memory, so a reload always begins without one — while
 * the refresh cookie is still there and a new token is on its way. Without `restoring`, the header
 * would flash "Sign in" at a customer who is signed in, on every navigation.
 */

export type SessionStatus = "restoring" | "authenticated" | "anonymous";

export type SessionValue = {
  status: SessionStatus;
  user: SessionUser | null;
  signOut: () => Promise<void>;
};

const SessionContext = createContext<SessionValue | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const session = useSyncExternalStore(subscribeToSession, getSession, getSession);
  const [restoring, setRestoring] = useState(true);

  useEffect(() => {
    // The silent refresh. It shares a single-flight gate with every retry in `lib/session.ts`, so a
    // page that also makes a protected call during load cannot produce two refreshes — and two
    // refreshes would look like a stolen token to the API and end every session for the account.
    let active = true;
    void (async () => {
      await renewSession();
      if (active) setRestoring(false);
    })();
    return () => {
      active = false;
    };
  }, []);

  const signOut = useCallback(async () => {
    await endSession();
  }, []);

  const value = useMemo<SessionValue>(
    () => ({
      status: session ? "authenticated" : restoring ? "restoring" : "anonymous",
      user: session?.user ?? null,
      signOut,
    }),
    [session, restoring, signOut],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession(): SessionValue {
  const value = useContext(SessionContext);
  if (value === null) {
    throw new Error("useSession() was called outside <SessionProvider>.");
  }
  return value;
}
