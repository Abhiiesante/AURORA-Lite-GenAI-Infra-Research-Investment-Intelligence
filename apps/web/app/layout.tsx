import Providers from "./providers";

type Props = { children?: any };

export const metadata = { title: "AURORA-Lite" };
export default function RootLayout({ children }: Props) {
  return (
    <html lang="en">
      <body
        onKeyDown={(e:any)=>{
          const isCmdK = (e.ctrlKey || e.metaKey) && (e.key?.toLowerCase?.() === 'k');
          if (isCmdK) {
            e.preventDefault();
            window.location.href = '/palette';
          }
        }}
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
