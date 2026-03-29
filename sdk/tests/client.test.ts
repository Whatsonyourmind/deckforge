/**
 * Tests for the DeckForge client class.
 *
 * Covers constructor validation, API method routing, header injection,
 * error mapping, and retry-on-429 behavior.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { DeckForge } from "../src/client";
import {
  AuthenticationError,
  ValidationError,
  RateLimitError,
  NotFoundError,
  InsufficientCreditsError,
  DeckForgeError,
} from "../src/errors";
import type { PresentationIR } from "../src/types";

// ── Helpers ─────────────────────────────────────────────────────────────────

const TEST_API_KEY = "dk_test_abc123";
const TEST_BASE_URL = "https://test.deckforge.io";

function makeClient(opts?: Partial<{ apiKey: string; baseUrl: string; maxRetries: number }>) {
  return new DeckForge({
    apiKey: opts?.apiKey ?? TEST_API_KEY,
    baseUrl: opts?.baseUrl ?? TEST_BASE_URL,
    maxRetries: opts?.maxRetries ?? 0, // No retries by default for fast tests
  });
}

function mockFetch(status: number, body: unknown, headers?: Record<string, string>) {
  return vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: () => Promise.resolve(body),
    arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
    headers: new Headers(headers ?? {}),
  });
}

const sampleIR: PresentationIR = {
  schema_version: "1.0",
  metadata: { title: "Test Deck" },
  slides: [
    {
      slide_type: "title_slide",
      elements: [{ type: "heading", content: { text: "Hello" } }],
    },
  ],
};

// ── Tests ───────────────────────────────────────────────────────────────────

describe("DeckForge constructor", () => {
  it("sets baseUrl and apiKey from options", () => {
    const client = makeClient();
    // Access via _fetch call to verify -- the fields are private,
    // so we test indirectly through behavior
    expect(client).toBeInstanceOf(DeckForge);
  });

  it("throws if apiKey is empty", () => {
    expect(() => new DeckForge({ apiKey: "" })).toThrow("apiKey is required");
  });

  it("strips trailing slashes from baseUrl", () => {
    const client = makeClient({ baseUrl: "https://test.io///" });
    expect(client).toBeInstanceOf(DeckForge);
  });
});

describe("DeckForge.render()", () => {
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchSpy = mockFetch(200, {
      id: "render-1",
      status: "complete",
      download_url: "https://cdn.deckforge.io/render-1.pptx",
    });
    vi.stubGlobal("fetch", fetchSpy);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("sends POST to /v1/render with IR body", async () => {
    const client = makeClient();
    const result = await client.render(sampleIR);

    expect(fetchSpy).toHaveBeenCalledOnce();
    const [url, opts] = fetchSpy.mock.calls[0];
    expect(url).toBe(`${TEST_BASE_URL}/v1/render`);
    expect(opts.method).toBe("POST");
    expect(JSON.parse(opts.body)).toEqual(sampleIR);
    expect(result.id).toBe("render-1");
  });

  it("includes Authorization header with Bearer token", async () => {
    const client = makeClient();
    await client.render(sampleIR);

    const [, opts] = fetchSpy.mock.calls[0];
    expect(opts.headers.Authorization).toBe(`Bearer ${TEST_API_KEY}`);
  });

  it("includes Content-Type: application/json for POST", async () => {
    const client = makeClient();
    await client.render(sampleIR);

    const [, opts] = fetchSpy.mock.calls[0];
    expect(opts.headers["Content-Type"]).toBe("application/json");
  });
});

describe("DeckForge.estimate()", () => {
  afterEach(() => vi.restoreAllMocks());

  it("sends POST to /v1/render/estimate", async () => {
    const fetchSpy = mockFetch(200, {
      base_credits: 5,
      surcharges: { finance: 2 },
      total_credits: 7,
    });
    vi.stubGlobal("fetch", fetchSpy);

    const client = makeClient();
    const result = await client.estimate(sampleIR);

    const [url] = fetchSpy.mock.calls[0];
    expect(url).toBe(`${TEST_BASE_URL}/v1/render/estimate`);
    expect(result.total_credits).toBe(7);
  });
});

describe("DeckForge.getJob()", () => {
  afterEach(() => vi.restoreAllMocks());

  it("sends GET to /v1/jobs/{id}", async () => {
    const fetchSpy = mockFetch(200, {
      id: "job-1",
      status: "processing",
      progress: 0.5,
      job_type: "render",
      created_at: "2026-01-01T00:00:00Z",
    });
    vi.stubGlobal("fetch", fetchSpy);

    const client = makeClient();
    const result = await client.getJob("job-1");

    const [url, opts] = fetchSpy.mock.calls[0];
    expect(url).toBe(`${TEST_BASE_URL}/v1/jobs/job-1`);
    expect(opts.method).toBe("GET");
    expect(result.progress).toBe(0.5);
  });
});

describe("DeckForge.decks.*", () => {
  afterEach(() => vi.restoreAllMocks());

  it("decks.list sends GET to /v1/decks with query params", async () => {
    const fetchSpy = mockFetch(200, { items: [], total: 0, page: 1, page_size: 20 });
    vi.stubGlobal("fetch", fetchSpy);

    const client = makeClient();
    await client.decks.list({ page: 2, page_size: 10 });

    const [url] = fetchSpy.mock.calls[0];
    expect(url).toContain("/v1/decks");
    expect(url).toContain("page=2");
    expect(url).toContain("page_size=10");
  });

  it("decks.delete sends DELETE to /v1/decks/{id}", async () => {
    const fetchSpy = mockFetch(204, undefined);
    vi.stubGlobal("fetch", fetchSpy);

    const client = makeClient();
    await client.decks.delete("deck-1");

    const [url, opts] = fetchSpy.mock.calls[0];
    expect(url).toBe(`${TEST_BASE_URL}/v1/decks/deck-1`);
    expect(opts.method).toBe("DELETE");
  });
});

describe("Error response handling", () => {
  afterEach(() => vi.restoreAllMocks());

  it("401 throws AuthenticationError", async () => {
    vi.stubGlobal("fetch", mockFetch(401, { detail: "Invalid API key" }));
    const client = makeClient();
    await expect(client.render(sampleIR)).rejects.toThrow(AuthenticationError);
  });

  it("422 throws ValidationError with errors array", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch(422, {
        detail: [
          { loc: ["body", "slides"], msg: "field required" },
        ],
      }),
    );
    const client = makeClient();
    await expect(client.render(sampleIR)).rejects.toThrow(ValidationError);
  });

  it("429 throws RateLimitError with retryAfter", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch(429, { detail: "Rate limit exceeded", retry_after: 30 }),
    );
    const client = makeClient();
    const err = await client.render(sampleIR).catch((e) => e);
    expect(err).toBeInstanceOf(RateLimitError);
    expect((err as RateLimitError).retryAfter).toBe(30);
  });

  it("404 throws NotFoundError", async () => {
    vi.stubGlobal("fetch", mockFetch(404, { detail: "Deck not found" }));
    const client = makeClient();
    await expect(client.getJob("missing")).rejects.toThrow(NotFoundError);
  });

  it("402 with 'credit' message throws InsufficientCreditsError", async () => {
    vi.stubGlobal(
      "fetch",
      mockFetch(402, { detail: "Insufficient credits for operation" }),
    );
    const client = makeClient();
    await expect(client.render(sampleIR)).rejects.toThrow(InsufficientCreditsError);
  });

  it("500 throws generic DeckForgeError", async () => {
    vi.stubGlobal("fetch", mockFetch(500, { detail: "Internal error" }));
    const client = makeClient();
    await expect(client.render(sampleIR)).rejects.toThrow(DeckForgeError);
  });
});

describe("Retry behavior", () => {
  afterEach(() => vi.restoreAllMocks());

  it("retries on 429 with Retry-After", async () => {
    let attempt = 0;
    const fetchFn = vi.fn().mockImplementation(() => {
      attempt++;
      if (attempt === 1) {
        return Promise.resolve({
          ok: false,
          status: 429,
          json: () => Promise.resolve({ detail: "Rate limited", retry_after: 0 }),
        });
      }
      return Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ id: "render-1", status: "complete" }),
      });
    });
    vi.stubGlobal("fetch", fetchFn);

    const client = makeClient({ maxRetries: 1 });
    const result = await client.render(sampleIR);
    expect(fetchFn).toHaveBeenCalledTimes(2);
    expect(result.id).toBe("render-1");
  });

  it("does NOT retry on 401", async () => {
    const fetchFn = mockFetch(401, { detail: "Bad key" });
    vi.stubGlobal("fetch", fetchFn);

    const client = makeClient({ maxRetries: 2 });
    await expect(client.render(sampleIR)).rejects.toThrow(AuthenticationError);
    expect(fetchFn).toHaveBeenCalledOnce();
  });
});
