import Link from "next/link";

import { ClothesList } from "@/components/clothes/ClothesList";
import { Button } from "@/components/ui/button";
import { fetchClothes } from "@/features/clothes/api";
import type { ClothingItem } from "@/features/clothes/types";

export default async function ClothesPage() {
    let items: ClothingItem[] = [];
    let errorMessage = "";

    try {
        const data = await fetchClothes();
        items = data.items;
    } catch (error) {
        errorMessage =
            error instanceof Error
                ? error.message
                : "服一覧の取得に失敗しました";
    }

    return (
        <div className="space-y-6">
            <div className="mx-auto max-w-md space-y-6">
                <header className="space-y-3">
                    <div>
                        <p className="text-sm text-stone-500">My Closet</p>
                        <h1 className="text-2xl font-bold text-stone-900">登録した服</h1>
                        <p className="mt-2 text-sm text-stone-600">
                            クローゼットに登録されているアイテム一覧です。
                        </p>
                    </div>

                    <Button asChild className="w-full">
                        <Link href="/clothes/new">服を登録する</Link>
                    </Button>
                </header>

                {errorMessage ? (
                    <div className="rounded-2xl bg-white p-6">
                        <h2 className="font-bold">服一覧を取得できませんでした</h2>
                        <p className="mt-2 text-sm text-stone-500">{errorMessage}</p>
                    </div>
                ) : (
                    <section aria-label="登録済みの服一覧">
                        <ClothesList items={items} />
                    </section>
                )}
            </div>
        </div>
    );
}