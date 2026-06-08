"use client";

import { useEffect } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/stores/auth-store";

export function RequireAuth({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const user = useAuthStore((state) => state.user);
  const isInitialized = useAuthStore((state) => state.isInitialized);

  useEffect(() => {
    if (!isInitialized) return;
    if (user) return;

    const query = searchParams.toString();
    const redirectTo = query ? pathname + "?" + query : pathname;
    router.replace("/login?redirect=" + encodeURIComponent(redirectTo));
  }, [isInitialized, user, pathname, searchParams, router]);

  if (!isInitialized) {
    return <div>認証状態を確認中...</div>;
  }

  if (!user) {
    return null;
  }

  return children;
}
