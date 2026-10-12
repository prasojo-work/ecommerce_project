"use client";

import Link from "next/link";

import { CartLink } from "./cart-link";
import { useSession } from "@/components/session-provider";

/**
 * The site header, and the only place the session becomes visible (`US-2.3`).
 *
 * It exists because a sign-in with no way back to an account screen is not demonstrable, and because
 * the session store needed a consumer rather than a promise that one would arrive. `UX.md` section 3
 * puts the account entry in the header, so this is where it goes.
 *
 * The three session states matter here more than anywhere else. On a reload the access token is gone
 * and a new one is on its way, so during that moment the header shows neither "Sign in" nor the
 * account — it holds the row's height and stays quiet. Showing "Sign in" would flash at a signed-in
 * customer, and showing the account would be a lie for the same instant.
 *
 * The cart entry sits beside the account one and reads the same three states, which is why the nav
 * is labelled for both rather than for the account alone.
 */
export function SiteHeader() {
  const { status, user, signOut } = useSession();

  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-6 py-4">
        <Link href="/" className="text-lg tracking-tight text-ink">
          LYSHEIM
        </Link>

        <nav aria-label="Account and cart" className="flex items-center gap-4 text-sm">
          <CartLink />
          {status === "restoring" ? (
            <span className="inline-block h-5 min-w-40" aria-hidden="true" />
          ) : status === "authenticated" && user !== null ? (
            <>
              {/* The account entry `UX.md` section 3 asks for, and the only way to reach `/account`
                  without typing the URL. */}
              <Link href="/account" className="inline-flex min-h-11 items-center">
                {user.display_name || user.email}
              </Link>
              <button
                type="button"
                onClick={() => void signOut()}
                className="min-h-11 text-primary underline"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/login" className="inline-flex min-h-11 items-center">
                Sign in
              </Link>
              <Link href="/register" className="inline-flex min-h-11 items-center">
                Create an account
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
