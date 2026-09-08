"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "@/lib/client";
import type { PaginationMeta } from "@/types/api";


interface ApiState<T> {
  data: T | null;
  meta?: PaginationMeta;
  loading: boolean;
  error: string | null;
}

export function useApi<T>(path: string | null) {
  const [state, setState] = useState<ApiState<T>>({
    data: null,
    loading: true,
    error: null,
  });

  const load = useCallback(async () => {
    if (path === null) return;

    setState((previous) => ({ ...previous, loading: true, error: null }));

    try {
      const result = await api.get<T>(path);
      setState({
        data: result.data,
        meta: result.meta,
        loading: false,
        error: null,
      });
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        window.location.href = "/login";
        return;
      }

      setState({
        data: null,
        loading: false,
        error:
          error instanceof ApiError
            ? error.message
            : "Something went wrong. Please try again.",
      });
    }
  }, [path]);

  useEffect(() => {
    void load();
  }, [load]);

  return { ...state, refetch: load };
}
