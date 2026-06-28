"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CalendarDays,
  CloudSun,
  Heart,
  MapPin,
  RefreshCw,
  Shirt,
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
import { getOutfit, updateOutfit } from "@/features/outfits/api";
import { getOutfitSuggestionStorageKey } from "@/features/outfits/storage";
import {
  formatRegionLabel,
  getSuggestedOutfitItemColor,
  getSuggestedOutfitItemName,
} from "@/features/outfits/types";
import type {
  SavedSuggestionResult,
  SuggestedOutfit,
} from "@/features/outfits/types";
import { useAuthStore } from "@/stores/auth-store";

const tpoLabels: Record<string, string> = {
  business: "オフィス向けコーデ",
  casual: "カジュアル向けコーデ",
  formal: "フォーマル向けコーデ",
  ceremony: "セレモニー向けコーデ",
  leisure: "レジャー向けコーデ",
};

const tpoSceneLabels: Record<string, string> = {
  business: "ビジネス",
  casual: "カジュアル",
  formal: "フォーマル",
  ceremony: "セレモニー",
  leisure: "レジャー",
};

type OutfitDetailState = {
  outfit: SuggestedOutfit | null;
  errorMessage: string | null;
  isLoading: boolean;
};

const COORDINATE_IMAGE_REFRESH_ATTEMPTS = 6;
const COORDINATE_IMAGE_REFRESH_INTERVAL_MS = 2000;

function loadOutfitSuggestion(
  userId: string,
  outfitId: string,
): OutfitDetailState {
  const rawSuggestion = window.sessionStorage.getItem(
    getOutfitSuggestionStorageKey(userId, outfitId),
  );

  if (!rawSuggestion) {
    return {
      outfit: null,
      errorMessage: "コーデ提案結果が見つかりません。",
      isLoading: false,
    };
  }

  try {
    const suggestion = JSON.parse(rawSuggestion) as SavedSuggestionResult;
    const rawOutfit = suggestion.outfits[0];
    const outfitUserId = rawOutfit?.user_id;
    const savedOutfitId = rawOutfit?.id;

    if (!rawOutfit || outfitUserId !== userId || savedOutfitId !== outfitId) {
      return {
        outfit: null,
        errorMessage: "ログイン中のユーザーまたはコーデ提案結果が一致しません。",
        isLoading: false,
      };
    }

    // Normalize: fill region / weather_* from the wrapper when absent on the
    // outfit (unsaved OutfitSuggestResponse stores these only at the top level).
    const outfit: SuggestedOutfit = {
      ...rawOutfit,
      region: rawOutfit.region ?? suggestion.region_used ?? null,
      weather_summary:
        rawOutfit.weather_summary ?? suggestion.weather_summary ?? null,
      weather_temp_max:
        rawOutfit.weather_temp_max ?? suggestion.weather_temp_max ?? null,
      weather_temp_min:
        rawOutfit.weather_temp_min ?? suggestion.weather_temp_min ?? null,
    };

    return {
      outfit,
      errorMessage: null,
      isLoading: false,
    };
  } catch {
    return {
      outfit: null,
      errorMessage: "コーデ提案結果の読み込みに失敗しました。",
      isLoading: false,
    };
  }
}

function getOutfitIdFromCurrentUrl() {
  const searchParams = new URLSearchParams(window.location.search);

  return searchParams.get("outfitId");
}

function waitForCoordinateImageRefresh() {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, COORDINATE_IMAGE_REFRESH_INTERVAL_MS);
  });
}

function formatTemperature(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return null;
  }

  return `${Math.round(value)}℃`;
}

function formatCurrentTemperature(
  weatherSummary: string | null | undefined,
) {
  if (!weatherSummary) {
    return null;
  }

  const match = weatherSummary.match(/current: temp=([\d.]+)C/);

  if (!match) {
    return null;
  }

  return `${Math.round(Number(match[1]))}℃`;
}

