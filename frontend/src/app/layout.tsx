import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth";
import { ThemeProvider } from "@/lib/theme";

export const metadata: Metadata = {
  title: "cashFlow | PLAN • FORECAST • GROW",
  description: "Financial intelligence SaaS platform for small service-based businesses.",
  icons: {
    icon: [
      { url: "/favicon.ico", sizes: "any" },
      { url: "/images/cashflow-favicon.png", type: "image/png" },
    ],
    apple: "/images/cashflow-favicon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              try {
                const stored = localStorage.getItem('cashflow-theme');
                if (stored === 'dark' || (!stored && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
                  document.documentElement.classList.add('dark');
                } else {
                  document.documentElement.classList.remove('dark');
                }
              } catch (e) {}
            `,
          }}
        />
      </head>
      <body className="min-h-full flex flex-col bg-theme-bg text-theme-text transition-colors duration-200">
        <ThemeProvider>
          <AuthProvider>{children}</AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
