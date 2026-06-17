"use client";

import { useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Sparkles } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { createOutfit, suggestOutfit } from "@/features/outfits/api";
import { getOutfitSuggestionStorageKey } from "@/features/outfits/storage";
import type { OutfitSuggestResponse } from "@/features/outfits/types";
import { useAuthStore } from "@/stores/auth-store";

const allowedTpos = [
  "business",
  "casual",
  "formal",
  "ceremony",
  "leisure",
] as const;

const outfitSuggestionRequests = new Map<
  string,
  Promise<OutfitSuggestResponse>
>();

function normalizeTpo(value: string | null) {
  if (value && allowedTpos.includes(value as (typeof allowedTpos)[number])) {
    return value;
  }

  return "business";
}

function requestOutfitSuggestion(userId: string, tpo: string) {
  const requestKey = `user:${userId}:tpo:${tpo}`;
  const existingRequest = outfitSuggestionRequests.get(requestKey);

  if (existingRequest) {
    return existingRequest;
  }

  const request = suggestOutfit({ tpo }).finally(() => {
    outfitSuggestionRequests.delete(requestKey);
  });

  outfitSuggestionRequests.set(requestKey, request);

  return request;
}

export function OutfitLoadingContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const userId = useAuthStore((state) => state.user?.id ?? null);
  const isInitialized = useAuthStore((state) => state.isInitialized);
  const tpo = normalizeTpo(searchParams.get("tpo"));

  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isInitialized) {
      return;
    }

    let isMounted = true;

    async function loadSuggestion() {
      try {
        setErrorMessage(null);

        if (!userId) {
          throw new Error("ログインが必要です。");
        }

        const result = await requestOutfitSuggestion(userId, tpo);

        if (!isMounted) return;

        const suggestedOutfit = result.outfits[0];
        const responseUserId = suggestedOutfit?.user_id;
        const suggestedOutfitId = suggestedOutfit?.id;

        if (!responseUserId || !suggestedOutfitId || !suggestedOutfit) {
          throw new Error("コーデ提案の識別情報が見つかりません。");
        }

        if (responseUserId !== userId) {
          throw new Error("ログイン中のユーザーとコーデ提案結果が一致しません。");
        }

        if (suggestedOutfit.items.length === 0) {
          window.sessionStorage.setItem(
            getOutfitSuggestionStorageKey(responseUserId, suggestedOutfitId),
            JSON.stringify(result),
          );

          router.replace(
            `/outfits/detail?tpo=${encodeURIComponent(tpo)}&outfitId=${encodeURIComponent(suggestedOutfitId)}`,
          );
          return;
        }

        const savedOutfit = await createOutfit({
          tpo: suggestedOutfit.tpo,
          region_code: suggestedOutfit.region_code,
          comment: suggestedOutfit.comment,
          is_favorite: suggestedOutfit.is_favorite,
          items: suggestedOutfit.items.map((item) => ({
            name:
              item.name ??
              item.clothing_item?.name ??
              "アイテム名未設定",
            role: item.role,
            color: item.color,
            pattern: item.pattern,
            display_order: item.display_order,
            clothes_id: item.clothing_item?.id ?? item.clothes_id ?? null,
          })),
        });

        if (!isMounted) return;

        const savedResult: OutfitSuggestResponse = {
          ...result,
          outfits: [savedOutfit],
        };

        window.sessionStorage.setItem(
          getOutfitSuggestionStorageKey(savedOutfit.user_id, savedOutfit.id),
          JSON.stringify(savedResult),
        );

        router.replace(
          `/outfits/detail?tpo=${encodeURIComponent(tpo)}&outfitId=${encodeURIComponent(savedOutfit.id)}`,
        );
      } catch (error) {
        if (!isMounted) return;

        setErrorMessage(
          error instanceof Error
            ? error.message
            : "コーデ提案に失敗しました。",
        );
      }
    }

    loadSuggestion();

    return () => {
      isMounted = false;
    };
  }, [isInitialized, router, tpo, userId]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#FAF8F5] px-5 text-[#2F2925]">
      <Card className="w-full max-w-[390px] border-[#E7DDD3] bg-white/90 shadow-sm">
        <CardContent className="flex flex-col items-center gap-5 px-6 py-12 text-center">
          <div className="rounded-full bg-[#F0E8E0] p-5 text-[#6B4F3A]">
            <Sparkles aria-hidden="true" className="h-8 w-8 animate-pulse" />
          </div>

          <div className="space-y-2">
            <h1 className="text-xl font-semibold">コーデを提案中です</h1>
            <p className="text-sm leading-6 text-[#6F6259]">
              今日の天気と予定に合わせて、登録済みの服から組み合わせを考えています。
            </p>

            {errorMessage ? (
              <p
                role="alert"
                className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700"
              >
                {errorMessage}
              </p>
            ) : null}
          </div>

          <div className="h-2 w-full overflow-hidden rounded-full bg-[#EFE7DF]">
            <div className="h-full w-2/3 animate-pulse rounded-full bg-[#8C715C]" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
