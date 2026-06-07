// frontend/src/app/outfits/scenes/page.tsx

import Link from "next/link";
import { BriefcaseBusiness, Home, Shirt, Umbrella } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

const scenes = [
    {
        label: "オフィス",
        description: "きちんと感を出したい出勤・客先訪問向け",
        href: "/outfits/loading?tpo=business",
        icon: BriefcaseBusiness,
    },
    {
        label: "カジュアル",
        description: "休日・買い物・保育園送迎に使いやすい服装",
        href: "/outfits/loading?tpo=casual",
        icon: Shirt,
    },
    {
        label: "在宅",
        description: "楽だけど急な外出にも対応できるコーデ",
        href: "/outfits/loading?tpo=home",
        icon: Home,
    },
    {
        label: "雨の日",
        description: "濡れにくさ・歩きやすさを重視",
        href: "/outfits/loading?tpo=rain",
        icon: Umbrella,
    },
];

export default function OutfitScenesPage() {
    return (
        <main className="min-h-screen bg-[#FAF8F5] px-5 py-6 text-[#2F2925]">
            <div className="mx-auto flex w-full max-w-[390px] flex-col gap-6">
                <section className="space-y-2">
                    <Badge className="bg-[#E8DDD3] text-[#6B4F3A] hover:bg-[#E8DDD3]">
                        Outfit Suggest
                    </Badge>
                    <h1 className="text-2xl font-semibold tracking-tight">
                        今日の予定を選んでください
                    </h1>
                    <p className="text-sm leading-6 text-[#6F6259]">
                        天気とシーンに合わせて、登録済みの服からおすすめコーデを提案します。
                    </p>
                </section>

                <section className="grid gap-3" aria-label="利用シーン一覧">
                    {scenes.map((scene) => {
                        const Icon = scene.icon;

                        return (
                            <Card
                                key={scene.label}
                                className="border-[#E7DDD3] bg-white/90 shadow-sm"
                            >
                                <CardHeader className="flex flex-row items-start gap-4 space-y-0">
                                    <div className="rounded-full bg-[#F0E8E0] p-3 text-[#6B4F3A]">
                                        <Icon aria-hidden="true" className="h-5 w-5" />
                                    </div>
                                    <div className="space-y-1">
                                        <CardTitle className="text-base">{scene.label}</CardTitle>
                                        <CardDescription className="text-sm leading-5">
                                            {scene.description}
                                        </CardDescription>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <Button
                                        asChild
                                        className="w-full bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
                                    >
                                        <Link
                                            href={scene.href}
                                            aria-label={`${scene.label}向けのコーデを提案する`}
                                        >
                                            このシーンで提案する
                                        </Link>
                                    </Button>
                                </CardContent>
                            </Card>
                        );
                    })}
                </section>

                <Button asChild variant="ghost" className="text-[#6B4F3A]">
                    <Link href="/">ホームへ戻る</Link>
                </Button>
            </div>
        </main>
    );
}