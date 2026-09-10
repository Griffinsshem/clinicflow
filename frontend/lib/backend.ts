import "server-only";

import type { ApiResponse } from "@/types/api";


const API_URL = process.env.API_URL;

if (!API_URL) {
  throw new Error("API_URL is not set. Copy .env.example to .env.local.");
}

const REQUEST_TIMEOUT_MS = 60_000;

export interface BackendResult<T> {
  status: number;
  body: ApiResponse<T>;
}

export async function callBackend<T>(
  path: string,
  init: RequestInit = {},
  token?: string | null,
): Promise<BackendResult<T>> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
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
