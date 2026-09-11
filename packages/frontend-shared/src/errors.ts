import type { ApiFailure } from "./contracts";

/**
 * A display-safe error surfaced by the shared HTTP module. `traceId` can be
 * included in an error boundary or support ticket without exposing internals.
 */
export class ApiError extends Error {
  readonly code: string;
  readonly details: ApiFailure["details"];
  readonly traceId?: string;

  constructor(failure: ApiFailure) {
    super(failure.message);
    this.name = "ApiError";
    this.code = failure.code;
    this.details = failure.details;
    this.traceId = failure.trace_id;
  }
}
