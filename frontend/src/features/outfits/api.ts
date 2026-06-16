import { apiClient } from "@/lib/api/client";
import { supabase } from "@/lib/auth";

import type {
  OutfitsListResponse,
  OutfitSuggestRequest,
  OutfitSuggestResponse,
} from "./types";

type GetOutfitsParams = {
  isFavorite?: boolean;
  limit?: number;
  offset?: number;
};

async function getAccessToken(tokenOverride?: string) {
  if (tokenOverride) {
    return tokenOverride;
  }

  const {
    data: { session },
  } = await supabase.auth.getSession();

  const token = session?.access_token;

  if (!token) {
    throw new Error("ログインが必要です");
  }

  return token;
}

export async function getOutfits(
  params: GetOutfitsParams = {},
  tokenOverride?: string,
): Promise<OutfitsListResponse> {
  const token = await getAccessToken(tokenOverride);
  const searchParams = new URLSearchParams();

  if (params.isFavorite !== undefined) {
    searchParams.set("is_favorite", String(params.isFavorite));
  }

  if (params.limit !== undefined) {
    searchParams.set("limit", String(params.limit));
  }

  if (params.offset !== undefined) {
    searchParams.set("offset", String(params.offset));
  }

  const query = searchParams.toString();

  return apiClient.get<OutfitsListResponse>(
    query ? `/outfits?${query}` : "/outfits",
    {
      token,
      cache: "no-store",
    },
  );
}

export async function suggestOutfit(
  payload: OutfitSuggestRequest,
): Promise<OutfitSuggestResponse> {
  const token = await getAccessToken();

  return apiClient.post<OutfitSuggestResponse>("/outfits/suggest", payload, {
    token,
    cache: "no-store",
  });
}
