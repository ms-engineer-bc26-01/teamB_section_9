"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CloudSun, Heart, RefreshCw, Save, Shirt, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardTitle,
} from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { fetchClothes } from "@/features/clothes/api";
import { createOutfit, suggestOutfit } from "@/features/outfits/api";
import {
  getSuggestedOutfitItemColor,
  getSuggestedOutfitItemName,
} from "@/features/outfits/types";
import type {
  OutfitSuggestResponse,
  SuggestedOutfit,
} from "@/features/outfits/types";
import { useAuthStore } from "@/stores/auth-store";

const tpoOptions = [
  { value: "business", label: "ビジネス" },
  { value: "casual", label: "カジュアル" },
  { value: "formal", label: "フォーマル" },
  { value: "ceremony", label: "セレモニー" },
  { value: "leisure", label: "レジャー" },
] as const;

type TpoValue = (typeof tpoOptions)[number]["value"];

type SuggestState = {
  outfit: SuggestedOutfit | null;
  savedOutfit: SuggestedOutfit | null;
  errorMessage: string | null;
  isSuggesting: boolean;
  isSaving: boolean;
  saveMessage: string | null;
};

type ClothesState = {
  count: number | null;
  errorMessage: string | null;
  isLoading: boolean;
};

function formatComment(comment: string | null | undefined) {
  if (!comment) {
    return "コーデポイントはまだありません。";
  }

  return comment
    .replace(/^#{1,6}\s*/gm, "")
    .replace(/\*\*/g, "")
    .trim();
}

function getItemPattern(item: SuggestedOutfit["items"][number]) {
  return item.pattern ?? item.clothing_item?.pattern ?? null;
}

function getTpoLabel(value: string) {
  return tpoOptions.find((option) => option.value === value)?.label ?? value;
}

export function OutfitClosetContent() {
  const session = useAuthStore((state) => state.session);
  const isInitialized = useAuthStore((state) => state.isInitialized);
  const [selectedTpo, setSelectedTpo] = useState<TpoValue>("casual");
  const [clothesState, setClothesState] = useState<ClothesState>({
    count: null,
    errorMessage: null,
    isLoading: true,
  });
  const [
    { outfit, savedOutfit, errorMessage, isSuggesting, isSaving, saveMessage },
    setSuggestState,
  ] = useState<SuggestState>({
    outfit: null,
    savedOutfit: null,
    errorMessage: null,
    isSuggesting: false,
    isSaving: false,
    saveMessage: null,
  });

  useEffect(() => {
    if (!isInitialized) {
      return;
    }

    if (!session?.access_token) {
      setClothesState({
        count: null,
        errorMessage: "ログインが必要です。",
        isLoading: false,
      });
      return;
    }

    let isMounted = true;

    fetchClothes()
      .then((response) => {
        if (!isMounted) {
          return;
        }

        setClothesState({
          count: response.total,
          errorMessage: null,
          isLoading: false,
        });
      })
      .catch((error) => {
        if (!isMounted) {
          return;
        }

        setClothesState({
          count: null,
          errorMessage:
            error instanceof Error
              ? error.message
              : "クローゼット服を取得できませんでした。",
          isLoading: false,
        });
      });

    return () => {
      isMounted = false;
    };
  }, [isInitialized, session?.access_token]);

  const hasNoClothes = clothesState.count === 0;
  const canSuggest =
    isInitialized &&
    Boolean(session?.access_token) &&
    !clothesState.isLoading &&
    !hasNoClothes &&
    !isSuggesting &&
    !isSaving;
  const outfitItems =
    outfit?.items.toSorted((a, b) => a.display_order - b.display_order) ?? [];
  const canSaveOutfit = Boolean(outfit) && outfitItems.length > 0;

  async function handleSuggest() {
    if (!canSuggest) {
      return;
    }

    setSuggestState({
      outfit: null,
      savedOutfit: null,
      errorMessage: null,
      isSuggesting: true,
      isSaving: false,
      saveMessage: null,
    });

    try {
      const response: OutfitSuggestResponse = await suggestOutfit({
        tpo: selectedTpo,
      });
      const suggestedOutfit = response.outfits[0] ?? null;

      if (!suggestedOutfit) {
        throw new Error("提案結果を取得できませんでした。");
      }

      setSuggestState({
        outfit: suggestedOutfit,
        savedOutfit: null,
        errorMessage: null,
        isSuggesting: false,
        isSaving: false,
        saveMessage: null,
      });
    } catch (error) {
      setSuggestState({
        outfit: null,
        savedOutfit: null,
        errorMessage:
          error instanceof Error
            ? error.message
            : "コーデ提案に失敗しました。",
        isSuggesting: false,
        isSaving: false,
        saveMessage: null,
      });
    }
  }

  async function handleSave() {
    if (!outfit || !canSaveOutfit || isSaving || savedOutfit) {
      return;
    }

    setSuggestState((current) => ({
      ...current,
      errorMessage: null,
      isSaving: true,
      saveMessage: null,
    }));

    try {
      const createdOutfit = await createOutfit({
        tpo: outfit.tpo,
        region_code: outfit.region_code,
        comment: outfit.comment,
        is_favorite: false,
        items: outfit.items.map((item) => ({
          name:
            item.name ??
            item.clothing_item?.name ??
            "アイテム名未設定",
          role: item.role,
          color: item.color ?? item.clothing_item?.color ?? null,
          pattern: item.pattern ?? item.clothing_item?.pattern ?? null,
          display_order: item.display_order,
          clothes_id: item.clothing_item?.id ?? item.clothes_id ?? null,
        })),
      });

      setSuggestState((current) => ({
        ...current,
        outfit: createdOutfit,
        savedOutfit: createdOutfit,
        isSaving: false,
        saveMessage: "コーデを保存しました。",
      }));
    } catch (error) {
      setSuggestState((current) => ({
        ...current,
        errorMessage:
          error instanceof Error
            ? error.message
            : "コーデの保存に失敗しました。",
        isSaving: false,
      }));
    }
  }

  return (
    <div className="min-h-screen bg-[#FAF8F5] px-5 py-6 text-[#2B2926]">
      <div className="mx-auto flex w-full max-w-[390px] flex-col gap-5">
        <section className="space-y-2">
          <Badge className="bg-white text-[#6B4F3A] hover:bg-white">
            Closet Suggest
          </Badge>
          <h1 className="text-2xl font-bold tracking-tight">
            クローゼット服で提案を見る
          </h1>
          <p className="text-sm leading-6 text-[#666666]">
            登録済みの服と今日の天気をもとに、クローゼット全体からコーデを提案します。
          </p>
        </section>

        <Card className="border-[#E8DED4] bg-white shadow-sm">
          <CardContent className="space-y-4 px-4 py-4">
            <div className="flex items-center gap-3">
              <label
                htmlFor="closet-tpo"
                className="flex shrink-0 items-center gap-2 text-sm font-semibold text-[#2B2926]"
              >
                <Shirt aria-hidden="true" className="h-5 w-5 text-[#6B4F3A]" />
                TPO
              </label>
              <Select
                value={selectedTpo}
                onValueChange={(value) => setSelectedTpo(value as TpoValue)}
              >
                <SelectTrigger
                  id="closet-tpo"
                  className="h-11 flex-1 border-[#8C715C] bg-white text-[#2B2926]"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {tpoOptions.map((option) => (
                    <SelectItem key={option.value} value={option.value}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="rounded-lg bg-[#FAF8F5] px-4 py-3 text-sm text-[#666666]">
              {clothesState.isLoading ? (
                <span>クローゼット服を確認しています。</span>
              ) : clothesState.errorMessage ? (
                <span role="alert">{clothesState.errorMessage}</span>
              ) : (
                <span>登録済み: {clothesState.count ?? 0}件</span>
              )}
            </div>

            {hasNoClothes ? (
              <div className="space-y-3 rounded-lg border border-[#E8DED4] bg-white px-4 py-4">
                <p className="text-sm leading-6 text-[#666666]">
                  登録済みの服がありません。先にクローゼットへ服を登録してください。
                </p>
                <Button
                  asChild
                  className="w-full bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
                >
                  <Link href="/clothes/register">服を登録する</Link>
                </Button>
              </div>
            ) : null}

            <Button
              type="button"
              disabled={!canSuggest}
              onClick={handleSuggest}
              className="h-12 w-full rounded-lg bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
            >
              {isSuggesting ? (
                <>
                  <Sparkles aria-hidden="true" className="mr-2 h-4 w-4 animate-pulse" />
                  提案中
                </>
              ) : (
                <>
                  <Sparkles aria-hidden="true" className="mr-2 h-4 w-4" />
                  コーデを提案する
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {errorMessage ? (
          <Card className="border-[#DC2626]/20 bg-white shadow-sm">
            <CardContent className="px-5 py-4">
              <p role="alert" className="text-sm leading-6 text-[#DC2626]">
                {errorMessage}
              </p>
            </CardContent>
          </Card>
        ) : null}

        {outfit ? (
          <>
            <Card className="border-[#E8DED4] bg-white shadow-sm">
              <div className="space-y-3 px-5 pt-5">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge className="bg-[#FAF8F5] text-[#6B4F3A] hover:bg-[#FAF8F5]">
                    {getTpoLabel(outfit.tpo)}
                  </Badge>
                  {savedOutfit ? (
                    <Badge className="bg-white text-[#16A34A] hover:bg-white">
                      保存済み
                    </Badge>
                  ) : null}
                </div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <CloudSun aria-hidden="true" className="h-5 w-5 text-[#6B4F3A]" />
                  提案結果
                </CardTitle>
              </div>
              <CardContent>
                <p className="whitespace-pre-line text-sm leading-6 text-[#666666]">
                  {formatComment(outfit.comment)}
                </p>
              </CardContent>
            </Card>

            <Card className="border-[#E8DED4] bg-white shadow-sm">
              <div className="space-y-1.5 px-5 pt-5">
                <CardTitle className="flex items-center gap-2 text-lg">
                  <Shirt aria-hidden="true" className="h-5 w-5 text-[#6B4F3A]" />
                  アイテム一覧
                </CardTitle>
                <CardDescription className="text-[#666666]">
                  登録服と足りないアイテムの提案を分けて表示します。
                </CardDescription>
              </div>
              <CardContent className="space-y-3">
                {outfitItems.length > 0 ? (
                  outfitItems.map((item) => {
                    const itemColor = getSuggestedOutfitItemColor(item);
                    const itemPattern = getItemPattern(item);
                    const isClosetItem = Boolean(item.clothing_item);

                    return (
                      <div
                        key={`${item.role}-${item.display_order}`}
                        className="rounded-lg bg-[#FAF8F5] px-4 py-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <span className="block text-xs font-semibold text-[#8C715C]">
                              {item.role}
                            </span>
                            <span className="block text-sm font-semibold text-[#2B2926]">
                              {getSuggestedOutfitItemName(item)}
                            </span>
                          </div>
                          <Badge
                            className={
                              isClosetItem
                                ? "shrink-0 bg-white text-[#16A34A] hover:bg-white"
                                : "shrink-0 bg-white text-[#6B4F3A] hover:bg-white"
                            }
                          >
                            {isClosetItem ? "クローゼット服" : "提案アイテム"}
                          </Badge>
                        </div>
                        {itemColor || itemPattern ? (
                          <p className="mt-2 text-xs leading-5 text-[#8C715C]">
                            {[itemColor, itemPattern].filter(Boolean).join(" / ")}
                          </p>
                        ) : null}
                      </div>
                    );
                  })
                ) : (
                  <p className="rounded-lg bg-[#FAF8F5] px-4 py-3 text-sm text-[#666666]">
                    アイテム情報がありません。
                  </p>
                )}
              </CardContent>
            </Card>

            {saveMessage ? (
              <Card className="border-[#16A34A]/20 bg-white shadow-sm">
                <CardContent className="space-y-3 px-5 py-4">
                  <p className="text-sm font-semibold text-[#16A34A]">
                    {saveMessage}
                  </p>
                  {savedOutfit ? (
                    <Button
                      asChild
                      variant="outline"
                      className="w-full border-[#16A34A] bg-white text-[#16A34A]"
                    >
                      <Link
                        href={`/outfits/detail?tpo=${encodeURIComponent(
                          savedOutfit.tpo,
                        )}&outfitId=${encodeURIComponent(savedOutfit.id)}`}
                      >
                        保存したコーデを見る
                      </Link>
                    </Button>
                  ) : null}
                </CardContent>
              </Card>
            ) : null}

            <div className="grid grid-cols-2 gap-3">
              <Button
                type="button"
                variant="outline"
                disabled={!canSaveOutfit || isSaving || Boolean(savedOutfit)}
                onClick={handleSave}
                className="h-11 rounded-lg border-[#8C715C] bg-white text-[#6B4F3A]"
              >
                {isSaving ? (
                  <>
                    <Heart aria-hidden="true" className="mr-2 h-4 w-4" />
                    保存中
                  </>
                ) : (
                  <>
                    <Save aria-hidden="true" className="mr-2 h-4 w-4" />
                    保存
                  </>
                )}
              </Button>
              <Button
                type="button"
                disabled={!canSuggest}
                onClick={handleSuggest}
                className="h-11 rounded-lg bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
              >
                <RefreshCw aria-hidden="true" className="mr-2 h-4 w-4" />
                再提案
              </Button>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}
