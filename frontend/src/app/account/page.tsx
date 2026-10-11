import type { Metadata } from "next";

import { AccountScreen } from "@/components/account-screen";

export const metadata: Metadata = {
  title: "Your account — LYSHEIM",
  description: "Your LYSHEIM profile and delivery addresses.",
};

/**
 * `/account` (`UX.md` section 3, `US-2.4`, `US-2.5`). A Server Component because the heading and the
 * frame do not depend on the session — only what goes inside does, and that is `AccountScreen`'s.
 * This is also what lets the route carry its own title (`NFR-6`), which a client component cannot.
 */
export default function AccountPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <h1 className="text-3xl tracking-tight">Your account</h1>
      <AccountScreen />
    </main>
  );
}
