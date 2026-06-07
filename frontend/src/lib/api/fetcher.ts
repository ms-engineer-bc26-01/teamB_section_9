// frontend/src/lib/api/fetcher.ts
import { env } from "@/lib/env";

export type ApiRequestOptions = RequestInit & {
  token?: string;
};

export async function apiFetch<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { token, headers, ...rest } = options;
  const normalizedHeaders = new Headers(headers);

  if (token) {
    normalizedHeaders.set("Authorization", `Bearer ${token}`);
  }

  const hasBody = rest.body != null;

  if (hasBody && !normalizedHeaders.has("Content-Type")) {
    normalizedHeaders.set("Content-Type", "application/json");
  }

  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...rest,
    headers: normalizedHeaders,
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => null);
    const detail =
      typeof errorBody?.detail === "string"
        ? errorBody.detail
        : Array.isArray(errorBody?.detail)
          ? JSON.stringify(errorBody.detail)
          : null;

    throw new Error(
      errorBody?.message ?? detail ?? `API Error: ${response.status}`,
    );
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  const contentType = response.headers.get("Content-Type");

  if (!contentType?.includes("application/json")) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
