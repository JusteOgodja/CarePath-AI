import type { ApiError } from "@/lib/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const DEFAULT_TIMEOUT = 15000;

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export class ApiClientError extends Error implements ApiError {
  status: number;
  details?: unknown;

  constructor(status: number, message: string, details?: unknown) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.details = details;
  }
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit & { timeout?: number } = {}
): Promise<T> {
  const { timeout = DEFAULT_TIMEOUT, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...fetchOptions,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...fetchOptions.headers,
      },
    });

    if (!response.ok) {
      let errorBody: unknown;
      try {
        errorBody = await response.json();
      } catch {
        errorBody = await response.text();
      }
      const message =
        typeof errorBody === "object" && errorBody && "detail" in errorBody
          ? String((errorBody as { detail: unknown }).detail)
          : `Erreur HTTP ${response.status}`;
      throw new ApiClientError(response.status, message, errorBody);
    }

    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  } catch (error) {
    if (error instanceof ApiClientError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiClientError(0, "La requête a expiré (timeout)");
    }
    throw new ApiClientError(0, "Erreur réseau – le serveur est-il accessible ?");
  } finally {
    clearTimeout(timeoutId);
  }
}
