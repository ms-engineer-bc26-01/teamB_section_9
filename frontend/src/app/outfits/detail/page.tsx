// frontend/src/app/outfits/detail/page.tsx

import Link from "next/link";
import { CalendarDays, CloudSun, Heart, RefreshCw, Shirt } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

const outfitItems = [
    { role: "トップス", name: "白シャツ" },
    { role: "ボトムス", name: "ベージュのワイドパンツ" },
    { role: "羽織り", name: "薄手のブラウンカーディガン" },
    { role: "靴", name: "ローファー" },
];

export default function OutfitDetailPage() {
    return (
        <main className="min-h-screen bg-[#FAF8F5] px-5 py-6 text-[#2F2925]">
            <div className="mx-auto flex w-full max-w-[390px] flex-col gap-5">
                <section className="space-y-2">
                    <Badge className="bg-[#E8DDD3] text-[#6B4F3A] hover:bg-[#E8DDD3]">
                        Today&apos;s Outfit
                    </Badge>
                    <h1 className="text-2xl font-semibold tracking-tight">
                        今日のおすすめコーデ
                    </h1>
                    <p className="text-sm leading-6 text-[#6F6259]">
                        気温差に対応しやすい、きちんと感のある組み合わせです。
                    </p>
                </section>

                <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
                    <CardHeader className="space-y-3">
                        <div className="flex items-center gap-2 text-sm text-[#6F6259]">
                            <CloudSun aria-hidden="true" className="h-4 w-4" />
                            <span>晴れ時々くもり / 最高24℃・最低17℃</span>
                        </div>
                        <div className="flex items-center gap-2 text-sm text-[#6F6259]">
                            <CalendarDays aria-hidden="true" className="h-4 w-4" />
                            <span>オフィス・外出あり</span>
                        </div>
                    </CardHeader>
                </Card>

                <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2 text-lg">
                            <Shirt aria-hidden="true" className="h-5 w-5 text-[#6B4F3A]" />
                            アイテム一覧
                        </CardTitle>
                        <CardDescription>
                            登録済みの服から選ばれた組み合わせです。
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-3">
                        {outfitItems.map((item) => (
                            <div
                                key={item.role}
                                className="flex items-center justify-between rounded-xl bg-[#FAF8F5] px-4 py-3"
                            >
                                <span className="text-sm text-[#6F6259]">{item.role}</span>
                                <span className="text-sm font-medium">{item.name}</span>
                            </div>
                        ))}
                    </CardContent>
                </Card>

                <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-lg">コーデのポイント</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-sm leading-6 text-[#6F6259]">
                            朝晩は少し肌寒いため、薄手のカーディガンを足しています。
                            白シャツとベージュのパンツで清潔感を出しつつ、
                            ブラウン系の羽織りでやわらかい印象にまとめています。
                        </p>
                    </CardContent>
                </Card>

                <div className="grid grid-cols-2 gap-3">
                    <Button
                        variant="outline"
                        className="border-[#D8C9BB] bg-white text-[#6B4F3A]"
                        aria-label="このコーデをお気に入りに登録する"
                    >
                        <Heart aria-hidden="true" className="mr-2 h-4 w-4" />
                        保存
                    </Button>

                    <Button
                        asChild
                        className="bg-[#6B4F3A] text-white hover:bg-[#5A4231]"
                    >
                        <Link
                            href="/outfits/loading?tpo=business"
                            aria-label="別のコーデを再提案する"
                        >
                            <RefreshCw aria-hidden="true" className="mr-2 h-4 w-4" />
                            別案
                        </Link>
                    </Button>
                </div>

                <Button asChild variant="ghost" className="text-[#6B4F3A]">
                    <Link href="/">ホームへ戻る</Link>
                </Button>
            </div>
        </main>
    );
}