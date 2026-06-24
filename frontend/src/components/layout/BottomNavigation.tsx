"use client";

import Link from "next/link";
import { Heart, Home, PencilLine, User } from "lucide-react";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "ホーム", icon: Home },
  { href: "/clothes/register", label: "アイテム登録", icon: PencilLine },
  { href: "/favorites", label: "お気に入り", icon: Heart },
  { href: "/mypage", label: "マイページ", icon: User },
];

export function BottomNavigation() {
  const pathname = usePathname();

  return (
    <nav
      className="
        fixed bottom-0 left-0 right-0 z-40 border-t border-[#E8DED4] bg-white/95 backdrop-blur
        md:left-[calc(50%+210px)] md:right-auto md:top-32 md:bottom-auto
        md:w-24 md:rounded-3xl md:border md:bg-white md:px-2 md:py-3 md:shadow-sm
      "
    >
      <div
        className="
          mx-auto grid h-16 max-w-[390px] grid-cols-4 px-2
          md:h-auto md:max-w-none md:grid-cols-1 md:gap-2 md:px-0
        "
      >
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);

          return (
            <Link
              key={item.href}
              href={item.href}
              className="
                flex flex-col items-center justify-center gap-1 rounded-2xl text-xs transition-colors
                hover:bg-[#F4EEE8]
              "
            >
              <Icon
                aria-hidden="true"
                size={21}
                className={isActive ? "text-[#5A4333]" : "text-[#9A8D80]"}
              />
              <span
                className={
                  isActive ? "font-medium text-[#5A4333]" : "text-[#9A8D80]"
                }
              >
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
