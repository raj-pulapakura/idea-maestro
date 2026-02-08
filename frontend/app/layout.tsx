import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Idea Maestro Workspace",
  description: "Collaborative AI workspace for idea development",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
