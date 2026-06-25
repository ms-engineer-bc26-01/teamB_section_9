import { apiClient } from "@/lib/api/client";

export type Region = {
  code: string;
  prefecture_code: string;
  prefecture_name: string;
  name: string;
  city: string;
  latitude: number;
  longitude: number;
};

type RegionsResponse = {
  items: Region[];
};

export async function getRegions() {
  return apiClient.get<RegionsResponse>("/regions");
}

export function getRegionLabel(region: Pick<Region, "prefecture_name" | "name">) {
  return `${region.prefecture_name} ${region.name}`;
}

export function getRegionLabelByCode(regions: Region[], regionCode: string | null) {
  if (!regionCode) {
    return null;
  }

  const region = regions.find((item) => item.code === regionCode);

  return region ? getRegionLabel(region) : null;
}
