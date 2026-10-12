import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { CartProvider } from "@/components/cart-provider";
import { SessionProvider } from "@/components/session-provider";
import { SiteHeader } from "@/components/site-header";

import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "LYSHEIM",
  description: "Warm, considered furniture for the long stay.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={inter.variable}>
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
