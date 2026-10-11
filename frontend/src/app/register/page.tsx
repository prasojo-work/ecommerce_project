import type { Metadata } from "next";

import { AuthForm } from "@/components/auth-form";

export const metadata: Metadata = {
  title: "Create an account — LYSHEIM",
  description: "Create a LYSHEIM account to save addresses and see your orders.",
};

/**
 * `/register` (`US-2.1`, `UX.md` flow D). The display name is optional here because the API defaults
 * it to empty — a form that insisted on it would refuse a registration the server accepts.
 */
export default function RegisterPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <div className="mx-auto max-w-md">
        <h1 className="text-3xl tracking-tight">Create an account</h1>
        <p className="mt-2 text-muted">
          An account keeps your addresses and order history in one place.
        </p>
        <AuthForm mode="register" />
      </div>
    </main>
  );
}
