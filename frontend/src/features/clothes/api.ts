import { apiClient } from "@/lib/api/client";
import { supabase } from "@/lib/auth";

import type {
  ClothingCreateRequest,
  ClothingItem,
  ClothesListResponse,
} from "./types";

async function getAccessToken() {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  const token = session?.access_token;

  if (!token) {
    throw new Error("ログインが必要です");
  }

  return token;
}

export async function fetchClothes(): Promise<ClothesListResponse> {
  const token = await getAccessToken();

  return apiClient.get<ClothesListResponse>("/clothes?limit=100", {
    token,
    cache: "no-store",
  });
}

export async function createClothing(
  payload: ClothingCreateRequest,
): Promise<ClothingItem> {
  const token = await getAccessToken();

  return apiClient.post<ClothingItem>("/clothes", payload, {
    token,
  });
}
