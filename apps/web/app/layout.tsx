import Providers from "./providers";
import GlobalHotkeys from "./GlobalHotkeys";

type Props = { children?: any };

export const metadata = { title: "AURORA-Lite" };
export const dynamic = "force-dynamic";
export default function RootLayout({ children }: Props) {
  return (
    <html lang="en">
      <body>
        <GlobalHotkeys />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
