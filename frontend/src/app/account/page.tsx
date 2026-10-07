"use client";

import Link from "next/link";
import { type FormEvent, useCallback, useEffect, useState } from "react";

import { type Address, createAddress, deleteAddress, fetchAddresses } from "@/lib/api";
import { useAuth } from "@/lib/auth";

const inputClass = "mt-1 w-full rounded-md border border-neutral-300 px-3 py-2 text-sm";

const EMPTY_FORM = {
  recipient: "",
  phone: "",
  line1: "",
  city: "",
  province: "",
  postal_code: "",
};

export default function AccountPage() {
  const { user, accessToken, ready } = useAuth();
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);

  const loadAddresses = useCallback(async () => {
    if (!accessToken) return;
    setAddresses(await fetchAddresses(accessToken));
  }, [accessToken]);

  useEffect(() => {
    if (!accessToken) return;
    let active = true;
    fetchAddresses(accessToken)
      .then((data) => {
        if (active) setAddresses(data);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, [accessToken]);

  async function handleAdd(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!accessToken) return;
    setError(null);
    try {
      await createAddress(accessToken, {
        ...form,
        line2: "",
        country: "ID",
        is_default: addresses.length === 0,
      });
      setForm(EMPTY_FORM);
      await loadAddresses();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not save the address.");
    }
  }

  async function handleDelete(id: number) {
    if (!accessToken) return;
    await deleteAddress(accessToken, id);
    await loadAddresses();
  }

  if (!ready) {
    return <p className="text-neutral-600">Loading…</p>;
  }

  if (!user) {
    return (
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Account</h1>
        <p className="mt-2 text-neutral-600">
          Please{" "}
          <Link href="/login" className="text-emerald-800 underline hover:text-emerald-900">
            sign in
          </Link>{" "}
          to view your account.
        </p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <h1 className="text-2xl font-semibold tracking-tight">Account</h1>
      <p className="mt-2 text-neutral-600">{user.email}</p>

      <h2 className="mt-10 text-lg font-medium">Addresses</h2>
      {addresses.length === 0 ? (
        <p className="mt-2 text-sm text-neutral-600">No saved addresses yet.</p>
      ) : (
        <ul className="mt-3 divide-y divide-neutral-200 rounded-md border border-neutral-200">
          {addresses.map((address) => (
            <li key={address.id} className="flex items-start justify-between gap-4 px-4 py-3 text-sm">
              <span>
                <span className="font-medium text-neutral-900">{address.recipient}</span>
                {address.is_default ? (
                  <span className="ml-2 text-xs text-emerald-700">Default</span>
                ) : null}
                <br />
                <span className="text-neutral-600">
                  {address.line1}, {address.city}, {address.province} {address.postal_code}
                </span>
              </span>
              <button
                type="button"
                onClick={() => void handleDelete(address.id)}
                className="text-neutral-500 hover:text-red-600"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}

      <h2 className="mt-10 text-lg font-medium">Add an address</h2>
      <form onSubmit={handleAdd} className="mt-3 grid grid-cols-2 gap-3">
        <label className="col-span-2 text-sm font-medium">
          Recipient
          <input
            required
            value={form.recipient}
            onChange={(event) => setForm({ ...form, recipient: event.target.value })}
            className={inputClass}
          />
        </label>
        <label className="text-sm font-medium">
          Phone
          <input
            required
            value={form.phone}
            onChange={(event) => setForm({ ...form, phone: event.target.value })}
            className={inputClass}
          />
        </label>
        <label className="text-sm font-medium">
          Postal code
          <input
            required
            value={form.postal_code}
            onChange={(event) => setForm({ ...form, postal_code: event.target.value })}
            className={inputClass}
          />
        </label>
        <label className="col-span-2 text-sm font-medium">
          Address line
          <input
            required
            value={form.line1}
            onChange={(event) => setForm({ ...form, line1: event.target.value })}
            className={inputClass}
          />
        </label>
        <label className="text-sm font-medium">
          City
          <input
            required
            value={form.city}
            onChange={(event) => setForm({ ...form, city: event.target.value })}
            className={inputClass}
          />
        </label>
        <label className="text-sm font-medium">
          Province
          <input
            required
            value={form.province}
            onChange={(event) => setForm({ ...form, province: event.target.value })}
            className={inputClass}
          />
        </label>
        {error ? <p className="col-span-2 text-sm text-red-600">{error}</p> : null}
        <button
          type="submit"
          className="col-span-2 mt-2 rounded-md bg-emerald-800 px-4 py-3 text-sm font-medium text-white transition hover:bg-emerald-900"
        >
          Save address
        </button>
      </form>
    </div>
  );
}
