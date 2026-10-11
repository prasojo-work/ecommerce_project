import type { Metadata } from "next";

import { AuthForm } from "@/components/auth-form";

export const metadata: Metadata = {
  title: "Sign in — LYSHEIM",
  description: "Sign in to your LYSHEIM account.",
};

/**
 * `/login` (`US-2.2`, `UX.md` flow D). A Server Component: the page is a heading, a sentence and the
 * form, and only the form needs to be interactive.
 */
export default function LoginPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <div className="mx-auto max-w-md">
        <h1 className="text-3xl tracking-tight">Sign in</h1>
        <p className="mt-2 text-muted">Welcome back. Your saved addresses and cart are waiting.</p>
        <AuthForm mode="login" />
      </div>
    </main>
  );
}
