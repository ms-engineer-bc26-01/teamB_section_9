import Link from "next/link";

import { ClothesList } from "@/components/clothes/ClothesList";
import { Button } from "@/components/ui/button";
import { fetchClothes } from "@/features/clothes/api";
import type { ClothingItem } from "@/features/clothes/types";

export default async function ClothesPage() {
    let items: ClothingItem[] = [];
    let hasError = false;

    try {
        const data = await fetchClothes();
        items = data.items;
    } catch {
        hasError = true;
    }

    return (
        <main className="min-h-screen bg-[#FAF8F5] px-4 py-6">
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

                {hasError ? (
                    <div className="rounded-2xl bg-white p-6">
                        <h2 className="font-bold">服一覧を取得できませんでした</h2>
                        <p className="mt-2 text-sm text-stone-500">
                            APIサーバーが起動しているか確認してください。
                        </p>
                    </div>
                ) : (
                    <section aria-label="登録済みの服一覧">
                        <ClothesList items={items} />
                    </section>
                )}
            </div>
        </main>
    );
}