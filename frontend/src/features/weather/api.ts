import type { Region } from "@/features/outfits/types";
import { apiClient } from "@/lib/api/client";

export type WeatherForecast = {
  region_code: string;
  region?: Region | null;
  current: {
    temperature_2m: number;
    weather_code: number;
    precipitation_probability: number;
  };
  daily: Array<{
    date: string;
    temperature_max: number;
    temperature_min: number;
    weather_code: number;
    precipitation_probability_max: number;
  }>;
  cached: boolean;
};

export function getWeatherForecast(token: string, regionCode: string) {
  const searchParams = new URLSearchParams({
    region_code: regionCode,
  });

  return apiClient.get<WeatherForecast>(
    `/weather/forecast?${searchParams.toString()}`,
    {
      token,
      cache: "no-store",
    },
  );
}
