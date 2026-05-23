import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Washington State Legal Assistant",
  description: "AI-powered Washington State law research tool grounded in RCW citations.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" style={{ height: "100%" }} suppressHydrationWarning>
      <body className={inter.className} style={{ height: "100%", margin: 0 }}>
        {children}
      </body>
    </html>
  );
}
