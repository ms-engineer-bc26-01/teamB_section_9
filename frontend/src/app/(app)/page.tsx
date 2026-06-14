"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CalendarDays,
  ChevronRight,
  Cloud,
  CloudDrizzle,
  CloudFog,
  CloudLightning,
  CloudRain,
  CloudSnow,
  CloudSun,
  Shirt,
  Sun,
  Sparkles,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  getWeatherForecast,
  type WeatherForecast,
} from "@/features/weather/api";
import { getOutfits } from "@/features/outfits/api";
import type { SuggestedOutfit } from "@/features/outfits/types";
import { apiClient } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

const weekdayLabels = ["日", "月", "火", "水", "木", "金", "土"];
const DEFAULT_REGION_CODE = "13_01";

const mockHomeData = {
  clothesCount: 18,
  weeklyOutfitCount: 5,
};

const tpoSceneLabels: Record<string, string> = {
  business: "お仕事",
  casual: "カジュアル",
  formal: "フォーマル",
  ceremony: "セレモニー",
  leisure: "レジャー",
};

type UserProfile = {
  default_region_code: string | null;
};

type HomeWeatherState = {
  weather: WeatherForecast | null;
  errorMessage: string | null;
};

type HomeOutfitState = {
  outfit: SuggestedOutfit | null;
  errorMessage: string | null;
};

function getWeatherLabel(weatherCode: number) {
  if (weatherCode === 0) {
    return "快晴";
  }

  if (weatherCode === 1) {
    return "晴れ";
  }

  if (weatherCode === 2) {
    return "くもり時々晴れ";
  }

  if (weatherCode === 3) {
    return "くもり";
  }

  if ([45, 48].includes(weatherCode)) {
    return "霧";
  }

  if ([51, 53, 55, 56, 57].includes(weatherCode)) {
    return "霧雨";
  }

  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(weatherCode)) {
    return "雨";
  }

  if ([71, 73, 75, 77, 85, 86].includes(weatherCode)) {
    return "雪";
  }

  if ([95, 96, 99].includes(weatherCode)) {
    return "雷雨";
  }

  return "不明";
}

function renderWeatherIcon(weatherCode: number | null, size: number) {
  if (weatherCode === null) {
    return <CloudSun aria-hidden="true" size={size} />;
  }

  if (weatherCode === 0 || weatherCode === 1) {
    return <Sun aria-hidden="true" size={size} />;
  }

  if (weatherCode === 2) {
    return <CloudSun aria-hidden="true" size={size} />;
  }

  if (weatherCode === 3) {
    return <Cloud aria-hidden="true" size={size} />;
  }

  if ([45, 48].includes(weatherCode)) {
    return <CloudFog aria-hidden="true" size={size} />;
  }

  if ([51, 53, 55, 56, 57].includes(weatherCode)) {
    return <CloudDrizzle aria-hidden="true" size={size} />;
  }

  if ([61, 63, 65, 66, 67, 80, 81, 82].includes(weatherCode)) {
    return <CloudRain aria-hidden="true" size={size} />;
  }

  if ([71, 73, 75, 77, 85, 86].includes(weatherCode)) {
    return <CloudSnow aria-hidden="true" size={size} />;
  }

  if ([95, 96, 99].includes(weatherCode)) {
    return <CloudLightning aria-hidden="true" size={size} />;
  }

  return <CloudSun aria-hidden="true" size={size} />;
}

async function fetchHomeWeather(token: string) {
  const profile = await apiClient.get<UserProfile>("/auth/me", { token });
  const regionCode = profile.default_region_code ?? DEFAULT_REGION_CODE;

  return getWeatherForecast(token, regionCode);
}

