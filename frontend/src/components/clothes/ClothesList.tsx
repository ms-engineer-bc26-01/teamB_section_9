import Link from "next/link";

import type { ClothingItem } from "@/features/clothes/types";
import { Button } from "@/components/ui/button";
import { ClothingCard } from "@/components/clothes/ClothingCard";

type ClothesListProps = {
  items: ClothingItem[];
};

export function ClothesList({ items }: ClothesListProps) {
  if (items.length === 0) {
    return (
      <section className="rounded-2xl border border-dashed border-stone-300 bg-white p-6 text-center">
        <h2 className="text-lg font-semibold text-stone-900">
          まだ服が登録されていません
        </h2>
        <p className="mt-2 text-sm text-stone-500">
          まずは1着登録して、クローゼットを作りましょう。
        </p>
        <Button asChild className="mt-5">
          <Link href="/clothes/register">服を登録する</Link>
        </Button>
      </section>
    );
  }

  return (
    <div className="grid gap-4">
      {items.map((item) => (
        <ClothingCard key={item.id} item={item} />
      ))}
    </div>
  );
}