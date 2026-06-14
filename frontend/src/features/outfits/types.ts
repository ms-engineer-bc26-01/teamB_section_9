import type { ClothingItem } from "@/features/clothes/types";

export type OutfitSuggestRequest = {
  tpo: string;
  date?: string;
  region_code?: string;
  clothing_ids?: string[];
  exclude_clothing_ids?: string[];
};

export type SuggestedOutfitItem = {
  clothes_id: string;
  role: string;
  display_order: number;
  clothing_item: ClothingItem;
};

export type SuggestedOutfit = {
  id: string;
  user_id: string;
  tpo: string;
  region_code: string;
  weather_summary: string;
  weather_temp_max: number | null;
  weather_temp_min: number | null;
  comment: string | null;
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
  weather_summary: string;
  region_used: Region;
  cached: boolean;
};

export type OutfitsListResponse = {
  items: SuggestedOutfit[];
  total: number;
};