function formatOutfitComment(comment: string | null | undefined) {
  if (!comment) {
    return null;
  }

  return comment
    .replace(/^#{1,6}\s*/gm, "")
    .replace(/\*\*/g, "")
    .trim();
}

export default function HomeDashboard() {
  const session = useAuthStore((state) => state.session);
  const isInitialized = useAuthStore((state) => state.isInitialized);
  const [weatherState, setWeatherState] = useState<HomeWeatherState>({
    weather: null,
    errorMessage: null,
  });
  const [outfitState, setOutfitState] = useState<HomeOutfitState>({
    outfit: null,
    errorMessage: null,
  });

  useEffect(() => {
    if (!isInitialized) {
      return;
    }

    const token = session?.access_token;

    if (!token) {
      return;
    }

    let isMounted = true;

    fetchHomeWeather(token)
      .then((weather) => {
        if (!isMounted) {
          return;
        }

        setWeatherState({
          weather,
          errorMessage: null,
        });
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }

        setWeatherState({
          weather: null,
          errorMessage: "天気情報を取得できませんでした。",
        });
      });

    return () => {
      isMounted = false;
    };
  }, [isInitialized, session?.access_token]);

  useEffect(() => {
    if (!isInitialized) {
      return;
    }

    const token = session?.access_token;

    if (!token) {
      return;
    }

    let isMounted = true;

    getOutfits({ limit: 1 }, token)
      .then((response) => {
        if (!isMounted) {
          return;
        }

        setOutfitState({
          outfit: response.items[0] ?? null,
          errorMessage:
            response.items.length > 0
              ? null
              : "まだ提案履歴がありません。シーンを選んでコーデを作成してください。",
        });
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }

        setOutfitState({
          outfit: null,
          errorMessage: "おすすめコーデを取得できませんでした。",
        });
      });

    return () => {
      isMounted = false;
    };
  }, [isInitialized, session?.access_token]);

  const today = new Date();
  const token = session?.access_token;
  const todayLabel = `${today.getMonth() + 1}月${today.getDate()}日(${weekdayLabels[today.getDay()]})`;
  const todayDateTime = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
  const weather = token ? weatherState.weather : null;
  const todayForecast = weather?.daily[0] ?? null;
  const hasWeather = weather !== null && todayForecast !== null;
  const errorMessage = token
    ? weatherState.errorMessage
    : isInitialized
      ? "ログインすると天気を表示できます。"
      : null;
  const weatherLabel = weather
    ? getWeatherLabel(weather.current.weather_code)
    : errorMessage
      ? "天気情報は未取得"
      : "天気を確認中";
  const highTemperature = hasWeather
    ? Math.round(todayForecast.temperature_max)
    : null;
  const lowTemperature = hasWeather
    ? Math.round(todayForecast.temperature_min)
    : null;
  const precipitationProbability =
    todayForecast?.precipitation_probability_max ??
    weather?.current.precipitation_probability ??
    null;
  const isWeatherLoading =
    Boolean(token) &&
    isInitialized &&
    weatherState.weather === null &&
    weatherState.errorMessage === null;
  const weatherCode = weather?.current.weather_code ?? null;
  const temperatureText =
    highTemperature !== null && lowTemperature !== null
      ? `${highTemperature}℃ / ${lowTemperature}℃`
      : "-";
  const precipitationText =
    precipitationProbability !== null ? `${precipitationProbability}%` : "-";
  const latestOutfit = outfitState.outfit;
  const outfitErrorMessage = token
    ? outfitState.errorMessage
    : isInitialized
      ? "ログインするとおすすめコーデを表示できます。"
      : null;
  const latestOutfitItems =
    latestOutfit?.items
      .toSorted((a, b) => a.display_order - b.display_order)
      .slice(0, 4) ?? [];
  const sceneLabel = latestOutfit
    ? tpoSceneLabels[latestOutfit.tpo] ?? latestOutfit.tpo
    : "最新の提案";
  const outfitComment = formatOutfitComment(latestOutfit?.comment);
  const isOutfitLoading =
    Boolean(token) &&
    isInitialized &&
    outfitState.outfit === null &&
    outfitErrorMessage === null;

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
            {renderWeatherIcon(weatherCode, 25)}
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
              {renderWeatherIcon(weatherCode, 56)}
            </div>

            <div className="space-y-1">
              <p className="text-lg font-bold text-[#2B2926]">{weatherLabel}</p>
              <p className="text-2xl font-bold text-[#2B2926]">
                {isWeatherLoading ? "-" : temperatureText}
              </p>
              <p className="text-sm font-semibold text-[#4B3A2F]">
                降水確率 {isWeatherLoading ? "-" : precipitationText}
              </p>
              {errorMessage ? (
                <p className="text-sm text-[#8C3D2F]">{errorMessage}</p>
              ) : null}
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
            {sceneLabel}
          </Badge>
        </CardHeader>
        <CardContent className="space-y-4">
          {latestOutfitItems.length > 0 ? (
            <div className="grid grid-cols-2 gap-2">
              {latestOutfitItems.map((item) => (
                <div
                  key={`${item.role}-${item.clothes_id}`}
                  className="rounded-lg border border-[#EFE5DC] bg-[#FFFCF8] px-3 py-3 text-sm font-medium text-[#4B3A2F]"
                >
                  <span className="block text-xs font-semibold text-[#8C715C]">
                    {item.role}
                  </span>
                  <span className="mt-1 block">{item.clothing_item.name}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="rounded-lg border border-[#EFE5DC] bg-[#FFFCF8] px-3 py-3 text-sm leading-6 text-[#6F6258]">
              {isOutfitLoading
                ? "おすすめコーデを読み込んでいます。"
                : outfitErrorMessage}
            </p>
          )}

          {latestOutfit ? (
            <div className="flex flex-wrap gap-2">
              <Badge className="bg-[#EAF4F0] text-[#2F6F63]">
                {latestOutfit.weather_temp_max !== null
                  ? `最高 ${Math.round(latestOutfit.weather_temp_max)}℃`
                  : "天気に合わせた提案"}
              </Badge>
              <Badge className="bg-[#F4EEE8] text-[#6B4F3A]">
                {latestOutfit.weather_temp_min !== null
                  ? `最低 ${Math.round(latestOutfit.weather_temp_min)}℃`
                  : sceneLabel}
              </Badge>
              {latestOutfit.is_favorite ? (
                <Badge variant="outline">お気に入り</Badge>
              ) : null}
            </div>
          ) : null}

          {outfitComment ? (
            <p className="line-clamp-2 text-sm leading-6 text-[#6F6258]">
              {outfitComment}
            </p>
          ) : null}

          <Link
            href="/outfits/preview"
            aria-label={`${sceneLabel}のコーデのポイントを見る`}
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
