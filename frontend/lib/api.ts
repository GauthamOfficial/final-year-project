import axios, { AxiosError, AxiosRequestConfig } from "axios";
import { useAuth } from "@/lib/auth";

/**
 * Axios client with JWT bearer auth and silent refresh on 401.
 * Backend base URL is read from `NEXT_PUBLIC_API_URL`.
 */
export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000",
  timeout: 60_000,
  withCredentials: false,
});

api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const access = useAuth.getState().access;
    if (access) {
      config.headers.Authorization = `Bearer ${access}`;
    }
  }
  return config;
});

let refreshing: Promise<string | null> | null = null;

async function tryRefresh(): Promise<string | null> {
  const refresh = useAuth.getState().refresh;
  if (!refresh) return null;
  try {
    const res = await axios.post(
      `${api.defaults.baseURL}/api/v1/auth/refresh/`,
      { refresh },
      { timeout: 15_000 }
    );
    const access = res.data?.access as string | undefined;
    if (!access) return null;
    useAuth.getState().setAccess(access);
    return access;
  } catch {
    useAuth.getState().clear();
    return null;
  }
}

api.interceptors.response.use(
  (r) => r,
  async (err: AxiosError) => {
    const original = err.config as
      | (AxiosRequestConfig & { _retry?: boolean })
      | undefined;
    if (
      err.response?.status === 401 &&
      original &&
      !original._retry &&
      !original.url?.includes("/auth/")
    ) {
      original._retry = true;
      refreshing ??= tryRefresh().finally(() => (refreshing = null));
      const newAccess = await refreshing;
      if (newAccess) {
        original.headers = original.headers || {};
        (original.headers as Record<string, string>).Authorization =
          `Bearer ${newAccess}`;
        return api(original);
      }
    }
    return Promise.reject(err);
  }
);

export type ApiError = {
  message: string;
  status?: number;
  detail?: unknown;
};

export function toApiError(err: unknown): ApiError {
  if (axios.isAxiosError(err)) {
    const data = err.response?.data as
      | { detail?: string; error?: string }
      | undefined;
    const message =
      (typeof data?.detail === "string" && data.detail) ||
      (typeof data?.error === "string" && data.error) ||
      err.message;
    return {
      message,
      status: err.response?.status,
      detail: err.response?.data,
    };
  }
  return { message: (err as Error)?.message ?? "Unknown error" };
}
