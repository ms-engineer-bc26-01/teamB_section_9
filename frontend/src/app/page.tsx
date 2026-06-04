import Link from "next/link";
import { CalendarDays, CloudSun, Shirt, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const mockHomeData = {
  weather: "曇り時々晴れ / 22度 / 仕事",
  clothesCount: 18,
  weeklyOutfitCount: 5,
};

const outfitItems = ["白シャツ", "ベージュのカーディガン", "濃紺デニム", "ローファー"];

export default function Home() {
  return (
    <main className="space-y-5">
      <section className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-[#8C715C]">Climo</p>
            <h1 className="mt-1 text-2xl font-bold leading-tight text-[#2B2926]">
              今日の天気に合う服を選びましょう
            </h1>
          </div>
          <div className="flex size-12 shrink-0 items-center justify-center rounded-full bg-[#EAF4F0] text-[#2F6F63]">
            <CloudSun aria-hidden="true" size={25} />
          </div>
        </div>
        <p className="text-sm leading-6 text-[#6F6258]">
          クローゼットの服と天気をもとに、外出前のコーデ選びを手早くサポートします。
        </p>
      </section>

      <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles aria-hidden="true" size={18} className="text-[#C0784A]" />
            おすすめコーデ
          </CardTitle>
          <CardDescription>{mockHomeData.weather}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-2">
            {outfitItems.map((item) => (
              <div
                key={item}
                className="rounded-lg border border-[#EFE5DC] bg-[#FFFCF8] px-3 py-3 text-sm font-medium text-[#4B3A2F]"
              >
                {item}
              </div>
            ))}
          </div>

          <div className="flex flex-wrap gap-2">
            <Badge className="bg-[#EAF4F0] text-[#2F6F63]">快適</Badge>
            <Badge className="bg-[#F4EEE8] text-[#6B4F3A]">きれいめ</Badge>
            <Badge variant="outline">羽織りあり</Badge>
          </div>

          <Button
            asChild
            className="h-11 w-full bg-[#5A4333] text-white hover:bg-[#4A372A]"
          >
            <Link
              href="/outfits/preview"
              aria-label={`${mockHomeData.weather}におすすめのコーデ詳細を見る`}
            >
              このコーデを見る
            </Link>
          </Button>
        </CardContent>
      </Card>

      <section className="grid grid-cols-2 gap-3">
        <Card className="rounded-lg border border-[#E8DED4]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <Shirt aria-hidden="true" size={16} className="text-[#6B4F3A]" />
              登録済み
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-[#2B2926]">
              {mockHomeData.clothesCount}
            </p>
            <p className="mt-1 text-xs text-[#8C715C]">クローゼット内の服</p>
          </CardContent>
        </Card>

        <Card className="rounded-lg border border-[#E8DED4]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <CalendarDays aria-hidden="true" size={16} className="text-[#6B4F3A]" />
              今週
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-[#2B2926]">
              {mockHomeData.weeklyOutfitCount}
            </p>
            <p className="mt-1 text-xs text-[#8C715C]">提案されたコーデ</p>
          </CardContent>
        </Card>
      </section>

      <div className="flex gap-2">
        <Button asChild variant="outline" className="h-10 flex-1 border-[#D9C9BA] bg-white">
          <Link href="/clothes/new">服を登録</Link>
        </Button>
        <Button asChild variant="outline" className="h-10 flex-1 border-[#D9C9BA] bg-white">
          <Link href="/login">ログイン</Link>
        </Button>
      </div>
    </main>
  );
}