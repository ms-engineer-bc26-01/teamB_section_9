import Image from "next/image";
import { Heart } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import {
    Card,
    CardContent,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

type ClothingCardProps = {
    name: string;
    category: string;
    color?: string | null;
    season: string[];
    imageUrl?: string | null;
    isFavorite?: boolean;
};

export function ClothingCard({
    name,
    category,
    color,
    season,
    imageUrl,
    isFavorite = false,
}: ClothingCardProps) {
    return (
        <Card className="bg-white">
            {imageUrl ? (
                <div className="relative aspect-[4/3] w-full bg-muted">
                    <Image
                        src={imageUrl}
                        alt={`${name}の画像`}
                        fill
                        className="object-cover"
                    />
                </div>
            ) : (
                <div className="flex aspect-[4/3] items-center justify-center bg-muted text-sm text-muted-foreground">
                    No image
                </div>
            )}

            <CardHeader>
                <div className="flex items-start justify-between gap-3">
                    <CardTitle>{name}</CardTitle>

                    {isFavorite && (
                        <Heart
                            aria-label="お気に入り"
                            className="size-4 shrink-0 fill-current"
                        />
                    )}
                </div>
            </CardHeader>

            <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                    <Badge variant="secondary">{category}</Badge>
                    {color && <Badge variant="outline">{color}</Badge>}
                </div>

                <div className="flex flex-wrap gap-2">
                    {season.map((item) => (
                        <Badge key={item} variant="outline">
                            {item}
                        </Badge>
                    ))}
                </div>
            </CardContent>
        </Card>
    );
}