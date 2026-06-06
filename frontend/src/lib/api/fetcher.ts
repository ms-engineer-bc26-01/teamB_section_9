import { env } from "@/lib/env";

type RequestOptions = RequestInit & {
  token?: string;
};

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
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
    const error = await response.json().catch(() => null);

    throw new Error(error?.message ?? `API Error: ${response.status}`);
  }

  return response.json();
}
