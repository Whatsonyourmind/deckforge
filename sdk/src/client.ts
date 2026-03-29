/**
 * DeckForge -- Main SDK client class.
 *
 * Provides typed methods for all DeckForge API endpoints:
 * - render / renderToBuffer / estimate (IR operations)
 * - decks.* (deck CRUD and mutations)
 * - generate.start / generate.stream (NL generation with SSE streaming)
 */

import { createApiError, DeckForgeError, RateLimitError } from "./errors";
import type {
  CostEstimate,
  DeckDetail,
  DeckForgeOptions,
  DeckListResponse,
  GenerateOptions,
  GenerateStartResponse,
  JobStatus,
  ListDecksOptions,
  PresentationIR,
  ProgressEvent,
  RenderResult,
  SlideInput,
} from "./types";

const DEFAULT_BASE_URL = "https://api.deckforge.io";
const DEFAULT_TIMEOUT = 30_000;
const DEFAULT_MAX_RETRIES = 2;

export class DeckForge {
  private readonly baseUrl: string;
  private readonly apiKey: string;
  private readonly timeout: number;
  private readonly maxRetries: number;

  constructor(opts: DeckForgeOptions) {
    if (!opts.apiKey) {
      throw new Error("DeckForge: apiKey is required");
    }
    this.apiKey = opts.apiKey;
    this.baseUrl = (opts.baseUrl ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.timeout = opts.timeout ?? DEFAULT_TIMEOUT;
    this.maxRetries = opts.maxRetries ?? DEFAULT_MAX_RETRIES;
  }

  // ── Core API methods ────────────────────────────────────────────────────

  /** POST /v1/render -- Render a presentation IR to PPTX. */
  async render(ir: PresentationIR): Promise<RenderResult> {
    return this._fetch<RenderResult>("POST", "/v1/render", ir);
  }

  /** POST /v1/render -- Render IR and return the PPTX file as an ArrayBuffer. */
  async renderToBuffer(ir: PresentationIR): Promise<ArrayBuffer> {
    const result = await this.render(ir);
    if (!result.download_url) {
      throw new DeckForgeError(
        "Render did not return a download URL",
        500,
      );
    }
    const res = await fetch(result.download_url);
    if (!res.ok) {
      throw new DeckForgeError(
        `Download failed: ${res.status}`,
        res.status,
      );
    }
    return res.arrayBuffer();
  }

  /** POST /v1/render/estimate -- Estimate rendering cost in credits. */
  async estimate(ir: PresentationIR): Promise<CostEstimate> {
    return this._fetch<CostEstimate>("POST", "/v1/render/estimate", ir);
  }

  /** GET /v1/jobs/{jobId} -- Poll job status. */
  async getJob(jobId: string): Promise<JobStatus> {
    return this._fetch<JobStatus>("GET", `/v1/jobs/${jobId}`);
  }

  // ── Deck operations ─────────────────────────────────────────────────────

  readonly decks = {
    /** GET /v1/decks -- List saved decks. */
    list: (opts?: ListDecksOptions): Promise<DeckListResponse> => {
      const params = new URLSearchParams();
      if (opts?.page != null) params.set("page", String(opts.page));
      if (opts?.page_size != null) params.set("page_size", String(opts.page_size));
      const qs = params.toString();
      return this._fetch<DeckListResponse>("GET", `/v1/decks${qs ? `?${qs}` : ""}`);
    },

    /** GET /v1/decks/{id} -- Get deck details. */
    get: (id: string): Promise<DeckDetail> => {
      return this._fetch<DeckDetail>("GET", `/v1/decks/${id}`);
    },

    /** GET /v1/decks/{id}/ir -- Get the raw IR for a deck. */
    getIR: (id: string): Promise<PresentationIR> => {
      return this._fetch<PresentationIR>("GET", `/v1/decks/${id}/ir`);
    },

    /** DELETE /v1/decks/{id} -- Delete a deck. */
    delete: (id: string): Promise<void> => {
      return this._fetch<void>("DELETE", `/v1/decks/${id}`);
    },

    /** POST /v1/decks/{id}/slides -- Append slides to a deck. */
    appendSlides: (id: string, slides: SlideInput[]): Promise<DeckDetail> => {
      return this._fetch<DeckDetail>("POST", `/v1/decks/${id}/slides`, { slides });
    },

    /** PUT /v1/decks/{id}/slides/{index} -- Replace a single slide. */
    replaceSlide: (id: string, index: number, slide: SlideInput): Promise<DeckDetail> => {
      return this._fetch<DeckDetail>("PUT", `/v1/decks/${id}/slides/${index}`, slide);
    },

    /** PUT /v1/decks/{id}/slides/reorder -- Reorder slides. */
    reorderSlides: (id: string, order: number[]): Promise<DeckDetail> => {
      return this._fetch<DeckDetail>("PUT", `/v1/decks/${id}/slides/reorder`, { order });
    },

    /** POST /v1/decks/{id}/retheme -- Apply a new theme. */
    retheme: (id: string, theme: string): Promise<DeckDetail> => {
      return this._fetch<DeckDetail>("POST", `/v1/decks/${id}/retheme`, { theme });
    },
  };

  // ── Generation ──────────────────────────────────────────────────────────

  readonly generate = {
    /** POST /v1/generate -- Start NL-to-deck generation. */
    start: (prompt: string, opts?: GenerateOptions): Promise<GenerateStartResponse> => {
      return this._fetch<GenerateStartResponse>("POST", "/v1/generate", {
        prompt,
        ...opts,
      });
    },

    /**
     * POST /v1/generate then GET /v1/generate/{id}/stream -- Stream progress
     * as an async generator of ProgressEvent objects via SSE.
     */
    stream: async function* (
      this: DeckForge,
      prompt: string,
      opts?: GenerateOptions,
    ): AsyncGenerator<ProgressEvent> {
      const job = await this.generate.start(prompt, opts);
      const url = `${this.baseUrl}/v1/generate/${job.job_id}/stream`;

      const res = await fetch(url, {
        headers: {
          Authorization: `Bearer ${this.apiKey}`,
          Accept: "text/event-stream",
        },
        signal: AbortSignal.timeout(this.timeout * 10), // Streaming gets longer timeout
      });

      if (!res.ok || !res.body) {
        const body = await res.json().catch(() => ({}));
        throw createApiError(res.status, body as Record<string, unknown>);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() ?? "";

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const payload = line.slice(6).trim();
              if (!payload || payload === "[DONE]") continue;
              try {
                const event = JSON.parse(payload) as ProgressEvent;
                yield event;
                if (event.stage === "complete" || event.stage === "failed") {
                  return;
                }
              } catch {
                // Skip malformed JSON lines
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    }.bind(this),
  };

  // ── Internal fetch with auth, error handling, retry ─────────────────────

  /** @internal */
  async _fetch<T>(
    method: string,
    path: string,
    body?: unknown,
  ): Promise<T> {
    let lastError: DeckForgeError | null = null;

    for (let attempt = 0; attempt <= this.maxRetries; attempt++) {
      if (attempt > 0 && lastError instanceof RateLimitError) {
        await this._sleep(lastError.retryAfter * 1000);
      } else if (attempt > 0) {
        await this._sleep(1000 * Math.pow(2, attempt - 1));
      }

      const headers: Record<string, string> = {
        Authorization: `Bearer ${this.apiKey}`,
        Accept: "application/json",
      };

      if (body !== undefined) {
        headers["Content-Type"] = "application/json";
      }

      const res = await fetch(`${this.baseUrl}${path}`, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal: AbortSignal.timeout(this.timeout),
      });

      if (res.ok) {
        if (res.status === 204) return undefined as T;
        return (await res.json()) as T;
      }

      const errorBody = await res.json().catch(() => ({}) as Record<string, unknown>);
      lastError = createApiError(res.status, errorBody as Record<string, unknown>);

      // Only retry on 429 or 5xx
      if (res.status !== 429 && res.status < 500) {
        throw lastError;
      }
    }

    throw lastError!;
  }

  /** @internal */
  private _sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}
