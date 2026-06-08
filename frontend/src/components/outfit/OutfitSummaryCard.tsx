import Link from "next/link";
import { Heart } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

type OutfitSummaryCardProps = {
    id: string;
    tpo: string;
    comment?: string | null;
    weatherSummary?: string | null;
    isFavorite?: boolean;
};

export function OutfitSummaryCard({
    id,
    tpo,
    comment,
    weatherSummary,
    isFavorite = false,
}: OutfitSummaryCardProps) {
    return (
        <Card className="bg-white">
            <CardHeader>
                <div className="flex items-start justify-between gap-3">
                    <div className="space-y-2">
                        <Badge variant="secondary">{tpo}</Badge>
                        <CardTitle>おすすめコーデ</CardTitle>
                    </div>

                    {isFavorite && (
                        <Heart
                            aria-label="お気に入り"
                            className="size-4 shrink-0 fill-current"
                        />
                    )}
                </div>
            </CardHeader>

            <CardContent className="space-y-2">
                {weatherSummary && (
                    <p className="text-sm text-muted-foreground">{weatherSummary}</p>
                )}

                {comment && <p className="text-sm leading-6">{comment}</p>}
            </CardContent>

            <CardFooter>
                <Button asChild className="w-full">
                    <Link href={`/outfits/${id}`}>このコーデを見る</Link>
                </Button>
            </CardFooter>
        </Card>
    );
}