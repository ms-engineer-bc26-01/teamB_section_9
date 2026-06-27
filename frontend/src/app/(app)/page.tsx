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
import { getRegionLabelByCode, getRegions } from "@/features/regions/api";
import { getOutfits } from "@/features/outfits/api";
import { getSuggestedOutfitItemName } from "@/features/outfits/types";
import type { SuggestedOutfit } from "@/features/outfits/types";
import { apiClient } from "@/lib/api/client";
import { useAuthStore } from "@/stores/auth-store";

const weekdayLabels = ["日", "月", "火", "水", "木", "金", "土"];
const DEFAULT_REGION_CODE = "13_01";
const HOME_OUTFIT_EMPTY_MESSAGE =
  "まだ提案履歴がありません。シーンを選んでコーデを作成してください。";

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
  regionLabel: string | null;
  errorMessage: string | null;
};

type HomeOutfitState = {
  outfit: SuggestedOutfit | null;
  errorMessage: string | null;
};

type HomeClothesState = {
  count: number | null;
  errorMessage: string | null;
};

type Summary = {
  total: number;
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

  const regionLabelPromise = getRegions()
    .then((regionsResponse) =>
      getRegionLabelByCode(regionsResponse.items, regionCode),
    )
    .catch(() => null);

  const weather = await getWeatherForecast(token, regionCode);

  return {
    weather,
    regionLabelPromise,
  };
}