function formatComment(comment: string | null | undefined) {
  if (!comment) {
    return "コメントはありません。";
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

function cacheOutfitSuggestion(outfit: SuggestedOutfit) {
  window.sessionStorage.setItem(
    getOutfitSuggestionStorageKey(outfit.user_id, outfit.id),
    JSON.stringify({
      outfits: [outfit],
    } satisfies SavedSuggestionResult),
  );
}

export function OutfitDetailContent() {
  const user = useAuthStore((state) => state.user);
  const isInitialized = useAuthStore((state) => state.isInitialized);

  const [{ outfit, errorMessage, isLoading }, setDetailState] =
    useState<OutfitDetailState>({
      outfit: null,
      errorMessage: null,
      isLoading: true,
    });
  const [isSavingFavorite, setIsSavingFavorite] = useState(false);

  useEffect(() => {
    if (!isInitialized) {
      return;
    }

    let isCancelled = false;

    const timeoutId = window.setTimeout(async () => {
      if (!user) {
        setDetailState({
          outfit: null,
          errorMessage: "ログインが必要です。",
          isLoading: false,
        });
        return;
      }

      const outfitId = getOutfitIdFromCurrentUrl();

      if (!outfitId) {
        setDetailState({
          outfit: null,
          errorMessage: "コーデ提案IDが見つかりません。",
          isLoading: false,
        });
        return;
      }

      const sessionStorageState = loadOutfitSuggestion(user.id, outfitId);
      const cachedOutfit = sessionStorageState.outfit;

      if (cachedOutfit) {
        setDetailState(sessionStorageState);
      }

      if (cachedOutfit) {
        const refreshAttempts = cachedOutfit.coordinate_image_url
          ? 1
          : COORDINATE_IMAGE_REFRESH_ATTEMPTS;

        for (let attempt = 0; attempt < refreshAttempts; attempt += 1) {
          if (attempt > 0) {
            await waitForCoordinateImageRefresh();
          }

          if (isCancelled) {
            return;
          }

          try {
            const foundOutfit = await getOutfit(outfitId);

            if (isCancelled) {
              return;
            }

            cacheOutfitSuggestion(foundOutfit);
            setDetailState({
              outfit: foundOutfit,
              errorMessage: null,
              isLoading: false,
            });

            if (foundOutfit.coordinate_image_url) {
              return;
            }
          } catch {
            return;
          }
        }

        return;
      }

      try {
        const foundOutfit = await getOutfit(outfitId);

        setDetailState({
          outfit: foundOutfit,
          errorMessage: null,
          isLoading: false,
        });
      } catch {
        setDetailState({
          outfit: null,
          errorMessage: "コーデ情報を取得できませんでした。",
          isLoading: false,
        });
      }
    }, 0);

    return () => {
      isCancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [isInitialized, user]);

  const outfitTitle = outfit ? tpoLabels[outfit.tpo] ?? "おすすめコーデ" : "";
  const sceneLabel = outfit ? tpoSceneLabels[outfit.tpo] ?? outfit.tpo : "";
  const regionLabel = formatRegionLabel(outfit?.region);
  const maxTemperature = formatTemperature(outfit?.weather_temp_max);
  const minTemperature = formatTemperature(outfit?.weather_temp_min);
  const temperatureText =
    maxTemperature && minTemperature
      ? `最高${maxTemperature}・最低${minTemperature}`
      : null;
  const currentTemperature = outfit
    ? formatCurrentTemperature(outfit.weather_summary)
    : null;
  const weatherText =
    currentTemperature && temperatureText
      ? `現在${currentTemperature} / ${temperatureText}`
      : temperatureText ?? outfit?.weather_summary ?? "";
  const commentText = formatComment(outfit?.comment);
  const outfitItems = [...(outfit?.items ?? [])].sort(
    (a, b) => a.display_order - b.display_order,
  );
  const outfitImageUrl = outfit ? getOutfitImageUrl(outfit) : null;
  // 未保存の /outfits/suggest 結果には source がないため PATCH 対象外にする。
  const canUpdateFavorite = Boolean(outfit?.source);

  async function handleToggleFavorite() {
    if (!outfit || !canUpdateFavorite || isSavingFavorite) {
      return;
    }

    setIsSavingFavorite(true);
    setDetailState((current) => ({
      ...current,
      errorMessage: null,
    }));

    try {
      const updatedOutfit = await updateOutfit(outfit.id, {
        is_favorite: !outfit.is_favorite,
      });

      cacheOutfitSuggestion(updatedOutfit);

      setDetailState((current) => ({
        ...current,
        outfit: updatedOutfit,
        errorMessage: null,
        isLoading: false,
      }));
    } catch (error) {
      setDetailState((current) => ({
        ...current,
        errorMessage:
          error instanceof Error
            ? error.message
            : "コーデの保存状態を更新できませんでした。",
      }));
    } finally {
      setIsSavingFavorite(false);
    }
  }

  return (
    <div className="min-h-screen bg-[#FAF8F5] px-5 py-6 text-[#2F2925]">
      <div className="mx-auto flex w-full max-w-[390px] flex-col gap-5">
        {errorMessage ? (
          <Card className="border-red-100 bg-red-50 shadow-sm">
            <CardContent className="px-5 py-4">
              <p role="alert" className="text-sm text-red-700">
                {errorMessage}
              </p>
            </CardContent>
          </Card>
        ) : null}

        {isLoading ? (
          <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
            <CardContent className="px-5 py-4">
              <p className="text-sm text-[#6F6259]">
                コーデ提案結果を読み込んでいます。
              </p>
            </CardContent>
          </Card>
        ) : null}

        {outfit ? (
          <>
            <section className="space-y-2">
              <Badge className="bg-[#E8DDD3] text-[#6B4F3A] hover:bg-[#E8DDD3]">
                Today&apos;s Outfit
              </Badge>
              <h1 className="text-2xl font-semibold tracking-tight">
                {outfitTitle}
              </h1>
              <p className="text-sm leading-6 text-[#6F6259]">
                今日の天気と予定に合わせたコーデ提案です。
              </p>
            </section>

            {outfitImageUrl ? (
              <Card className="overflow-hidden border-[#E7DDD3] bg-white/90 shadow-sm">
                <div
                  aria-label={`${sceneLabel}のコーデ画像`}
                  className="aspect-[4/3] w-full bg-[#F4EEE8] bg-contain bg-center bg-no-repeat"
                  role="img"
                  style={{ backgroundImage: `url(${outfitImageUrl})` }}
                />
              </Card>
            ) : null}

            <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
              <CardHeader className="space-y-3">
                {regionLabel ? (
                  <div className="flex items-center gap-2 text-sm text-[#6F6259]">
                    <MapPin aria-hidden="true" className="h-4 w-4" />
                    <span>{regionLabel}</span>
                  </div>
                ) : null}
                <div className="flex items-center gap-2 text-sm text-[#6F6259]">
                  <CloudSun aria-hidden="true" className="h-4 w-4" />
                  <span>{weatherText}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-[#6F6259]">
                  <CalendarDays aria-hidden="true" className="h-4 w-4" />
                  <span>{sceneLabel}</span>
                </div>
              </CardHeader>
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
                    const itemPattern =
                      item.pattern ?? item.clothing_item?.pattern ?? null;

                    return (
                      <div
                        key={`${item.role}-${item.display_order}`}
                        className="rounded-xl bg-[#FAF8F5] px-4 py-3"
                      >
                        <div className="flex items-center justify-between gap-3">
                          <span className="text-sm text-[#6F6259]">
                            {item.role}
                          </span>
                          <span className="text-right text-sm font-medium">
                            {getSuggestedOutfitItemName(item)}
                          </span>
                        </div>

                        {itemColor || itemPattern ? (
                          <p className="mt-1 text-xs text-[#8C715C]">
                            {[itemColor, itemPattern]
                              .filter(Boolean)
                              .join(" / ")}
                          </p>
                        ) : null}
                      </div>
                    );
                  })
                ) : (
                  <p className="rounded-xl bg-[#FAF8F5] px-4 py-3 text-sm text-[#6F6259]">
                    アイテム情報がありません。
                  </p>
                )}
              </CardContent>
            </Card>

            <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
              <CardHeader>
                <CardTitle className="text-lg">コーデのポイント</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm leading-6 text-[#6F6259]">
                  {commentText}
                </p>
              </CardContent>
            </Card>

            <div className="grid grid-cols-2 gap-3">
              <Button
                type="button"
                variant="outline"
                className="border-[#D8C9BB] bg-white text-[#6B4F3A]"
                aria-label={
                  !canUpdateFavorite
                    ? "未保存のコーデのためお気に入りを更新できません"
                    : outfit.is_favorite
                      ? "このコーデのお気に入りを解除する"
                      : "このコーデをお気に入りに登録する"
                }
                disabled={isSavingFavorite || !canUpdateFavorite}
                onClick={handleToggleFavorite}
              >
                <Heart
                  aria-hidden="true"
                  className={
                    outfit.is_favorite
                      ? "mr-2 h-4 w-4 fill-[#6B4F3A] text-[#6B4F3A]"
                      : "mr-2 h-4 w-4"
                  }
                />
                {!canUpdateFavorite
                  ? "保存不可"
                  : isSavingFavorite
                    ? "保存中..."
                    : outfit.is_favorite
                      ? "保存済み"
                      : "保存"}
              </Button>

              <Button
                asChild
                className="bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
              >
                <Link
                  href={`/outfits/loading?tpo=${encodeURIComponent(outfit.tpo)}`}
                  aria-label="同じシーンで別のコーデを再提案する"
                >
                  <RefreshCw aria-hidden="true" className="mr-2 h-4 w-4" />
                  別案
                </Link>
              </Button>
            </div>
          </>
        ) : null}

        <Button asChild variant="ghost" className="text-[#6B4F3A]">
          <Link href="/">ホームへ戻る</Link>
        </Button>
      </div>
    </div>
  );
}
