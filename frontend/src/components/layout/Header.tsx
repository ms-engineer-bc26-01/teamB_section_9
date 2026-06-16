"use client";

import Image from "next/image";
import Link from "next/link";
import { ChevronLeft, Settings } from "lucide-react";
import { usePathname, useRouter } from "next/navigation";

const pageTitles: Record<string, string> = {
  "/mypage": "マイページ",
  "/settings": "設定",
  "/clothes": "服一覧",
  "/clothes/register": "服登録",
  "/outfits/scenes": "シーン選択",
  "/outfits/loading": "提案生成中",
  "/outfits/detail": "コーデ詳細",
  "/register": "アカウント登録",
  "/login": "ログイン",
};

export function Header() {
  const pathname = usePathname();
  const router = useRouter();

  const isHome = pathname === "/";
  const title = pageTitles[pathname] ?? "";

  return (
    <header className="sticky top-0 z-40 border-b border-[#E8DED4] bg-[#FAF8F5]/95 backdrop-blur">
      <div className="mx-auto grid h-16 w-full max-w-[390px] grid-cols-[48px_1fr_48px] items-center px-4">
        <div className="flex justify-start">
          {isHome ? (
            <Link
              href="/"
              aria-label="Climo ホームへ戻る"
              className="flex items-center"
            >
              <Image
                src="/image-icon.png"
                alt="Climo"
                width={80}
                height={32}
                priority
                className="h-auto w-[104px]"
              />
            </Link>
          ) : (
            <button
              type="button"
              aria-label="前の画面へ戻る"
              onClick={() => router.back()}
              className="flex h-9 w-9 items-center justify-center rounded-full border border-[#E8DED4] bg-white text-[#6B4F3A] shadow-sm transition hover:bg-[#F3EDE7]"
            >
              <ChevronLeft aria-hidden="true" size={20} />
            </button>
          )}
        </div>

        <div className="min-w-0 text-center">
          {isHome ? (
            <span className="sr-only">Climo</span>
          ) : (
            <h1 className="truncate text-base font-bold text-[#2B2926]">
              {title}
            </h1>
          )}
        </div>

        <div className="flex justify-end">
          <Link
            href="/settings"
            aria-label="設定を開く"
            className="flex h-9 w-9 items-center justify-center rounded-full border border-[#E8DED4] bg-white text-[#6B4F3A] shadow-sm transition hover:bg-[#F3EDE7]"
          >
            <Settings aria-hidden="true" size={18} />
          </Link>
        </div>
      </div>
    </header>
  );
}