async function fetchHomeClothesCount(token: string) {
  const clothes = await apiClient.get<Summary>("/clothes?limit=1", { token });
  return clothes.total;
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

function getOutfitImageUrl(outfit: SuggestedOutfit | null) {
  if (!outfit) {
    return null;
  }

  if (outfit.coordinate_image_url) {
    return outfit.coordinate_image_url;
  }

  const imageItem = outfit.items.find(
    (item) =>
      item.clothing_item?.thumbnail_url ?? item.clothing_item?.image_url,
  );

  return (
    imageItem?.clothing_item?.thumbnail_url ??
    imageItem?.clothing_item?.image_url ??
    null
  );
}

export default function HomeDashboard() {
  const session = useAuthStore((state) => state.session);
  const isInitialized = useAuthStore((state) => state.isInitialized);
  const [weatherState, setWeatherState] = useState<HomeWeatherState>({
    weather: null,
    regionLabel: null,
    errorMessage: null,
  });
  const [outfitState, setOutfitState] = useState<HomeOutfitState>({
    outfit: null,
    errorMessage: null,
  });
  const [clothesState, setClothesState] = useState<HomeClothesState>({
    count: null,
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
      .then(({ weather, regionLabelPromise }) => {
        if (!isMounted) {
          return;
        }

        setWeatherState({
          weather,
          regionLabel: null,
          errorMessage: null,
        });

        void regionLabelPromise.then((regionLabel) => {
          if (!isMounted) {
            return;
          }

          setWeatherState((current) => ({
            ...current,
            regionLabel,
          }));
        });
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }

        setWeatherState({
          weather: null,
          regionLabel: null,
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

    fetchHomeClothesCount(token)
      .then((count) => {
        if (!isMounted) {
          return;
        }

        setClothesState({
          count,
          errorMessage: null,
        });
      })
      .catch(() => {
        if (!isMounted) {
          return;
        }

        setClothesState({
          count: null,
          errorMessage: "登録済み件数を取得できませんでした。",
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
              : HOME_OUTFIT_EMPTY_MESSAGE,
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
  const regionLabel = token ? weatherState.regionLabel : null;
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
  const latestOutfitImageUrl = getOutfitImageUrl(latestOutfit);
  const isOutfitLoading =
    Boolean(token) &&
    isInitialized &&
    outfitState.outfit === null &&
    outfitErrorMessage === null;
  const shouldShowCreateOutfitLinks =
    Boolean(token) &&
    !isOutfitLoading &&
    latestOutfit === null &&
    outfitState.errorMessage === HOME_OUTFIT_EMPTY_MESSAGE;
  const isClothesCountLoading =
    Boolean(token) &&
    isInitialized &&
    clothesState.count === null &&
    clothesState.errorMessage === null;
  const clothesCountText =
    isClothesCountLoading || clothesState.errorMessage
      ? "-"
      : String(clothesState.count ?? 0);

  return (
    <div className="space-y-5">
      <h1 className="sr-only">
        Climo | 天気と手持ち服から今日のコーデを提案するAIスタイリスト
      </h1>
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
          {latestOutfitImageUrl ? (
            <div
              aria-label={`${sceneLabel}のコーデ画像`}
              className="aspect-square w-full rounded-lg border border-[#EFE5DC] bg-[#F4EEE8] bg-contain bg-center bg-no-repeat"
              role="img"
              style={{ backgroundImage: `url(${latestOutfitImageUrl})` }}
            />
          ) : (
            <div className="flex aspect-square w-full items-center justify-center rounded-lg border border-[#EFE5DC] bg-[#FFFCF8] px-3 py-3 text-center text-sm leading-6 text-[#6F6258]">
              コーデ画像は準備中です。アイテム一覧とコーデのポイントは確認できます。
            </div>
          )}

          {latestOutfitItems.length > 0 ? (
            <div className="grid grid-cols-2 gap-2">
              {latestOutfitItems.map((item) => (
                <div
                  key={`${item.role}-${item.display_order}`}
                  className="rounded-lg border border-[#EFE5DC] bg-[#FFFCF8] px-3 py-3 text-sm font-medium text-[#4B3A2F]"
                >
                  <span className="block text-xs font-semibold text-[#8C715C]">
                    {item.role}
                  </span>
                  <span className="mt-1 block">{getSuggestedOutfitItemName(item)}</span>
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

          {shouldShowCreateOutfitLinks ? (
            <div className="grid gap-2 sm:grid-cols-2">
              <Link
                href="/outfits/scenes"
                className="flex min-h-11 items-center justify-center rounded-lg border border-[#8C715C] bg-white px-3 py-2 text-center text-sm font-bold text-[#6B4F3A] hover:bg-[#FFFCF8]"
              >
                シーンを選んで作成
              </Link>
              <Link
                href="/outfits/closet"
                className="flex min-h-11 items-center justify-center rounded-lg bg-[#6B4F3A] px-3 py-2 text-center text-sm font-bold text-white hover:bg-[#5A4231]"
              >
                クローゼット服で提案
              </Link>
            </div>
          ) : null}

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

          {latestOutfit ? (
            <Link
              href={`/outfits/preview?id=${latestOutfit.id}`}
              aria-label={`${sceneLabel}のコーデのポイントを見る`}
              className="flex items-center justify-center gap-3 py-3 text-sm font-bold text-[#2B2926]"
            >
              コーデのポイントを見る
              <ChevronRight aria-hidden="true" size={20} />
            </Link>
          ) : null}
        </CardContent>
      </Card>

      <Card className="rounded-lg border border-[#E8DED4] shadow-sm">
        <CardContent className="flex items-center gap-8 px-5 py-5">
          <div className="flex size-24 shrink-0 items-center justify-center rounded-full bg-[#F6FAF8] text-[#2F6F63]">
            {renderWeatherIcon(weatherCode, 56)}
          </div>

          <div className="space-y-1">
            <p className="text-lg font-bold text-[#2B2926]">{weatherLabel}</p>
            <p className="text-sm font-semibold text-[#6F6258]">
              地点：{isWeatherLoading ? "確認中" : regionLabel ?? "-"}
            </p>
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

      <Link
        href="/outfits/scenes"
        aria-label="別のシーンで提案を見る"
        className="flex h-14 items-center justify-center gap-3 rounded-lg border border-[#E8DED4] bg-white text-base font-bold text-[#2B2926] shadow-sm hover:bg-[#FFFCF8]"
      >
        別のシーンで提案を見る
      </Link>

      <Link
        href="/outfits/closet"
        aria-label="クローゼット服で提案を見る"
        className="flex h-14 items-center justify-center gap-3 rounded-lg border border-[#E8DED4] bg-white text-base font-bold text-[#2B2926] shadow-sm hover:bg-[#FFFCF8]"
      >
        <Shirt aria-hidden="true" size={20} className="text-[#6B4F3A]" />
        クローゼット服で提案を見る
      </Link>

      <section
        aria-label="クローゼットサマリー"
        className="grid grid-cols-2 gap-3"
      >
        <Link
          href="/clothes"
          aria-label="登録済みの服一覧を見る"
          className="block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2F6F63] focus-visible:ring-offset-2"
        >
          <Card className="h-full rounded-lg border border-[#E8DED4] transition-colors hover:bg-[#FFFCF8]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <Shirt
                  aria-hidden="true"
                  size={16}
                  className="text-[#6B4F3A]"
                />
                登録済み
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-3xl font-bold text-[#2B2926]">
                {clothesCountText}
              </p>
              <p className="mt-1 text-xs text-[#8C715C]">クローゼット内の服</p>
            </CardContent>
          </Card>
        </Link>

        <Link
          href="/outfits"
          aria-label="提案履歴を見る"
          className="block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#2F6F63] focus-visible:ring-offset-2"
        >
          <Card className="h-full rounded-lg border border-[#E8DED4] transition-colors hover:bg-[#FFFCF8]">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-sm">
                <CalendarDays
                  aria-hidden="true"
                  size={16}
                  className="text-[#6B4F3A]"
                />
                提案履歴
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm font-semibold text-[#2B2926]">一覧を見る</p>
              <p className="mt-1 text-xs text-[#8C715C]">保存済みのコーデ</p>
            </CardContent>
          </Card>
        </Link>
      </section>
    </div>
  );
}
