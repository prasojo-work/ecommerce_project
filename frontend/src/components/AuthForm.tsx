"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { type FormEvent, useState } from "react";

import { useAuth } from "@/lib/auth";

const inputClass = "mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const { login, register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const isRegister = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (isRegister) {
        await register(email, password, fullName);
      } else {
        await login(email, password);
      }
      router.push("/account");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-sm py-8">
      <h1 className="text-2xl font-semibold tracking-tight">
        {isRegister ? "Create account" : "Sign in"}
      </h1>

      {isRegister ? (
        <label className="mt-6 block text-sm font-medium">
          Full name
          <input
            value={fullName}
            onChange={(event) => setFullName(event.target.value)}
            className={inputClass}
          />
        </label>
      ) : null}

      <label className="mt-4 block text-sm font-medium">
        Email
        <input
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className={inputClass}
        />
      </label>

      <label className="mt-4 block text-sm font-medium">
        Password
        <input
          type="password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className={inputClass}
        />
      </label>

      {error ? <p className="mt-4 text-sm text-red-600">{error}</p> : null}

      <button
        type="submit"
        disabled={busy}
        className="mt-6 w-full rounded-md bg-emerald-800 px-4 py-3 text-sm font-medium text-white transition hover:bg-emerald-900 disabled:opacity-60"
      >
        {busy ? "Please wait…" : isRegister ? "Create account" : "Sign in"}
      </button>

      <p className="mt-4 text-sm text-neutral-600">
        {isRegister ? (
          <>
            Already have an account?{" "}
            <Link href="/login" className="text-emerald-800 underline hover:text-emerald-900">
              Sign in
            </Link>
          </>
        ) : (
          <>
            New here?{" "}
            <Link href="/register" className="text-emerald-800 underline hover:text-emerald-900">
              Create an account
            </Link>
          </>
        )}
      </p>
    </form>
  );
}
