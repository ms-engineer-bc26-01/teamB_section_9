import { Heart } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { ClothingItem } from "@/features/clothes/types";

type ClothingCardWithItemProps = {
    item: ClothingItem;
};

type ClothingCardWithValuesProps = {
    name: string;
    category: string;
    color?: string | null;
    season: string[];
    imageUrl?: string | null;
    isFavorite?: boolean;
    tpoTags?: string[];
    wearCount?: number;
};

type ClothingCardProps = ClothingCardWithItemProps | ClothingCardWithValuesProps;

export function ClothingCard(props: ClothingCardProps) {
    let name: string;
    let category: string;
    let color: string | null | undefined;
    let season: string[];
    let imageSrc: string | null | undefined;
    let isFavorite: boolean;
    let tpoTags: string[];
    let wearCount: number | undefined;

    if ("item" in props) {
        const item = props.item;

        name = item.name;
        category = item.category;
        color = item.color;
        season = item.season;
        imageSrc = item.thumbnail_url ?? item.image_url;
        isFavorite = item.is_favorite;
        tpoTags = item.tpo_tags;
        wearCount = item.wear_count;
    } else {
        name = props.name;
        category = props.category;
        color = props.color;
        season = props.season;
        imageSrc = props.imageUrl;
        isFavorite = props.isFavorite ?? false;
        tpoTags = props.tpoTags ?? [];
        wearCount = props.wearCount;
    }

    return (
        <Card className="overflow-hidden border-stone-200 bg-white">
            <CardContent className="p-0">
                <div className="aspect-[4/3] bg-stone-100">
                    {imageSrc ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img
                            src={imageSrc}
                            alt={`${name}の画像`}
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
                                {name}
                            </h2>
                            <p className="text-sm text-stone-500">
                                {category}
                                {color ? ` / ${color}` : ""}
                            </p>
                        </div>

                        <Heart
                            aria-hidden="true"
                            className={
                                isFavorite
                                    ? "h-5 w-5 fill-stone-800 text-stone-800"
                                    : "h-5 w-5 text-stone-400"
                            }
                        />
                    </div>

                    <div className="flex flex-wrap gap-2">
                        {season.map((seasonItem) => (
                            <Badge key={seasonItem} variant="secondary">
                                {seasonItem}
                            </Badge>
                        ))}

                        {tpoTags.map((tag) => (
                            <Badge key={tag} variant="outline">
                                {tag}
                            </Badge>
                        ))}
                    </div>

                    {wearCount !== undefined && (
                        <p className="text-xs text-stone-500">
                            着用回数 {wearCount}回
                        </p>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}
