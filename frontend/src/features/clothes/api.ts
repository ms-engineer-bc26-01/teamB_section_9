import { supabase } from "@/lib/auth";

import type {
    ClothingCreateRequest,
    ClothingItem,
    ClothesListResponse,
} from "./types";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export async function fetchClothes(): Promise<ClothesListResponse> {
    const {
        data: { session },
    } = await supabase.auth.getSession();

    const token = session?.access_token;

    if (!token) {
        throw new Error("ログインが必要です");
    }

    const response = await fetch(`${API_BASE_URL}/clothes?limit=100`, {
        headers: {
            Accept: "application/json",
            Authorization: `Bearer ${token}`,
        },
        cache: "no-store",
    });

    if (response.status === 401) {
        throw new Error("ログインが必要です");
    }

    if (!response.ok) {
        throw new Error("服一覧の取得に失敗しました");
    }

    return response.json();
}

export async function createClothing(
    payload: ClothingCreateRequest,
): Promise<ClothingItem> {
    const {
        data: { session },
    } = await supabase.auth.getSession();

    const token = session?.access_token;

    if (!token) {
        throw new Error("ログインが必要です");
    }

    const response = await fetch(`${API_BASE_URL}/clothes`, {
        method: "POST",
        headers: {
            Accept: "application/json",
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
    });

    if (response.status === 401) {
        throw new Error("ログインが必要です");
    }

    if (!response.ok) {
        throw new Error("服の登録に失敗しました");
    }

    return response.json();
}
