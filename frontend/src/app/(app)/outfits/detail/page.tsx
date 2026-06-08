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

type OutfitItem = {
  role: string;
  name: string;
};

type OutfitMock = {
  title: string;
  lead: string;
  scene: string;
  weather: string;
  items: OutfitItem[];
  comment: string;
};

const outfitData: Record<string, OutfitMock> = {
  business: {
    title: "オフィス向けコーデ",
    lead: "外出予定にも対応しやすい、きちんと感のある組み合わせです。",
    scene: "オフィス・外出あり",
    weather: "晴れ時々くもり / 最高24℃・最低17℃",
    items: [
      { role: "トップス", name: "白シャツ" },
      { role: "ボトムス", name: "ベージュのワイドパンツ" },
      { role: "羽織り", name: "薄手のブラウンカーディガン" },
      { role: "靴", name: "ローファー" },
    ],
    comment:
      "朝晩は少し肌寒いため、薄手のカーディガンを足しています。白シャツとベージュのパンツで清潔感を出しつつ、ブラウン系の羽織りでやわらかい印象にまとめています。",
  },
  casual: {
    title: "カジュアル向けコーデ",
    lead: "動きやすさと清潔感を両立した、休日向けの組み合わせです。",
    scene: "休日・買い物・保育園送迎",
    weather: "晴れ / 最高25℃・最低18℃",
    items: [
      { role: "トップス", name: "ボーダーカットソー" },
      { role: "ボトムス", name: "デニムパンツ" },
      { role: "羽織り", name: "ライトベージュのシャツジャケット" },
      { role: "靴", name: "白スニーカー" },
    ],
    comment:
      "歩く時間が長くても疲れにくいよう、スニーカーを中心にした組み合わせです。ボーダーとデニムでカジュアルにしつつ、淡い羽織りで全体を軽く見せています。",
  },
  home: {
    title: "在宅向けコーデ",
    lead: "楽に過ごせて、急な外出にも対応しやすい組み合わせです。",
    scene: "在宅ワーク・近所への外出",
    weather: "くもり / 最高23℃・最低17℃",
    items: [
      { role: "トップス", name: "やわらかい白ニット" },
      { role: "ボトムス", name: "ストレッチパンツ" },
      { role: "羽織り", name: "ロングカーディガン" },
      { role: "靴", name: "フラットシューズ" },
    ],
    comment:
      "長時間座っていても疲れにくいよう、締め付けの少ないアイテムを選んでいます。外に出る時もカーディガンを羽織るだけで整った印象になります。",
  },
  rain: {
    title: "雨の日向けコーデ",
    lead: "濡れにくさと歩きやすさを重視した、雨の日向けの組み合わせです。",
    scene: "雨の日・移動あり",
    weather: "雨 / 最高21℃・最低16℃",
    items: [
      { role: "トップス", name: "ネイビーのカットソー" },
      { role: "ボトムス", name: "黒のテーパードパンツ" },
      { role: "羽織り", name: "撥水ライトコート" },
      { role: "靴", name: "レイン対応ローファー" },
    ],
    comment:
      "雨の日は裾が濡れにくいテーパードパンツと、撥水性のある羽織りを選んでいます。足元は滑りにくく、きれいめにも見える靴でまとめています。",
  },
};

type Props = {
  searchParams: Promise<{
    tpo?: string;
  }>;
};

export default async function OutfitDetailPage({ searchParams }: Props) {
  const { tpo = "business" } = await searchParams;
  const currentTpo = Object.hasOwn(outfitData, tpo) ? tpo : "business";
  const currentOutfit = outfitData[currentTpo];

  return (
    <div className="min-h-screen bg-[#FAF8F5] px-5 py-6 text-[#2F2925]">
      <div className="mx-auto flex w-full max-w-[390px] flex-col gap-5">
        <section className="space-y-2">
          <Badge className="bg-[#E8DDD3] text-[#6B4F3A] hover:bg-[#E8DDD3]">
            Today&apos;s Outfit
          </Badge>
          <h1 className="text-2xl font-semibold tracking-tight">
            {currentOutfit.title}
          </h1>
          <p className="text-sm leading-6 text-[#6F6259]">
            {currentOutfit.lead}
          </p>
        </section>

        <Card className="border-[#E7DDD3] bg-white/90 shadow-sm">
          <CardHeader className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-[#6F6259]">
              <CloudSun aria-hidden="true" className="h-4 w-4" />
              <span>{currentOutfit.weather}</span>
            </div>
            <div className="flex items-center gap-2 text-sm text-[#6F6259]">
              <CalendarDays aria-hidden="true" className="h-4 w-4" />
              <span>{currentOutfit.scene}</span>
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
            {currentOutfit.items.map((item) => (
              <div
                key={`${item.role}-${item.name}`}
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
              {currentOutfit.comment}
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
              href={`/outfits/loading?tpo=${encodeURIComponent(currentTpo)}`}
              aria-label="同じシーンで別のコーデを再提案する"
            >
              <RefreshCw aria-hidden="true" className="mr-2 h-4 w-4" />
              別案
            </Link>
          </Button>
        </div>

        <Button asChild variant="ghost" className="text-[#6B4F3A]">
          <Link href="/home">ホームへ戻る</Link>
        </Button>
      </div>
    </div>
  );
}
