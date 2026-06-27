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
  // 提案時の天気を保存時に引き継ぐ（suggest レスポンスから転送）。
  weather_summary?: string | null;
  weather_temp_max?: number | null;
  weather_temp_min?: number | null;
  comment?: string | null;
  is_favorite?: boolean;
  items: OutfitCreateItem[];
};

export type OutfitUpdateRequest = {
  is_favorite: boolean;
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
  // region_code から解決した地域情報（名称表示用）。未定義コードは null。
  region?: Region | null;
  // 保存済みコーデ（オンデマンド保存）では null。
  weather_summary: string | null;
  weather_temp_max: number | null;
  weather_temp_min: number | null;
  comment: string | null;
  coordinate_image_url: string | null;
  is_favorite: boolean;
  source?: string;
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

// POST /outfits/suggest の生レスポンス内の outfit（BE `SuggestOutfit` と一致）。
// 保存前のため region / weather_* / source / coordinate_image_url は持たない。
// 地域名・天気は提案時点の値としてレスポンス top-level（region_used / weather_*）に入る。
export type SuggestOutfit = {
  id: string;
  user_id: string;
  tpo: string;
  region_code: string;
  comment: string | null;
  is_favorite: boolean;
  items: SuggestedOutfitItem[];
  created_at: string;
};

export type OutfitSuggestResponse = {
  // 生提案結果は SuggestOutfit（保存後の SuggestedOutfit とは別物）。
  outfits: SuggestOutfit[];
  region_used?: Region | null;
  weather_summary?: string | null;
  weather_temp_max?: number | null;
  weather_temp_min?: number | null;
  cached?: boolean;
};

// 保存後に sessionStorage 経由で詳細画面へ受け渡す結果。outfits は保存済みの
// SuggestedOutfit（region / weather_* を解決済み）。top-level の地域・天気は任意。
export type SavedSuggestionResult = {
  outfits: SuggestedOutfit[];
  // 提案に用いた地域。BE は返すが現状 FE 未使用（プレビュー地域表示で消費予定）。
  region_used?: Region | null;
  // 提案時の天気。保存（POST /outfits）時に引き継ぐ。
  weather_summary?: string | null;
  weather_temp_max?: number | null;
  weather_temp_min?: number | null;
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

// region_code から解決した地域の表示ラベル。履歴一覧 / 詳細で共通利用する。
// region が無い（未解決 / null）場合は null を返し、呼び出し側で非表示にする。
export function formatRegionLabel(region: Region | null | undefined) {
  if (!region) {
    return null;
  }

  return `${region.prefecture_name} ${region.name}`.trim() || null;
}
