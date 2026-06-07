import type { ClothesListResponse } from "./types";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function fetchClothes(): Promise<ClothesListResponse> {
    const response = await fetch(`${API_BASE_URL}/clothes`, {
        headers: {
            Accept: "application/json",
            Authorization: "Bearer 123", //後でSupabase Authのトークン取得に差し替えます。
        },
        cache: "no-store",
    });

    if (!response.ok) {
        throw new Error("服一覧の取得に失敗しました");
    }

    return response.json();
}