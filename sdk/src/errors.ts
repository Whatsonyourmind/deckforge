/**
 * Typed error classes for DeckForge API responses.
 *
 * Maps HTTP status codes to specific error types so SDK consumers
 * can catch and handle errors with full type safety.
 */

export class DeckForgeError extends Error {
  /** HTTP status code (if from API response). */
  readonly status: number;
  /** Raw error body from the API. */
  readonly body?: Record<string, unknown>;

  constructor(
    message: string,
    status: number,
    body?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "DeckForgeError";
    this.status = status;
    this.body = body;
  }
}

/** 401 -- Invalid or missing API key. */
export class AuthenticationError extends DeckForgeError {
  constructor(message = "Invalid or missing API key", body?: Record<string, unknown>) {
    super(message, 401, body);
    this.name = "AuthenticationError";
  }
}

/** 422 -- IR validation failed. */
export class ValidationError extends DeckForgeError {
  /** Detailed validation errors from the API. */
  readonly errors: unknown[];

  constructor(
    message = "IR validation failed",
    errors: unknown[] = [],
    body?: Record<string, unknown>,
  ) {
    super(message, 422, body);
    this.name = "ValidationError";
    this.errors = errors;
  }
}

/** 429 -- Rate limit exceeded. */
export class RateLimitError extends DeckForgeError {
  /** Seconds until the rate limit resets. */
  readonly retryAfter: number;

  constructor(
    retryAfter: number,
    message = "Rate limit exceeded",
    body?: Record<string, unknown>,
  ) {
    super(message, 429, body);
    this.name = "RateLimitError";
    this.retryAfter = retryAfter;
  }
}

/** 402/403 -- Insufficient credits for the requested operation. */
export class InsufficientCreditsError extends DeckForgeError {
  constructor(
    message = "Insufficient credits",
    body?: Record<string, unknown>,
  ) {
    super(message, 402, body);
    this.name = "InsufficientCreditsError";
  }
}

/** 404 -- Resource not found. */
export class NotFoundError extends DeckForgeError {
  constructor(message = "Resource not found", body?: Record<string, unknown>) {
    super(message, 404, body);
    this.name = "NotFoundError";
  }
}

/**
 * Map an HTTP status code and response body to a typed error.
 * Used internally by the client _fetch method.
 */
export function createApiError(
  status: number,
  body: Record<string, unknown>,
): DeckForgeError {
  const message =
    typeof body.detail === "string"
      ? body.detail
      : typeof body.message === "string"
        ? body.message
        : `API error ${status}`;

  switch (status) {
    case 401:
      return new AuthenticationError(message, body);
    case 402:
    case 403:
      if (
        message.toLowerCase().includes("credit") ||
        message.toLowerCase().includes("insufficient")
      ) {
        return new InsufficientCreditsError(message, body);
      }
      return new DeckForgeError(message, status, body);
    case 404:
      return new NotFoundError(message, body);
    case 422: {
      const errors = Array.isArray(body.detail) ? body.detail : [];
      return new ValidationError(message, errors, body);
    }
    case 429: {
      const retryAfter =
        typeof body.retry_after === "number" ? body.retry_after : 60;
      return new RateLimitError(retryAfter, message, body);
    }
    default:
      return new DeckForgeError(message, status, body);
  }
}
