import Providers from "./providers";
import GlobalHotkeys from "./GlobalHotkeys";
import "./globals.css";
import CommandKOverlay from "@/components/CommandKOverlay";

type Props = { children?: any };

export const metadata = { title: "AURORA-Lite" };
// When performing a static export (STATIC_EXPORT=1) we must not force dynamic rendering
// or Next.js will bail out with NEXT_STATIC_GEN_BAILOUT errors. Default to force-dynamic
// for normal SSR builds to preserve existing behaviour.
export const dynamic = process.env.STATIC_EXPORT ? "auto" : "force-dynamic";
export default function RootLayout({ children }: Props) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Orbitron:wght@600;700;800&family=Exo+2:wght@600;700&family=Roboto+Mono:wght@500;700&display=swap" rel="stylesheet" />
      </head>
      <body>
        <canvas className="canvas-stars" />
        <GlobalHotkeys />
        <CommandKOverlay />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
