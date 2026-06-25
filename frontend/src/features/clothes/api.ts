import { apiClient } from "@/lib/api/client";
import { supabase } from "@/lib/auth";

import type {
  ClothingCreateRequest,
  ClothingItem,
  ClothingUploadUrlRequest,
  ClothingUploadUrlResponse,
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

function isUnauthorizedApiError(error: unknown) {
  if (!(error instanceof Error)) {
    return false;
  }

  return (
    error.message === "Not authenticated" ||
    error.message === "Invalid authentication credentials" ||
    error.message === "API Error: 401"
  );
}

async function handleClothesApiError<T>(
  request: () => Promise<T>,
  fallbackMessage: string,
) {
  try {
    return await request();
  } catch (error) {
    if (isUnauthorizedApiError(error)) {
      throw new Error("ログインが必要です", { cause: error });
    }

    throw new Error(fallbackMessage, { cause: error });
  }
}

export async function fetchClothes(): Promise<ClothesListResponse> {
  const token = await getAccessToken();

  return handleClothesApiError(
    () =>
      apiClient.get<ClothesListResponse>("/clothes?limit=100", {
        token,
        cache: "no-store",
      }),
    "服一覧の取得に失敗しました",
  );
}

export async function createClothing(
  payload: ClothingCreateRequest,
): Promise<ClothingItem> {
  const token = await getAccessToken();

  return handleClothesApiError(
    () =>
      apiClient.post<ClothingItem>("/clothes", payload, {
        token,
      }),
    "服の登録に失敗しました",
  );
}

export async function createClothingUploadUrl(
  payload: ClothingUploadUrlRequest,
): Promise<ClothingUploadUrlResponse> {
  const token = await getAccessToken();

  return handleClothesApiError(
    () =>
      apiClient.post<ClothingUploadUrlResponse>(
        "/clothes/upload-url",
        payload,
        {
          token,
        },
      ),
    "画像アップロードURLの取得に失敗しました",
  );
}
