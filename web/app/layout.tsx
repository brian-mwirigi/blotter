import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "LedgerHeal",
  description: "The supplier was short KSh 4,500.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
