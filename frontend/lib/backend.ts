import "server-only";

import type { ApiResponse } from "@/types/api";


const API_URL = process.env.API_URL;

if (!API_URL) {
  throw new Error("API_URL is not set. Copy .env.example to .env.local.");
}

const REQUEST_TIMEOUT_MS = 60_000;

/**
 * Shared with the Flask API. Sent with the visitor's IP so the API can
 * trust that header for rate limiting; a request without the secret is
 * attributed to its connecting address instead. Optional locally, where
 * there is only ever one visitor.
 */
const PROXY_SHARED_SECRET = process.env.PROXY_SHARED_SECRET;

export interface BackendResult<T> {
  status: number;
  body: ApiResponse<T>;
}

export async function callBackend<T>(
  path: string,
  init: RequestInit = {},
  token?: string | null,
  clientIp?: string | null,
): Promise<BackendResult<T>> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  if (clientIp && PROXY_SHARED_SECRET) {
    headers.set("X-Client-IP", clientIp);
    headers.set("X-Proxy-Secret", PROXY_SHARED_SECRET);
  }

  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers,
      cache: "no-store",
      signal: AbortSignal.timeout(REQUEST_TIMEOUT_MS),
    });

    const body = (await response.json()) as ApiResponse<T>;
    return { status: response.status, body };
  } catch (error) {
    console.error("Backend request failed:", path, error);
    return {
      status: 503,
      body: {
        success: false,
        message: "We can't reach the server right now. Please try again.",
      },
    };
  }
}
