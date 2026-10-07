"use client";

import Link from "next/link";

import { useAuth } from "@/lib/auth";
import { useCart } from "@/lib/cart";

export function HeaderNav() {
  const { user, ready, logout } = useAuth();
  const { count } = useCart();

  return (
    <nav className="flex items-center gap-6 text-sm">
      <Link href="/products" className="text-neutral-700 hover:text-emerald-800">
        Shop
      </Link>
      <Link href="/cart" className="text-neutral-700 hover:text-emerald-800">
        Cart{count > 0 ? ` (${count})` : ""}
      </Link>
      {ready && user ? (
        <>
          <Link href="/orders" className="text-neutral-700 hover:text-emerald-800">
            Orders
          </Link>
          <Link href="/account" className="text-neutral-700 hover:text-emerald-800">
            {user.full_name || user.email}
          </Link>
          <button
            type="button"
            onClick={() => void logout()}
            className="text-neutral-700 hover:text-emerald-800"
          >
            Sign out
          </button>
        </>
      ) : (
        <Link href="/login" className="text-neutral-700 hover:text-emerald-800">
          Sign in
        </Link>
      )}
    </nav>
  );
}
