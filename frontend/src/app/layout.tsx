import type { Metadata } from "next";
import { Geist, Geist_Mono, Figtree } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { BottomNavigation } from "@/components/layout/BottomNavigation";
import { AuthProvider } from "@/components/auth/AuthProvider";

const figtree = Figtree({ subsets: ["latin"], variable: "--font-sans" });

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Climo",
  description: "天気と手持ち服から今日のコーデを提案するAIスタイリスト",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="ja"
      className={cn(
        "h-full",
        "antialiased",
        geistSans.variable,
        geistMono.variable,
        "font-sans",
        figtree.variable,
      )}
    >
      <body
        className={cn(
          "min-h-full",
          "bg-[#FAF8F5]",
          "text-[#2B2926]",
          "flex",
          "flex-col",
        )}
      >
        <AuthProvider>
          <Header />

          <main className="mx-auto w-full max-w-[390px] flex-1 px-4 pt-4 pb-20 md:pb-6">
            {children}
          </main>

          <Footer />
          <BottomNavigation />
        </AuthProvider>
      </body>
    </html>
  );
}
