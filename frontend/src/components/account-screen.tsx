"use client";

import Link from "next/link";

import { AddressList } from "./address-list";
import { ProfileForm } from "./profile-form";
import { useSession } from "./session-provider";

/**
 * `/account` (`US-2.4`, `US-2.5`) — the client half of the page, because everything on it is behind
 * a token that only exists in memory (`ADR-0009`), so none of it can be rendered on the server.
 *
 * The three session states are handled here rather than by each section:
 *
 * - **`restoring`** — the token is on its way back from the refresh cookie. Rendering the signed-out
 *   state here is the one thing that must not happen: it would show "not signed in" to a signed-in
 *   customer on every navigation. `UX.md` section 5 has no `/account` row, so the states are chosen
 *   here rather than quoted.
 * - **signed out** — the page is still useful, because it says what the account is for and how to
 *   get to one, instead of being an error.
 * - **signed in** — profile and addresses, each its own `<section>` with its own heading, so the
 *   page keeps one `<h1>` and a heading order a screen reader can follow (`UX.md` section 7).
 */
export function AccountScreen() {
  const { status, user } = useSession();

  if (status === "restoring") {
    return <p className="mt-10 text-muted">Loading your account…</p>;
  }

  if (status !== "authenticated" || user === null) {
    return (
      <div className="mt-10 rounded-2xl border border-dashed border-border bg-surface px-8 py-16 text-center">
        <h2 className="text-xl">You are not signed in</h2>
        <p className="mx-auto mt-3 max-w-measure text-muted">
          Sign in to see your profile and keep your delivery addresses.
        </p>
        <p className="mt-6">
          <Link
            href="/login"
            className="inline-flex min-h-11 items-center rounded-lg bg-primary px-6 text-primary-ink"
          >
            Sign in
          </Link>
        </p>
      </div>
    );
  }

  return (
    <div className="mt-10 flex flex-col gap-16">
      <section aria-labelledby="profile-heading">
        <h2 id="profile-heading" className="text-2xl tracking-tight">
          Profile
        </h2>
        <ProfileForm user={user} />
      </section>

      <section aria-labelledby="addresses-heading">
        <h2 id="addresses-heading" className="text-2xl tracking-tight">
          Addresses
        </h2>
        <AddressList />
      </section>
    </div>
  );
}
