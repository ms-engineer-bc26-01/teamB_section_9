import Link from "next/link";
import {
  CalendarDays,
  ChevronRight,
  CloudSun,
  Shirt,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const weekdayLabels = ["日", "月", "火", "水", "木", "金", "土"];

const mockHomeData = {
  weatherLabel: "くもり時々晴れ",
  highTemperature: 18,
  lowTemperature: 12,
  precipitationProbability: 30,
  sceneLabel: "お仕事",
  clothesCount: 18,
  weeklyOutfitCount: 5,
};

const outfitItems = [
  "白シャツ",
  "ベージュのカーディガン",
  "濃紺デニム",
  "ローファー",
];

export default function HomeDashboard() {
  const today = new Date();
  const todayLabel = `${today.getMonth() + 1}月${today.getDate()}日(${weekdayLabels[today.getDay()]})`;
  const todayDateTime = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;

  return (
    <div className="space-y-5">
      <section aria-labelledby="home-heading" className="space-y-3">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-sm font-medium text-[#8C715C]">Climo</p>
            <h1
              id="home-heading"
              className="mt-1 text-2xl font-bold leading-tight text-[#2B2926]"
            >
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

      <section aria-labelledby="weather-heading" className="space-y-3">
        <h2 id="weather-heading" className="sr-only">
          今日の天気
        </h2>
        <time
          dateTime={todayDateTime}
          className="block text-center text-lg font-semibold text-[#2B2926]"
        >
          {todayLabel}
        </time>

        <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
          <CardContent className="flex items-center gap-8 px-5 py-5">
            <div className="flex size-24 shrink-0 items-center justify-center rounded-full bg-[#F6FAF8] text-[#2F6F63]">
              <CloudSun aria-hidden="true" size={56} />
            </div>

            <div className="space-y-1">
              <p className="text-lg font-bold text-[#2B2926]">
                {mockHomeData.weatherLabel}
              </p>
              <p className="text-2xl font-bold text-[#2B2926]">
                {mockHomeData.highTemperature}℃ / {mockHomeData.lowTemperature}℃
              </p>
              <p className="text-sm font-semibold text-[#4B3A2F]">
                降水確率 {mockHomeData.precipitationProbability}%
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles aria-hidden="true" size={18} className="text-[#C0784A]" />
            おすすめコーデ
          </CardTitle>
          <Badge className="w-fit bg-[#F4EEE8] px-4 py-1 text-sm font-semibold text-[#6B4F3A]">
            {mockHomeData.sceneLabel}
          </Badge>
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

          <Link
            href="/outfits/preview"
            aria-label={`${mockHomeData.sceneLabel}のコーデのポイントを見る`}
            className="flex items-center justify-center gap-3 py-3 text-sm font-bold text-[#2B2926]"
          >
            コーデのポイントを見る
            <ChevronRight aria-hidden="true" size={20} />
          </Link>
        </CardContent>
      </Card>

      <Link
        href="/outfits/scenes"
        aria-label="別のシーンで提案を見る"
        className="flex h-14 items-center justify-center gap-3 rounded-lg border border-[#E8DED4] bg-white text-base font-bold text-[#2B2926] shadow-sm hover:bg-[#FFFCF8]"
      >
        別のシーンで提案を見る
      </Link>

      <section
        aria-label="クローゼットサマリー"
        className="grid grid-cols-2 gap-3"
      >
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
              <CalendarDays
                aria-hidden="true"
                size={16}
                className="text-[#6B4F3A]"
              />
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
    </div>
  );
}
