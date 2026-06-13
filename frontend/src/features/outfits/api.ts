import { apiClient } from "@/lib/api/client";
import { supabase } from "@/lib/auth";

import type { OutfitSuggestRequest, OutfitSuggestResponse } from "./types";

export async function suggestOutfit(
  payload: OutfitSuggestRequest,
): Promise<OutfitSuggestResponse> {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const token = session?.access_token;

  if (!token) {
    throw new Error("ログインが必要です");
  }

  return apiClient.post<OutfitSuggestResponse>("/outfits/suggest", payload, {
    token,
    cache: "no-store",
  });
}
