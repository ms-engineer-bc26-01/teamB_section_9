"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  CalendarDays,
  ChevronLeft,
  CloudSun,
  Heart,
  RefreshCw,
  Shirt,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getOutfits } from "@/features/outfits/api";
import {
  getSuggestedOutfitItemColor,
  getSuggestedOutfitItemName,
} from "@/features/outfits/types";
import type { SuggestedOutfit } from "@/features/outfits/types";
import { useAuthStore } from "@/stores/auth-store";

const tpoLabels: Record<string, string> = {
  business: "オフィス向けコーデ",
  casual: "カジュアル向けコーデ",
  formal: "フォーマル向けコーデ",
  ceremony: "セレモニー向けコーデ",
  leisure: "レジャー向けコーデ",
};

const tpoSceneLabels: Record<string, string> = {
  business: "お仕事",
  casual: "カジュアル",
  formal: "フォーマル",
  ceremony: "セレモニー",
  leisure: "レジャー",
};

type OutfitPreviewState = {
  outfit: SuggestedOutfit | null;
  errorMessage: string | null;
  isLoading: boolean;
};

function formatTemperature(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return null;
  }

  return `${Math.round(value)}℃`;
}

function formatComment(comment: string | null | undefined) {
  if (!comment) {
    return "コーデのポイントはまだ登録されていません。";
  }

  return comment
    .replace(/^#{1,6}\s*/gm, "")
    .replace(/\*\*/g, "")
    .trim();
}

function formatCreatedAt(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return new Intl.DateTimeFormat("ja-JP", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function OutfitPreviewContent() {
  const searchParams = useSearchParams();
  const session = useAuthStore((state) => state.session);
  const isInitialized = useAuthStore((state) => state.isInitialized);
  const selectedOutfitId = searchParams.get("id");
  const [{ outfit, errorMessage, isLoading }, setPreviewState] =
    useState<OutfitPreviewState>({
      outfit: null,
      errorMessage: null,
      isLoading: true,
    });

  useEffect(() => {
    if (!isInitialized) {
      return;
    }

    const token = session?.access_token;

    if (!token) {
      const timeoutId = window.setTimeout(() => {
        setPreviewState({
          outfit: null,
          errorMessage: "ログインが必要です。",
          isLoading: false,
        });
      }, 0);

      return () => window.clearTimeout(timeoutId);
    }

    let isMounted = true;

    getOutfits({ limit: selectedOutfitId ? 100 : 1 }, token)
      .then((response) => {
        if (!isMounted) {
          return;
        }

        const selectedOutfit = selectedOutfitId
          ? response.items.find((item) => item.id === selectedOutfitId) ?? null
          : response.items[0] ?? null;

        setPreviewState({
          outfit: selectedOutfit,
          errorMessage: selectedOutfit
            ? null
            : selectedOutfitId
              ? "選択したコーデが見つかりませんでした。"
              : "まだ提案履歴がありません。シーンを選んでコーデを作成してください。",
          isLoading: false,
        });
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }

        setPreviewState({
          outfit: null,
          errorMessage: "コーデ情報を取得できませんでした。",
          isLoading: false,
        });
      });

    return () => {
      isMounted = false;
    };
  }, [isInitialized, selectedOutfitId, session?.access_token]);

  const outfitTitle = outfit
    ? tpoLabels[outfit.tpo] ?? "おすすめコーデ"
    : "おすすめコーデ";
  const sceneLabel = outfit ? tpoSceneLabels[outfit.tpo] ?? outfit.tpo : "";
  const maxTemperature = formatTemperature(outfit?.weather_temp_max);
  const minTemperature = formatTemperature(outfit?.weather_temp_min);
  const temperatureText =
    maxTemperature && minTemperature
      ? `最高 ${maxTemperature} / 最低 ${minTemperature}`
      : outfit?.weather_summary ?? "天気情報なし";
  const createdAt = outfit ? formatCreatedAt(outfit.created_at) : null;
  const commentText = formatComment(outfit?.comment);
  const outfitItems =
    outfit?.items.toSorted((a, b) => a.display_order - b.display_order) ?? [];

  return (
    <div className="min-h-screen bg-[#FAF8F5] px-5 py-6 text-[#2F2925]">
      <div className="mx-auto flex w-full max-w-[390px] flex-col gap-5">
        <Button
          asChild
          variant="ghost"
          className="w-fit px-0 text-[#6B4F3A] hover:bg-transparent"
        >
          <Link href="/">
            <ChevronLeft aria-hidden="true" className="mr-1 h-4 w-4" />
            ホームへ戻る
          </Link>
        </Button>

        <section className="space-y-2">
          <Badge className="bg-[#E8DDD3] text-[#6B4F3A] hover:bg-[#E8DDD3]">
            Outfit Preview
          </Badge>
          <h1 className="text-2xl font-semibold tracking-tight">
            {outfitTitle}
          </h1>
          <p className="text-sm leading-6 text-[#6F6259]">
            最新の提案履歴から、コーデのポイントと選ばれたアイテムを確認できます。
          </p>
        </section>

        {errorMessage ? (
          <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
            <CardContent className="space-y-4 px-5 py-4">
              <p role="alert" className="text-sm leading-6 text-[#6F6259]">
                {errorMessage}
              </p>
              <Button
                asChild
                className="w-full bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
              >
                <Link href="/outfits/scenes">シーンを選ぶ</Link>
              </Button>
            </CardContent>
          </Card>
        ) : null}

        {isLoading ? (
          <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
            <CardContent className="flex items-center gap-3 px-5 py-4">
              <Sparkles
                aria-hidden="true"
                className="h-5 w-5 animate-pulse text-[#C0784A]"
              />
              <p className="text-sm text-[#6F6259]">
                最新のおすすめコーデを読み込んでいます。
              </p>
            </CardContent>
          </Card>
        ) : null}

        {outfit ? (
          <>
            <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
              <CardHeader className="space-y-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 text-sm text-[#6F6259]">
                    <CloudSun aria-hidden="true" className="h-4 w-4" />
                    <span>{temperatureText}</span>
                  </div>
                  {outfit.is_favorite ? (
                    <Heart
                      aria-label="お気に入り"
                      className="h-4 w-4 fill-current text-[#C0784A]"
                    />
                  ) : null}
                </div>
                <div className="flex items-center gap-2 text-sm text-[#6F6259]">
                  <CalendarDays aria-hidden="true" className="h-4 w-4" />
                  <span>{createdAt ? `${sceneLabel} / ${createdAt}` : sceneLabel}</span>
                </div>
              </CardHeader>
            </Card>

            <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">コーデのポイント</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="whitespace-pre-line text-sm leading-6 text-[#6F6259]">
                  {commentText}
                </p>
              </CardContent>
            </Card>

            <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Shirt aria-hidden="true" className="h-5 w-5 text-[#6B4F3A]" />
                  アイテム一覧
                </CardTitle>
                <CardDescription>
                  登録済みの服から選ばれた組み合わせです。
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                {outfitItems.length > 0 ? (
                  outfitItems.map((item) => {
                    const itemColor = getSuggestedOutfitItemColor(item);

                    return (
                      <div
                        key={`${item.role}-${item.display_order}`}
                        className="rounded-lg bg-[#FAF8F5] px-4 py-3"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-sm text-[#6F6259]">
                            {item.role}
                          </span>
                          <span className="text-right text-sm font-medium">
                            {getSuggestedOutfitItemName(item)}
                          </span>
                        </div>
                        {itemColor ? (
                          <p className="mt-1 text-xs text-[#8C715C]">
                            {itemColor}
                          </p>
                        ) : null}
                      </div>
                    );
                  })
                ) : (
                  <p className="rounded-lg bg-[#FAF8F5] px-4 py-3 text-sm text-[#6F6259]">
                    アイテム情報がありません。
                  </p>
                )}
              </CardContent>
            </Card>

            <Button
              asChild
              className="bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
            >
              <Link href={`/outfits/loading?tpo=${encodeURIComponent(outfit.tpo)}`}>
                <RefreshCw aria-hidden="true" className="mr-2 h-4 w-4" />
                同じシーンで再提案する
              </Link>
            </Button>
          </>
        ) : null}
      </div>
    </div>
  );
}
