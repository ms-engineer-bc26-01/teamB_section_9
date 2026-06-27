"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Plus, RefreshCw, Shirt, Trash2 } from "lucide-react";

import { deleteClothing, fetchClothes } from "@/features/clothes/api";
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

type LoadClothesOptions = {
  showLoading?: boolean;
};

function getClothesErrorMessage(error: unknown) {
  return error instanceof Error
    ? error.message
    : "服一覧の取得に失敗しました。時間をおいて再度お試しください。";
}

export default function ClothesPage() {
  const [clothes, setClothes] = useState<ClothingItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [deleteErrorMessage, setDeleteErrorMessage] = useState("");
  const [deletingClothesId, setDeletingClothesId] = useState<string | null>(null);
  const [successMessage] = useState(() => {
    if (typeof window === "undefined") {
      return "";
    }

    const params = new URLSearchParams(window.location.search);
    return params.get("created") === "1" ? "登録しました。" : "";
  });
  const isMountedRef = useRef(true);

  const loadClothes = useCallback(async (
    shouldIgnore: () => boolean = () => false,
    { showLoading = true }: LoadClothesOptions = {},
  ) => {
    const isIgnored = () => shouldIgnore() || !isMountedRef.current;

    if (showLoading) {
      setIsLoading(true);
      setErrorMessage("");
    }

    try {
      const data = await fetchClothes();
      if (isIgnored()) {
        return;
      }
      setClothes(data.items);
    } catch (error) {
      if (isIgnored()) {
        return;
      }
      setErrorMessage(getClothesErrorMessage(error));
    } finally {
      if (!isIgnored()) {
        setIsLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    if (!successMessage) {
      return;
    }

    window.history.replaceState(null, "", "/clothes");
  }, [successMessage]);

  useEffect(() => {
    let ignore = false;
    isMountedRef.current = true;

    async function loadInitialClothes() {
      try {
        const data = await fetchClothes();

        if (!ignore && isMountedRef.current) {
          setClothes(data.items);
        }
      } catch (error) {
        if (!ignore && isMountedRef.current) {
          setErrorMessage(getClothesErrorMessage(error));
        }
      } finally {
        if (!ignore && isMountedRef.current) {
          setIsLoading(false);
        }
      }
    }

    void loadInitialClothes();

    return () => {
      ignore = true;
      isMountedRef.current = false;
    };
  }, []);

  async function handleDeleteClothing(clothingId: string) {
    if (deletingClothesId) {
      return;
    }

    const confirmed = window.confirm("この服を削除しますか？");

    if (!confirmed) {
      return;
    }

    setDeletingClothesId(clothingId);
    setDeleteErrorMessage("");

    try {
      await deleteClothing(clothingId);

      if (!isMountedRef.current) {
        return;
      }

      setClothes((current) =>
        current.filter((item) => item.id !== clothingId),
      );
    } catch (error) {
      if (!isMountedRef.current) {
        return;
      }

      setDeleteErrorMessage(
        error instanceof Error
          ? error.message
          : "服の削除に失敗しました。時間をおいて再度お試しください。",
      );
    } finally {
      if (isMountedRef.current) {
        setDeletingClothesId(null);
      }
    }
  }

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

      {successMessage ? (
        <div
          role="status"
          className="mb-4 rounded-3xl border border-[#D6E7DD] bg-[#F6FAF8] px-4 py-3 text-sm font-bold text-[#2F6F63]"
        >
          {successMessage}
        </div>
      ) : null}

      {deleteErrorMessage ? (
        <div
          role="alert"
          className="mb-4 rounded-3xl border border-[#F1D0C8] bg-[#FFF7F4] px-4 py-3 text-sm font-bold text-[#8C3D2F]"
        >
          {deleteErrorMessage}
        </div>
      ) : null}

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
            const isDeleting = deletingClothesId === item.id;

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
                    <h3 className="truncate text-base font-bold">{item.name}</h3>
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

                  <p className="mt-1 text-xs text-[#6F6A63]">
                    着用回数 {item.wear_count}回
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

                  <button
                    type="button"
                    className="mt-4 inline-flex items-center justify-center rounded-full border border-[#E8DED4] px-3 py-2 text-xs font-bold text-[#8C3D2F] transition-colors hover:border-[#8C3D2F] hover:bg-[#FFF4F1] disabled:cursor-not-allowed disabled:opacity-60 disabled:hover:border-[#E8DED4] disabled:hover:bg-transparent"
                    disabled={isDeleting}
                    onClick={() => void handleDeleteClothing(item.id)}
                  >
                    <Trash2 className="mr-1 h-3.5 w-3.5" aria-hidden="true" />
                    {isDeleting ? "削除中..." : "削除"}
                  </button>
                </div>
              </article>
            );
          })}
        </section>
      )}
    </section>
  );
}
