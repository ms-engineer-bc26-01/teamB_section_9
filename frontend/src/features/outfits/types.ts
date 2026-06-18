import type { ClothingItem } from "@/features/clothes/types";

export type OutfitSuggestRequest = {
  tpo: string;
  date?: string;
  region_code?: string;
  clothing_ids?: string[];
  exclude_clothing_ids?: string[];
};

export type OutfitCreateItem = {
  name: string;
  role: string;
  color?: string | null;
  pattern?: string | null;
  display_order: number;
  clothes_id?: string | null;
};

export type OutfitCreateRequest = {
  tpo: string;
  region_code: string;
  comment?: string | null;
  is_favorite?: boolean;
  items: OutfitCreateItem[];
};

export type SuggestedOutfitItem = {
  clothes_id?: string | null;
  name?: string | null;
  role: string;
  color?: string | null;
  pattern?: string | null;
  display_order: number;
  clothing_item?: ClothingItem | null;
};

export type SuggestedOutfit = {
  id: string;
  user_id: string;
  tpo: string;
  region_code: string;
  // 保存済みコーデ（オンデマンド保存）では null。
  weather_summary: string | null;
  weather_temp_max: number | null;
  weather_temp_min: number | null;
  comment: string | null;
  coordinate_image_url: string | null;
  is_favorite: boolean;
  source: string;
  items: SuggestedOutfitItem[];
  created_at: string;
};

export type Region = {
  code: string;
  prefecture_code: string;
  prefecture_name: string;
  name: string;
  city: string;
  latitude: number;
  longitude: number;
};

export type OutfitSuggestResponse = {
  outfits: SuggestedOutfit[];
  weather_summary?: string;
  region_used?: Region;
  cached?: boolean;
};

export type OutfitsListResponse = {
  items: SuggestedOutfit[];
  total: number;
};

export function getSuggestedOutfitItemName(item: SuggestedOutfitItem) {
  return item.name ?? item.clothing_item?.name ?? "アイテム名未設定";
}

export function getSuggestedOutfitItemColor(item: SuggestedOutfitItem) {
  return item.color ?? item.clothing_item?.color ?? null;
}
