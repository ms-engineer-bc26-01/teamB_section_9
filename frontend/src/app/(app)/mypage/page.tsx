"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Heart, Settings, Shirt, UserRound } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiClient } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

type UserProfile = {
  id: string;
  email: string;
  display_name: string | null;
};

type Summary = {
  total: number;
};

type MypageState = {
  profile: UserProfile | null;
  clothesCount: number;
  favoriteCount: number;
};

function getMetadataDisplayName(metadata: Record<string, unknown> | undefined) {
  const displayName = metadata?.display_name;
  return typeof displayName === "string" && displayName.trim().length > 0
    ? displayName.trim()
    : null;
}

async function fetchMypageData(token: string): Promise<MypageState> {
  const [profile, clothes, favoriteOutfits] = await Promise.all([
    apiClient.get<UserProfile>("/auth/me", { token }),
    apiClient.get<Summary>("/clothes?limit=1", { token }),
    apiClient.get<Summary>("/outfits?limit=1&is_favorite=true", { token }),
  ]);

  return {
    profile,
    clothesCount: clothes.total,
    favoriteCount: favoriteOutfits.total,
  };
}

export default function MypagePage() {
  const { session, user } = useAuthStore();
  const [data, setData] = useState<MypageState | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const token = session?.access_token;

    if (!token) {
      return;
    }

    let isMounted = true;

    fetchMypageData(token)
      .then((result) => {
        if (!isMounted) return;
        setData(result);
      })
      .catch(() => {
        if (!isMounted) return;
        setErrorMessage("マイページ情報を取得できませんでした。");
      });

    return () => {
      isMounted = false;
    };
  }, [session?.access_token]);

  const displayName = useMemo(() => {
    const metadataName = getMetadataDisplayName(user?.user_metadata);
    return metadataName ?? data?.profile?.display_name ?? "ユーザー";
  }, [data?.profile?.display_name, user?.user_metadata]);

  const token = session?.access_token;
  const isLoading = Boolean(token) && data === null && errorMessage === null;

  const email = data?.profile?.email ?? user?.email ?? "";
  const clothesCount = data?.clothesCount ?? 0;
  const favoriteCount = data?.favoriteCount ?? 0;

  return (
    <div className="space-y-5">
      <section aria-labelledby="mypage-heading" className="space-y-3">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <p className="text-sm font-medium text-[#8C715C]">My page</p>
            <h1
              id="mypage-heading"
              className="mt-1 text-2xl font-bold leading-tight text-[#2B2926]"
            >
              {displayName}
            </h1>
            {email ? (
              <p className="mt-1 truncate text-sm text-[#6F6258]">{email}</p>
            ) : null}
          </div>

          <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-[#EAF4F0] text-[#2F6F63]">
            <UserRound aria-hidden="true" size={25} />
          </div>
        </div>
      </section>

      {errorMessage ? (
        <div className="rounded-lg border border-[#E8DED4] bg-white px-4 py-3 text-sm text-[#8C3D2F]">
          {errorMessage}
        </div>
      ) : null}

      <section aria-label="アカウント概要" className="grid grid-cols-2 gap-3">
        <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Shirt aria-hidden="true" size={16} className="text-[#6B4F3A]" />
              服登録件数
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-[#2B2926]">
              {isLoading ? "-" : clothesCount}
            </p>
            <p className="mt-1 text-xs text-[#8C715C]">クローゼット内</p>
          </CardContent>
        </Card>

        <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Heart aria-hidden="true" size={16} className="text-[#B76559]" />
              お気に入りコーデ
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-[#2B2926]">
              {isLoading ? "-" : favoriteCount}
            </p>
            <p className="mt-1 text-xs text-[#8C715C]">保存したコーデ</p>
          </CardContent>
        </Card>
      </section>

      <Button
        asChild
        className="h-12 w-full rounded-lg bg-[#2F6F63] text-base font-bold text-white hover:bg-[#285F55]"
      >
        <Link href="/settings">
          <Settings aria-hidden="true" />
          設定
        </Link>
      </Button>
    </div>
  );
}
