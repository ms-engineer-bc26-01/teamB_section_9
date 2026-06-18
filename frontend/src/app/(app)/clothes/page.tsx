"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { Plus, RefreshCw, Shirt } from "lucide-react";

import { fetchClothes } from "@/features/clothes/api";
import type { ClothingItem } from "@/features/clothes/types";

const categoryLabels: Record<string, string> = {
  tops: "トップス",
  bottoms: "ボトムス",
  outer: "アウター",
  shoes: "シューズ",
  bag: "バッグ",
  accessory: "小物",
};

const seasonLabels: Record<string, string> = {
  spring: "春",
  summer: "夏",
  autumn: "秋",
  winter: "冬",
  all: "通年",
};

const tpoLabels: Record<string, string> = {
  casual: "カジュアル",
  business: "オフィス",
};

export default function ClothesPage() {
  const [clothes, setClothes] = useState<ClothingItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  const loadClothes = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage("");

    try {
      const data = await fetchClothes();
      setClothes(data.items);
    } catch (error) {
      setErrorMessage(
        error instanceof Error
          ? error.message
          : "服一覧の取得に失敗しました。時間をおいて再度お試しください。",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let ignore = false;

    async function load() {
      setIsLoading(true);
      setErrorMessage("");

      try {
        const data = await fetchClothes();

        if (!ignore) {
          setClothes(data.items);
        }
      } catch (error) {
        if (!ignore) {
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "服一覧の取得に失敗しました。時間をおいて再度お試しください。",
          );
        }
      } finally {
        if (!ignore) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => {
      ignore = true;
    };
  }, []);


  return (
    <section className="mx-auto min-h-screen w-full max-w-md bg-[#FAF8F5] px-5 pb-24 pt-6 text-[#2B2926]">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <p className="text-xs font-bold tracking-[0.18em] text-[#8C715C]">
            CLOSET
          </p>
          <h2 className="mt-1 text-2xl font-bold">登録した服</h2>
        </div>

        <Link
          href="/clothes/register"
          className="inline-flex h-11 w-11 items-center justify-center rounded-full bg-[#2B2926] text-white shadow-sm"
          aria-label="服を登録する"
        >
          <Plus size={22} aria-hidden="true" />
        </Link>
      </div>

      {isLoading ? (
        <div className="rounded-3xl bg-white p-6 text-center shadow-sm">
          <RefreshCw className="mx-auto mb-3 animate-spin text-[#8C715C]" />
          <p className="text-sm font-bold">服一覧を読み込み中です</p>
        </div>
      ) : errorMessage ? (
        <div className="rounded-3xl bg-white p-6 text-center shadow-sm">
          <p className="mb-4 text-sm font-bold text-red-700">{errorMessage}</p>
          <button
            type="button"
            onClick={() => void loadClothes()}
            className="rounded-full bg-[#2B2926] px-5 py-3 text-sm font-bold text-white"
          >
            再読み込みする
          </button>
        </div>
      ) : clothes.length === 0 ? (
        <section className="rounded-3xl bg-white p-8 text-center shadow-sm">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-[#F2ECE6] text-[#8C715C]">
            <Shirt size={30} aria-hidden="true" />
          </div>
          <h2 className="text-lg font-bold">まだ服が登録されていません</h2>
          <p className="mt-3 text-sm leading-6 text-[#6F6A63]">
            手持ちの服を登録すると、天気やシーンに合わせたコーデ提案に使えます。
          </p>
          <Link
            href="/clothes/register"
            className="mt-6 inline-flex w-full items-center justify-center rounded-full bg-[#2B2926] px-5 py-3 text-sm font-bold text-white"
          >
            服を登録する
          </Link>
        </section>
      ) : (
        <section className="space-y-4" aria-label="登録した服一覧">
          {clothes.map((item) => {
            const imageSrc = item.thumbnail_url ?? item.image_url;
            const seasons = item.season ?? [];
            const tpoTags = item.tpo_tags ?? [];

            return (
              <article
                key={item.id}
                className="flex gap-4 rounded-3xl bg-white p-4 shadow-sm"
              >
                <div className="flex h-24 w-24 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-[#F2ECE6]">
                  {imageSrc ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={imageSrc}
                      alt={item.name}
                      className="h-full w-full object-cover"
                    />
                  ) : (
                    <Shirt className="text-[#8C715C]" size={32} aria-hidden="true" />
                  )}
                </div>

                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <h2 className="truncate text-base font-bold">{item.name}</h2>
                    {item.is_favorite ? (
                      <span className="text-sm text-[#8C715C]" aria-label="お気に入り">
                        ♥
                      </span>
                    ) : null}
                  </div>

                  <p className="mt-1 text-sm text-[#6F6A63]">
                    {categoryLabels[item.category] ?? item.category}
                    {item.color ? ` / ${item.color}` : ""}
                  </p>

                  {seasons.length > 0 || tpoTags.length > 0 ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {seasons.map((season) => (
                        <span
                          key={season}
                          className="rounded-full bg-[#FAF8F5] px-3 py-1 text-xs font-bold text-[#8C715C]"
                        >
                          {seasonLabels[season] ?? season}
                        </span>
                      ))}
                      {tpoTags.map((tag) => (
                        <span
                          key={tag}
                          className="rounded-full border border-[#E8DED4] bg-white px-3 py-1 text-xs font-bold text-[#6F6A63]"
                        >
                          {tpoLabels[tag] ?? tag}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </article>
            );
          })}
        </section>
      )}
    </section>
  );
}
