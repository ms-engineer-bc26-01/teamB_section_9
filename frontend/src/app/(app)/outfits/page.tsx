"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  CalendarDays,
  ChevronRight,
  Heart,
  MapPin,
  RefreshCw,
  Shirt,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { getOutfits, updateOutfit } from "@/features/outfits/api";
import {
  formatRegionLabel,
  getSuggestedOutfitItemName,
  type SuggestedOutfit,
} from "@/features/outfits/types";
import { useAuthStore } from "@/stores/auth-store";

const PAGE_SIZE = 20;

const tpoLabels: Record<string, string> = {
  business: "ビジネス",
  casual: "カジュアル",
  formal: "フォーマル",
  ceremony: "セレモニー",
  leisure: "レジャー",
};

type FilterMode = "all" | "favorite";

type HistoryState = {
  items: SuggestedOutfit[];
  total: number;
  errorMessage: string | null;
  isLoading: boolean;
  isLoadingMore: boolean;
};

type LoadOutfitsOptions = {
  append?: boolean;
  offset?: number;
};

function formatCreatedAt(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "日時不明";
  }

  return new Intl.DateTimeFormat("ja-JP", {
    year: "numeric",
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatTemperature(value: number | null | undefined) {
  if (value === null || value === undefined) {
    return null;
  }

  return `${Math.round(value)}℃`;
}

function formatComment(comment: string | null | undefined) {
  if (!comment) {
    return "コーデのコメントはありません。";
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

function getTemperatureText(outfit: SuggestedOutfit) {
  const maxTemperature = formatTemperature(outfit.weather_temp_max);
  const minTemperature = formatTemperature(outfit.weather_temp_min);

  if (maxTemperature && minTemperature) {
    return `最高 ${maxTemperature} / 最低 ${minTemperature}`;
  }

  return outfit.weather_summary ?? "天気情報なし";
}

export default function OutfitsHistoryPage() {
  const session = useAuthStore((state) => state.session);
  const isInitialized = useAuthStore((state) => state.isInitialized);
  const [filterMode, setFilterMode] = useState<FilterMode>("all");
  const [{ items, total, errorMessage, isLoading, isLoadingMore }, setState] =
    useState<HistoryState>({
      items: [],
      total: 0,
      errorMessage: null,
      isLoading: true,
      isLoadingMore: false,
    });
  const [savingFavoriteIds, setSavingFavoriteIds] = useState<Set<string>>(
    () => new Set(),
  );
  const requestIdRef = useRef(0);

  const token = session?.access_token;
  const hasMore = items.length < total;
  const selectedFilterLabel =
    filterMode === "favorite" ? "お気に入り" : "すべて";

  const loadOutfits = useCallback(
    async ({ append = false, offset = 0 }: LoadOutfitsOptions = {}) => {
      if (!isInitialized) {
        return;
      }

      const requestId = requestIdRef.current + 1;
      requestIdRef.current = requestId;
      const isLatestRequest = () => requestId === requestIdRef.current;

      if (!token) {
        setState({
          items: [],
          total: 0,
          errorMessage: "ログインが必要です。",
          isLoading: false,
          isLoadingMore: false,
        });
        return;
      }

      setState((current) => ({
        ...current,
        errorMessage: null,
        isLoading: !append,
        isLoadingMore: append,
      }));

      try {
        const response = await getOutfits(
          {
            isFavorite: filterMode === "favorite" ? true : undefined,
            limit: PAGE_SIZE,
            offset,
          },
          token,
        );

        if (!isLatestRequest()) {
          return;
        }

        setState((current) => ({
          items: append ? [...current.items, ...response.items] : response.items,
          total: response.total,
          errorMessage: null,
          isLoading: false,
          isLoadingMore: false,
        }));
      } catch (error) {
        if (!isLatestRequest()) {
          return;
        }

        setState((current) => ({
          ...current,
          errorMessage:
            error instanceof Error
              ? error.message
              : "コーデ履歴を取得できませんでした。",
          isLoading: false,
          isLoadingMore: false,
        }));
      }
    },
    [filterMode, isInitialized, token],
  );

  useEffect(() => {
    void loadOutfits();
  }, [loadOutfits]);

  async function handleToggleFavorite(outfit: SuggestedOutfit) {
    if (savingFavoriteIds.has(outfit.id)) {
      return;
    }

    setSavingFavoriteIds((current) => new Set(current).add(outfit.id));
    setState((current) => ({ ...current, errorMessage: null }));

    try {
      const updatedOutfit = await updateOutfit(outfit.id, {
        is_favorite: !outfit.is_favorite,
      });

      setState((current) => {
        const nextItems = current.items
          .map((item) => (item.id === outfit.id ? updatedOutfit : item))
          .filter((item) => filterMode !== "favorite" || item.is_favorite);

        return {
          ...current,
          items: nextItems,
          total:
            filterMode === "favorite" && !updatedOutfit.is_favorite
              ? Math.max(0, current.total - 1)
              : current.total,
        };
      });
    } catch (error) {
      setState((current) => ({
        ...current,
        errorMessage:
          error instanceof Error
            ? error.message
            : "お気に入りを更新できませんでした。",
      }));
    } finally {
      setSavingFavoriteIds((current) => {
        const next = new Set(current);
        next.delete(outfit.id);
        return next;
      });
    }
  }

  const summaryText = useMemo(() => {
    if (isLoading) {
      return "読み込み中";
    }

    return `${selectedFilterLabel} ${total}件`;
  }, [isLoading, selectedFilterLabel, total]);

  return (
    <div className="space-y-5">
      <section className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#8C715C]">
              Outfit History
            </p>
            <h1 className="mt-1 text-2xl font-bold text-[#2B2926]">
              コーデ履歴
            </h1>
          </div>

          <Button
            type="button"
            variant="outline"
            size="icon"
            className="h-11 w-11 rounded-lg border-[#E8DED4] bg-white"
            aria-label="コーデ履歴を再読み込み"
            disabled={isLoading || isLoadingMore}
            onClick={() => void loadOutfits()}
          >
            <RefreshCw
              aria-hidden="true"
              className={isLoading ? "h-4 w-4 animate-spin" : "h-4 w-4"}
            />
          </Button>
        </div>

        <div className="grid grid-cols-2 gap-2 rounded-lg bg-[#EEE5DC] p-1">
          {[
            { label: "すべて", value: "all" as const },
            { label: "お気に入り", value: "favorite" as const },
          ].map((option) => {
            const isSelected = filterMode === option.value;

            return (
              <button
                key={option.value}
                type="button"
                className={
                  isSelected
                    ? "h-10 rounded-md bg-white text-sm font-bold text-[#2B2926] shadow-sm"
                    : "h-10 rounded-md text-sm font-bold text-[#6F6258]"
                }
                aria-pressed={isSelected}
                onClick={() => setFilterMode(option.value)}
              >
                {option.label}
              </button>
            );
          })}
        </div>

        <p className="text-sm font-medium text-[#6F6258]">{summaryText}</p>
      </section>

      {errorMessage ? (
        <section className="rounded-lg border border-red-100 bg-red-50 px-4 py-3">
          <p role="alert" className="text-sm leading-6 text-red-700">
            {errorMessage}
          </p>
        </section>
      ) : null}

      {isLoading ? (
        <section className="rounded-lg border border-[#E8DED4] bg-white px-5 py-6 text-center shadow-sm">
          <Sparkles
            aria-hidden="true"
            className="mx-auto mb-3 h-6 w-6 animate-pulse text-[#C0784A]"
          />
          <p className="text-sm font-bold text-[#6F6258]">
            コーデ履歴を読み込んでいます
          </p>
        </section>
      ) : items.length === 0 ? (
        <section className="rounded-lg border border-[#E8DED4] bg-white px-6 py-8 text-center shadow-sm">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-lg bg-[#F4EEE8] text-[#6B4F3A]">
            <Shirt aria-hidden="true" size={28} />
          </div>
          <h2 className="text-base font-bold text-[#2B2926]">
            {filterMode === "favorite"
              ? "お気に入りのコーデはまだありません"
              : "コーデ履歴はまだありません"}
          </h2>
          <p className="mt-3 text-sm leading-6 text-[#6F6258]">
            シーンを選んでコーデを作成すると、保存済みのコーデがここに並びます。
          </p>
          <Button
            asChild
            className="mt-5 w-full rounded-lg bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
          >
            <Link href="/outfits/scenes">シーンを選ぶ</Link>
          </Button>
        </section>
      ) : (
        <section className="space-y-3" aria-label="コーデ履歴一覧">
          {items.map((outfit) => {
            const sceneLabel = tpoLabels[outfit.tpo] ?? outfit.tpo;
            const createdAt = formatCreatedAt(outfit.created_at);
            const regionLabel = formatRegionLabel(outfit.region);
            const imageUrl = getOutfitImageUrl(outfit);
            const previewItems = [...outfit.items]
              .sort((a, b) => a.display_order - b.display_order)
              .slice(0, 3);
            const isSavingFavorite = savingFavoriteIds.has(outfit.id);

            return (
              <article
                key={outfit.id}
                className="rounded-lg border border-[#E8DED4] bg-white p-4 shadow-sm"
              >
                <div className="flex gap-4">
                  <div className="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-lg bg-[#F4EEE8] text-[#8C715C]">
                    {imageUrl ? (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={imageUrl}
                        alt={`${sceneLabel}のコーデ画像`}
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <Shirt aria-hidden="true" size={30} />
                    )}
                  </div>

                  <div className="min-w-0 flex-1">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <Badge className="bg-[#F4EEE8] text-[#6B4F3A] hover:bg-[#F4EEE8]">
                          {sceneLabel}
                        </Badge>
                        <p className="mt-2 line-clamp-2 text-sm font-medium leading-6 text-[#2B2926]">
                          {formatComment(outfit.comment)}
                        </p>
                      </div>

                      <button
                        type="button"
                        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-[#8C715C] hover:bg-[#F4EEE8]"
                        aria-label={
                          outfit.is_favorite
                            ? "お気に入りを解除"
                            : "お気に入りに追加"
                        }
                        disabled={isSavingFavorite}
                        onClick={() => void handleToggleFavorite(outfit)}
                      >
                        <Heart
                          aria-hidden="true"
                          className={
                            outfit.is_favorite
                              ? "h-5 w-5 fill-[#C0784A] text-[#C0784A]"
                              : "h-5 w-5"
                          }
                        />
                      </button>
                    </div>

                    <div className="mt-3 flex items-center gap-2 text-xs font-medium text-[#6F6258]">
                      <CalendarDays aria-hidden="true" className="h-4 w-4" />
                      <span>{createdAt}</span>
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex flex-wrap gap-2">
                  {regionLabel ? (
                    <Badge
                      variant="outline"
                      className="flex items-center gap-1 border-[#E8DED4]"
                    >
                      <MapPin aria-hidden="true" className="h-3.5 w-3.5" />
                      {regionLabel}
                    </Badge>
                  ) : null}
                  <Badge variant="outline" className="border-[#E8DED4]">
                    {getTemperatureText(outfit)}
                  </Badge>
                  {previewItems.map((item) => (
                    <Badge
                      key={`${outfit.id}-${item.role}-${item.display_order}`}
                      variant="outline"
                      className="max-w-full border-[#E8DED4]"
                    >
                      <span className="truncate">
                        {getSuggestedOutfitItemName(item)}
                      </span>
                    </Badge>
                  ))}
                </div>

                <Link
                  href={`/outfits/preview?id=${outfit.id}`}
                  className="mt-4 flex min-h-11 items-center justify-center gap-2 rounded-lg bg-[#2B2926] px-4 py-2 text-sm font-bold text-white hover:bg-[#3A332D]"
                >
                  詳細を見る
                  <ChevronRight aria-hidden="true" className="h-4 w-4" />
                </Link>
              </article>
            );
          })}
        </section>
      )}

      {!isLoading && hasMore ? (
        <Button
          type="button"
          variant="outline"
          className="h-12 w-full rounded-lg border-[#D8C9BB] bg-white text-[#6B4F3A]"
          disabled={isLoadingMore}
          onClick={() => void loadOutfits({ append: true, offset: items.length })}
        >
          {isLoadingMore ? (
            <>
              <RefreshCw aria-hidden="true" className="mr-2 h-4 w-4 animate-spin" />
              読み込み中
            </>
          ) : (
            "もっと見る"
          )}
        </Button>
      ) : null}
    </div>
  );
}
