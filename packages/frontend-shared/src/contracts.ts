/** Shared wire-level contracts from docs/03-详细设计/00-通用约定.md. */
export interface ApiSuccess<T> {
  code: "OK";
  message: string;
  data: T;
  trace_id: string;
  timestamp: string;
}

export interface ApiFailure {
  code: string;
  message: string;
  details?: Array<{
    field?: string;
    reason: string;
  }>;
  data: null;
  trace_id?: string;
  timestamp?: string;
}

export type ApiEnvelope<T> = ApiSuccess<T> | ApiFailure;

export interface OffsetPagination {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

export interface CursorPagination {
  next_cursor: string | null;
  has_more: boolean;
}

export type Role =
  | "BUYER"
  | "PRODUCT_OPS"
  | "ORDER_OPS"
  | "WAREHOUSE"
  | "CS"
  | "FINANCE"
  | "ADMIN";

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
}
