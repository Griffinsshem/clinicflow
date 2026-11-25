import type { Metadata } from "next";
import { connection } from "next/server";
import { Public_Sans, Source_Serif_4 } from "next/font/google";

import "./globals.css";

const publicSans = Public_Sans({
  subsets: ["latin"],
  variable: "--font-public-sans",
  display: "swap",
});

const sourceSerif = Source_Serif_4({
  subsets: ["latin"],
  weight: ["400"],
  style: ["italic"],
  variable: "--font-source-serif",
  display: "swap",
});

export const metadata: Metadata = {
  title: "ClinicFlow",
  description: "Appointment and follow-up management for small clinics.",
};

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Render every page per request. The Content-Security-Policy carries a
  // fresh nonce each time (proxy.ts), and Next.js can only stamp that
  // nonce onto its scripts while rendering; a page built ahead of time
  // would carry no nonce and its scripts would be blocked.
  await connection();

  return (
    <html lang="en" className={`${publicSans.variable} ${sourceSerif.variable}`}>
      <body>{children}</body>
    </html>
  );
}
