import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "NORDVIK — Everyday home goods",
    template: "%s · NORDVIK",
  },
  description: "Affordable, well-designed home goods for small spaces.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-neutral-50 text-neutral-900">
        <header className="border-b border-neutral-200 bg-white">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-4">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              NORDVIK
            </Link>
            <nav className="text-sm">
              <Link href="/products" className="text-neutral-700 hover:text-emerald-800">
                Shop
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">{children}</main>
        <footer className="border-t border-neutral-200 bg-white">
          <div className="mx-auto w-full max-w-6xl px-4 py-6 text-sm text-neutral-500">
            Demo store — payments are simulated.
          </div>
        </footer>
      </body>
    </html>
  );
}
