import type { Metadata } from "next";
import { Fraunces, Inter } from "next/font/google";

import { CartProvider } from "@/components/cart-provider";
import { SessionProvider } from "@/components/session-provider";
import { SiteHeader } from "@/components/site-header";

import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

/**
 * The display serif (`UX-DIRECTION.md` section 3): one family for the single loud heading each page
 * gets, against `Inter` for everything that is read rather than looked at.
 *
 * One weight, latin only, because this is bytes on the critical path and the hero heading is the
 * `NFR-1` LCP element. `display: swap` rather than `block` for the same reason — the heading renders
 * immediately in the serif fallback rather than waiting, and section 7 of the direction document
 * records the back-out (drop the family, keep the scale in `Inter`) if `e2e/perf.spec.ts` regresses.
 */
const fraunces = Fraunces({
  variable: "--font-fraunces",
  subsets: ["latin"],
  weight: ["600"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "LYSHEIM",
  description: "Warm, considered furniture for the long stay.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} ${fraunces.variable}`}>
      <body>
        <SessionProvider>
          <CartProvider>
            <SiteHeader />
            {children}
          </CartProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
