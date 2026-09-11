import axios, {
  AxiosError,
  AxiosHeaders,
  type AxiosInstance,
  type AxiosRequestConfig,
  type InternalAxiosRequestConfig,
} from "axios";

import type { ApiEnvelope, ApiFailure } from "./contracts";
import { ApiError } from "./errors";

declare module "axios" {
  interface AxiosRequestConfig {
    /** Do not attach the current access token (used by the refresh request). */
    skipAuth?: boolean;
    /** Do not create an idempotency key for this mutation. */
    skipIdempotency?: boolean;
    /** Internal marker preventing a refresh loop. */
    _retriedAfterRefresh?: boolean;
  }
}

export interface AuthSessionAdapter {
  getAccessToken(): string | null;
  refresh(): Promise<string | null>;
  clear(): void;
  redirectToLogin(): void;
}

export interface CreateApiClientOptions {
  baseURL: string;
  auth: AuthSessionAdapter;
  timeoutMs?: number;
}

export interface ApiClient {
  readonly raw: AxiosInstance;
  request<T>(config: AxiosRequestConfig): Promise<T>;
  get<T>(url: string, config?: AxiosRequestConfig): Promise<T>;
  post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
  put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
  patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>;
  delete<T>(url: string, config?: AxiosRequestConfig): Promise<T>;
}

const mutationMethods = new Set(["post", "put", "patch", "delete"]);

function isApiFailure(value: unknown): value is ApiFailure {
  return (
    typeof value === "object" &&
    value !== null &&
    "code" in value &&
    (value as { code?: unknown }).code !== "OK" &&
    "message" in value
  );
}

function unwrap<T>(value: unknown): T {
  const envelope = value as ApiEnvelope<T>;
  if (envelope && envelope.code === "OK") {
    return envelope.data as T;
  }

  if (isApiFailure(value)) {
    throw new ApiError(value);
  }

  // This makes a malformed response visible during integration instead of
  // silently turning a protocol violation into an arbitrary UI value.
  throw new ApiError({
    code: "COMMON-8001",
    message: "服务响应格式异常，请稍后重试",
    data: null,
  });
}

function newUuid(): string {
  if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/**
 * Creates one deep HTTP module per web application. The application supplies
 * its session adapter; transport retries, request IDs, idempotency keys and
 * the single-flight token refresh queue stay hidden behind this interface.
 */
export function createApiClient(options: CreateApiClientOptions): ApiClient {
  const instance = axios.create({
    baseURL: options.baseURL,
    timeout: options.timeoutMs ?? 10_000,
    headers: { "Content-Type": "application/json" },
  });

  let refreshInFlight: Promise<string | null> | null = null;

  instance.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const headers = AxiosHeaders.from(config.headers);
    const token = options.auth.getAccessToken();

    if (token && !config.skipAuth) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    if (!headers.has("X-Request-Id")) {
      headers.set("X-Request-Id", newUuid());
    }

    const method = config.method?.toLowerCase();
    if (
      method &&
      mutationMethods.has(method) &&
      !config.skipIdempotency &&
      !headers.has("Idempotency-Key")
    ) {
      headers.set("Idempotency-Key", newUuid());
    }

    config.headers = headers;
    return config;
  });

  instance.interceptors.response.use(undefined, async (error: AxiosError) => {
    const config = error.config;
    if (
      error.response?.status !== 401 ||
      !config ||
      config.skipAuth ||
      config._retriedAfterRefresh
    ) {
      return Promise.reject(error);
    }

    refreshInFlight ??= options.auth.refresh().finally(() => {
      refreshInFlight = null;
    });

    const token = await refreshInFlight;
    if (!token) {
      options.auth.clear();
      options.auth.redirectToLogin();
      return Promise.reject(error);
    }

    config._retriedAfterRefresh = true;
    const headers = AxiosHeaders.from(config.headers);
    headers.set("Authorization", `Bearer ${token}`);
    config.headers = headers;
    return instance.request(config);
  });

  const request = async <T>(config: AxiosRequestConfig): Promise<T> => {
    try {
      const response = await instance.request(config);
      return unwrap<T>(response.data);
    } catch (error) {
      if (axios.isAxiosError(error) && isApiFailure(error.response?.data)) {
        throw new ApiError(error.response.data);
      }
      throw error;
    }
  };

  return {
    raw: instance,
    request,
    get: <T>(url: string, config?: AxiosRequestConfig) => request<T>({ ...config, method: "get", url }),
    post: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) => request<T>({ ...config, method: "post", url, data }),
    put: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) => request<T>({ ...config, method: "put", url, data }),
    patch: <T>(url: string, data?: unknown, config?: AxiosRequestConfig) => request<T>({ ...config, method: "patch", url, data }),
    delete: <T>(url: string, config?: AxiosRequestConfig) => request<T>({ ...config, method: "delete", url }),
  };
}
