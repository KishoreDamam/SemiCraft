import type { Metadata } from "next";
// Self-hosted, like Monaco: no font CDN, so the UI renders the same on a
// network with no outbound access.
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-mono/400.css";
import "@fontsource/ibm-plex-mono/500.css";
import "./globals.css";

export const metadata: Metadata = {
  title: "SemiCraft · RTL, module and IP generator",
  description:
    "Configure a counter, a FIFO or an AXI4-Lite UART and get lint-checked RTL, testbenches and a datasheet. Same options, same bytes.",
  openGraph: {
    title: "SemiCraft",
    description:
      "Lint-checked RTL, testbenches and a datasheet from options you choose. Same options, same bytes.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="flex min-h-full flex-col">
        <a href="#main" className="skip-link">
          Skip to generator
        </a>
        {children}
      </body>
    </html>
  );
}
