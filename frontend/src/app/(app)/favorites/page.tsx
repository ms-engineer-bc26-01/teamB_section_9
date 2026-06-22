"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CalendarDays,
  ChevronRight,
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
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { getOutfits, updateOutfit } from "@/features/outfits/api";
import {
  getSuggestedOutfitItemName,
  type SuggestedOutfit,
} from "@/features/outfits/types";
import { useAuthStore } from "@/stores/auth-store";

type FavoritesState = {
  outfits: SuggestedOutfit[];
  total: number;
  errorMessage: string | null;
  isLoading: boolean;
};

const tpoLabels: Record<string, string> = {
  business: "ビジネス",
  casual: "カジュアル",
  formal: "フォーマル",
  ceremony: "セレモニー",
  leisure: "レジャー",
};

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

function formatComment(comment: string | null | undefined) {
  if (!comment) {
    return "コーデのポイントはまだ登録されていません。";
  }

  return comment
    .replace(/^#{1,6}\s*/gm, "")
    .replace(/\*\*/g, "")
    .trim();
}

function getOutfitImageUrl(outfit: SuggestedOutfit) {
  if (outfit.coordinate_image_url) {
    return outfit.coordinate_image_url;
  }

  const imageItem = outfit.items.find(
    (item) => item.clothing_item?.thumbnail_url ?? item.clothing_item?.image_url,
  );

  return (
    imageItem?.clothing_item?.thumbnail_url ??
    imageItem?.clothing_item?.image_url ??
    null
  );
}

export default function FavoritesPage() {
  const session = useAuthStore((state) => state.session);
  const isInitialized = useAuthStore((state) => state.isInitialized);
  const [{ outfits, total, errorMessage, isLoading }, setFavoritesState] =
    useState<FavoritesState>({
      outfits: [],
      total: 0,
      errorMessage: null,
      isLoading: true,
    });
  const [updatingOutfitId, setUpdatingOutfitId] = useState<string | null>(null);

  async function loadFavorites() {
    setFavoritesState((current) => ({
      ...current,
      errorMessage: null,
      isLoading: true,
    }));

    try {
      const response = await getOutfits({ isFavorite: true, limit: 100 });

      setFavoritesState({
        outfits: response.items,
        total: response.total,
        errorMessage: null,
        isLoading: false,
      });
    } catch (error) {
      setFavoritesState({
        outfits: [],
        total: 0,
        errorMessage:
          error instanceof Error
            ? error.message
            : "お気に入りコーデを取得できませんでした。",
        isLoading: false,
      });
    }
  }

  useEffect(() => {
    if (!isInitialized) {
      return;
    }

    if (!session?.access_token) {
      setFavoritesState({
        outfits: [],
        total: 0,
        errorMessage: "ログインが必要です。",
        isLoading: false,
      });
      return;
    }

    void loadFavorites();
  }, [isInitialized, session?.access_token]);

  async function handleRemoveFavorite(outfitId: string) {
    if (updatingOutfitId) {
      return;
    }

    setUpdatingOutfitId(outfitId);
    setFavoritesState((current) => ({
      ...current,
      errorMessage: null,
    }));

    try {
      await updateOutfit(outfitId, { is_favorite: false });
      setFavoritesState((current) => ({
        ...current,
        outfits: current.outfits.filter((outfit) => outfit.id !== outfitId),
        total: Math.max(0, current.total - 1),
      }));
    } catch (error) {
      setFavoritesState((current) => ({
        ...current,
        errorMessage:
          error instanceof Error
            ? error.message
            : "お気に入りを解除できませんでした。",
      }));
    } finally {
      setUpdatingOutfitId(null);
    }
  }

  const isEmpty = !isLoading && !errorMessage && outfits.length === 0;

  return (
    <main className="min-h-screen bg-[#FAF8F5] px-5 py-6 text-[#2B2926]">
      <div className="mx-auto flex w-full max-w-[390px] flex-col gap-5">
        <section className="space-y-2">
          <Badge className="bg-[#E8DDD3] text-[#6B4F3A] hover:bg-[#E8DDD3]">
            Favorites
          </Badge>
          <h1 className="text-2xl font-semibold tracking-tight">
            お気に入り
          </h1>
          <p className="text-sm leading-6 text-[#6F6259]">
            保存したコーデの中から、お気に入りにしたものだけを確認できます。
          </p>
        </section>

        <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
          <CardContent className="flex items-center justify-between px-5 py-4">
            <div>
              <p className="text-xs font-semibold text-[#8C715C]">
                FAVORITE OUTFITS
              </p>
              <p className="mt-1 text-2xl font-bold">{total}</p>
            </div>
            <Heart
              aria-hidden="true"
              className="h-7 w-7 fill-[#C0784A] text-[#C0784A]"
            />
          </CardContent>
        </Card>

        {errorMessage ? (
          <Card className="border-red-100 bg-red-50 shadow-sm">
            <CardContent className="space-y-3 px-5 py-4">
              <p role="alert" className="text-sm leading-6 text-red-700">
                {errorMessage}
              </p>
              <Button
                type="button"
                variant="outline"
                className="w-full border-red-200 bg-white text-red-700"
                onClick={loadFavorites}
              >
                <RefreshCw aria-hidden="true" className="mr-2 h-4 w-4" />
                再読み込み
              </Button>
            </CardContent>
          </Card>
        ) : null}

        {isLoading ? (
          <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
            <CardContent className="flex items-center gap-3 px-5 py-5">
              <Sparkles
                aria-hidden="true"
                className="h-5 w-5 animate-pulse text-[#C0784A]"
              />
              <p className="text-sm text-[#6F6259]">
                お気に入りコーデを読み込んでいます。
              </p>
            </CardContent>
          </Card>
        ) : null}

        {isEmpty ? (
          <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
            <CardContent className="space-y-4 px-5 py-6">
              <div className="flex justify-center">
                <span className="flex h-14 w-14 items-center justify-center rounded-full bg-[#F4EEE8] text-[#6B4F3A]">
                  <Heart aria-hidden="true" className="h-7 w-7" />
                </span>
              </div>
              <div className="space-y-2 text-center">
                <h2 className="text-lg font-semibold">
                  お気に入りはまだありません
                </h2>
                <p className="text-sm leading-6 text-[#6F6259]">
                  気に入ったコーデを保存すると、ここからすぐに見返せます。
                </p>
              </div>
              <div className="grid gap-2">
                <Button
                  asChild
                  className="bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
                >
                  <Link href="/outfits/scenes">シーンを選ぶ</Link>
                </Button>
                <Button
                  asChild
                  variant="outline"
                  className="border-[#D8C9BB] bg-white text-[#6B4F3A]"
                >
                  <Link href="/outfits/closet">クローゼット服で提案</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : null}

        <section className="space-y-4" aria-label="お気に入りコーデ一覧">
          {outfits.map((outfit) => {
            const imageUrl = getOutfitImageUrl(outfit);
            const createdAt = formatCreatedAt(outfit.created_at);
            const items = outfit.items
              .toSorted((a, b) => a.display_order - b.display_order)
              .slice(0, 3);
            const tpoLabel = tpoLabels[outfit.tpo] ?? outfit.tpo;

            return (
              <Card
                key={outfit.id}
                className="overflow-hidden border-[#E7DDD3] bg-white/90 shadow-sm"
              >
                {imageUrl ? (
                  <div
                    aria-label={`${tpoLabel}のコーデ画像`}
                    className="aspect-[4/3] w-full bg-[#F4EEE8] bg-contain bg-center bg-no-repeat"
                    role="img"
                    style={{ backgroundImage: `url(${imageUrl})` }}
                  />
                ) : (
                  <div className="flex aspect-[4/3] w-full items-center justify-center bg-[#FFFCF8] px-6 text-center text-sm leading-6 text-[#6F6259]">
                    コーデ画像は準備中です。アイテム一覧とポイントを確認できます。
                  </div>
                )}

                <CardHeader className="space-y-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="space-y-2">
                      <Badge className="bg-[#F4EEE8] text-[#6B4F3A] hover:bg-[#F4EEE8]">
                        {tpoLabel}
                      </Badge>
                      <CardTitle className="text-lg">
                        お気に入りコーデ
                      </CardTitle>
                    </div>
                    <Heart
                      aria-label="お気に入り登録済み"
                      className="h-5 w-5 shrink-0 fill-[#C0784A] text-[#C0784A]"
                    />
                  </div>
                  {createdAt ? (
                    <div className="flex items-center gap-2 text-sm text-[#6F6259]">
                      <CalendarDays aria-hidden="true" className="h-4 w-4" />
                      <span>{createdAt}</span>
                    </div>
                  ) : null}
                </CardHeader>

                <CardContent className="space-y-4">
                  <p className="line-clamp-3 text-sm leading-6 text-[#6F6259]">
                    {formatComment(outfit.comment)}
                  </p>

                  {items.length > 0 ? (
                    <div className="grid gap-2">
                      {items.map((item) => (
                        <div
                          key={`${outfit.id}-${item.role}-${item.display_order}`}
                          className="flex items-center gap-3 rounded-lg bg-[#FAF8F5] px-3 py-2 text-sm"
                        >
                          <Shirt
                            aria-hidden="true"
                            className="h-4 w-4 shrink-0 text-[#8C715C]"
                          />
                          <span className="min-w-14 text-xs font-semibold text-[#8C715C]">
                            {item.role}
                          </span>
                          <span className="truncate font-medium">
                            {getSuggestedOutfitItemName(item)}
                          </span>
                        </div>
                      ))}
                    </div>
                  ) : null}

                  <div className="grid grid-cols-2 gap-3">
                    <Button
                      asChild
                      className="bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
                    >
                      <Link href={`/outfits/preview?id=${encodeURIComponent(outfit.id)}`}>
                        詳細を見る
                        <ChevronRight
                          aria-hidden="true"
                          className="ml-1 h-4 w-4"
                        />
                      </Link>
                    </Button>
                    <Button
                      type="button"
                      variant="outline"
                      className="border-[#D8C9BB] bg-white text-[#6B4F3A]"
                      disabled={updatingOutfitId === outfit.id}
                      onClick={() => handleRemoveFavorite(outfit.id)}
                    >
                      <Heart aria-hidden="true" className="mr-2 h-4 w-4" />
                      {updatingOutfitId === outfit.id ? "解除中" : "解除"}
                    </Button>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </section>
      </div>
    </main>
  );
}
