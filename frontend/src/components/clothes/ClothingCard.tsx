import { Heart } from "lucide-react";

import type { ClothingItem } from "@/features/clothes/types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

type ClothingCardProps = {
    item: ClothingItem;
};

export function ClothingCard({ item }: ClothingCardProps) {
    const imageSrc = item.thumbnail_url ?? item.image_url;

    return (
        <Card className="overflow-hidden border-stone-200 bg-white">
            <CardContent className="p-0">
                <div className="aspect-[4/3] bg-stone-100">
                    {imageSrc ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                            src={imageSrc}
                            alt={`${item.name}の画像`}
                            className="h-full w-full object-cover"
                        />
                    ) : (
                        <div className="flex h-full items-center justify-center text-sm text-stone-400">
                            No image
                        </div>
                    )}
                </div>

                <div className="space-y-3 p-4">
                    <div className="flex items-start justify-between gap-3">
                        <div>
                            <h2 className="text-base font-semibold text-stone-900">
                                {item.name}
                            </h2>
                            <p className="text-sm text-stone-500">
                                {item.category}
                                {item.color ? ` / ${item.color}` : ""}
                            </p>
                        </div>

                        <Heart
                            aria-hidden="true"
                            className={
                                item.is_favorite
                                    ? "h-5 w-5 fill-stone-800 text-stone-800"
                                    : "h-5 w-5 text-stone-400"
                            }
                        />
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {item.season.map((season) => (
                            <Badge key={season} variant="secondary">
                                {season}
                            </Badge>
                        ))}

                        {item.tpo_tags.map((tag) => (
                            <Badge key={tag} variant="outline">
                                {tag}
                            </Badge>
                        ))}
                    </div>

                    <p className="text-xs text-stone-500">着用回数 {item.wear_count}回</p>
                </div>
            </CardContent>
        </Card>
    );
}