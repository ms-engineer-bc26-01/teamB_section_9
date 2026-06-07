// frontend/src/lib/api/client.ts
import { apiFetch, type ApiRequestOptions } from "./fetcher";

type MutationOptions = Omit<ApiRequestOptions, "method" | "body">;

export const apiClient = {
  get: <T>(path: string, options?: ApiRequestOptions) =>
    apiFetch<T>(path, options),

  post: <T>(path: string, body?: unknown, options?: MutationOptions) =>
    apiFetch<T>(path, {
      ...options,
      method: "POST",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),

  put: <T>(path: string, body?: unknown, options?: MutationOptions) =>
    apiFetch<T>(path, {
      ...options,
      method: "PUT",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),

  patch: <T>(path: string, body?: unknown, options?: MutationOptions) =>
    apiFetch<T>(path, {
      ...options,
      method: "PATCH",
      body: body === undefined ? undefined : JSON.stringify(body),
    }),

  delete: <T>(path: string, options?: ApiRequestOptions) =>
    apiFetch<T>(path, {
      ...options,
      method: "DELETE",
    }),
};
