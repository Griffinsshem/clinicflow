import type { ApiResponse, PaginationMeta } from "@/types/api";


const PROXY_BASE = "/api/proxy";

export class ApiError extends Error {
  readonly status: number;
  readonly fieldErrors: Record<string, string>;

  constructor(
    message: string,
    status: number,
    fieldErrors: Record<string, string> = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.fieldErrors = fieldErrors;
  }
}

export interface ApiResult<T> {
  data: T;
  meta?: PaginationMeta;
}

async function request<T>(
  path: string,
  init: RequestInit = {},
): Promise<ApiResult<T>> {
  let response: Response;

  try {
    response = await fetch(`${PROXY_BASE}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init.headers },
    });
  } catch {
    throw new ApiError(
      "You appear to be offline. Check your connection and try again.",
      0,
    );
  }

  const body = (await response.json().catch(() => null)) as ApiResponse<T> | null;

  if (!body) {
    throw new ApiError("Something went wrong. Please try again.", response.status);
  }

  if (!body.success) {
    throw new ApiError(body.message, response.status, body.errors ?? {});
  }

  return { data: body.data, meta: body.meta };
}

export function timezoneOffsetMinutes(): number {
  return -new Date().getTimezoneOffset();
}

export const api = {
  get: <T>(path: string) => request<T>(path),

  post: <T>(path: string, payload?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: JSON.stringify(payload ?? {}),
    }),

  patch: <T>(path: string, payload: unknown) =>
    request<T>(path, { method: "PATCH", body: JSON.stringify(payload) }),

  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
