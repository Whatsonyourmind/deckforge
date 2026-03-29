/**
 * SSE streaming helper for DeckForge generation progress.
 *
 * Uses fetch + ReadableStream (NOT EventSource -- cannot set Authorization header).
 * Parses "data: {...}\n\n" SSE format, handles reconnection with Last-Event-ID,
 * and yields typed ProgressEvent objects via AsyncGenerator.
 */

import { createApiError } from "./errors";
import type { ProgressEvent } from "./types";

/** Options for the streaming helper. */
export interface StreamOptions {
  /** Timeout in ms for the streaming connection (default: 300000 = 5 min). */
  timeout?: number;
  /** AbortSignal for external cancellation. */
  signal?: AbortSignal;
  /** Last event ID for reconnection. */
  lastEventId?: string;
}

/**
 * StreamingHelper -- stateless utility for consuming SSE progress events.
 *
 * @example
 * ```typescript
 * for await (const event of streamGeneration(baseUrl, apiKey, "job-123")) {
 *   console.log(`${event.stage}: ${event.progress * 100}%`);
 *   if (event.stage === "complete") break;
 * }
 * ```
 */
export async function* streamGeneration(
  baseUrl: string,
  apiKey: string,
  jobId: string,
  options?: StreamOptions,
): AsyncGenerator<ProgressEvent> {
  const timeout = options?.timeout ?? 300_000;
  let lastEventId = options?.lastEventId;

  const headers: Record<string, string> = {
    Authorization: `Bearer ${apiKey}`,
    Accept: "text/event-stream",
    "Cache-Control": "no-cache",
  };

  if (lastEventId) {
    headers["Last-Event-ID"] = lastEventId;
  }

  const url = `${baseUrl}/v1/generate/${jobId}/stream`;

  const res = await fetch(url, {
    headers,
    signal: options?.signal ?? AbortSignal.timeout(timeout),
  });

  if (!res.ok || !res.body) {
    const body = await res.json().catch(() => ({}));
    throw createApiError(res.status, body as Record<string, unknown>);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let currentEventId: string | undefined;

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE messages (terminated by double newline)
      const messages = buffer.split("\n\n");
      // Last element is incomplete -- keep in buffer
      buffer = messages.pop() ?? "";

      for (const message of messages) {
        const lines = message.split("\n");
        let data: string | undefined;

        for (const line of lines) {
          if (line.startsWith("id:")) {
            currentEventId = line.slice(3).trim();
            lastEventId = currentEventId;
          } else if (line.startsWith("data:")) {
            data = line.slice(5).trim();
          }
          // Ignore "event:", "retry:", and comment lines (starting with :)
        }

        if (!data || data === "[DONE]") continue;

        try {
          const event = JSON.parse(data) as ProgressEvent;
          yield event;

          if (event.stage === "complete" || event.stage === "failed") {
            return;
          }
        } catch {
          // Skip malformed JSON -- SSE streams can include keep-alive or comments
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

/**
 * Parse a single SSE data line into a ProgressEvent.
 * Exported for testing convenience.
 */
export function parseSSELine(line: string): ProgressEvent | null {
  if (!line.startsWith("data:")) return null;
  const payload = line.slice(5).trim();
  if (!payload || payload === "[DONE]") return null;
  try {
    return JSON.parse(payload) as ProgressEvent;
  } catch {
    return null;
  }
}

/** Convenience alias for module export. */
export const StreamingHelper = {
  streamGeneration,
  parseSSELine,
} as const;
