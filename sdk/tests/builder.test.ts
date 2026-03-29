/**
 * Tests for the fluent builder API, slide/element factories, and SSE streaming.
 *
 * Covers immutability, validation, type correctness, and SSE parsing.
 */

import { describe, it, expect, vi, afterEach } from "vitest";
import { PresentationBuilder, Presentation } from "../src/builder/presentation";
import { Slide } from "../src/builder/slides";
import { Element, Chart } from "../src/builder/elements";
import { parseSSELine, streamGeneration } from "../src/streaming";
import type { PresentationIR, SlideInput } from "../src/types";

// ── PresentationBuilder ─────────────────────────────────────────────────────

describe("PresentationBuilder", () => {
  it("create() returns a PresentationBuilder instance", () => {
    const builder = PresentationBuilder.create("Test");
    expect(builder).toBeInstanceOf(PresentationBuilder);
  });

  it("build() throws when no slides added", () => {
    expect(() => PresentationBuilder.create("Empty").build()).toThrow(
      "at least one slide is required",
    );
  });

  it("build() returns valid IR with one slide", () => {
    const ir = PresentationBuilder.create("My Deck")
      .addSlide(Slide.title({ title: "Hello" }))
      .build();

    expect(ir.schema_version).toBe("1.0");
    expect(ir.metadata.title).toBe("My Deck");
    expect(ir.slides).toHaveLength(1);
    expect(ir.slides[0].slide_type).toBe("title_slide");
  });

  it("is immutable -- addSlide returns a new instance", () => {
    const builder1 = PresentationBuilder.create("Test");
    const builder2 = builder1.addSlide(Slide.title({ title: "T" }));

    expect(builder1).not.toBe(builder2);
    // builder1 still has no slides
    expect(() => builder1.build()).toThrow("at least one slide is required");
    // builder2 has one slide
    expect(builder2.build().slides).toHaveLength(1);
  });

  it(".theme() sets theme in built IR", () => {
    const ir = PresentationBuilder.create("Test")
      .theme("corporate_dark")
      .addSlide(Slide.title({ title: "T" }))
      .build();

    expect(ir.theme).toBe("corporate_dark");
  });

  it(".metadata() merges metadata fields", () => {
    const ir = PresentationBuilder.create("Test")
      .metadata({ audience: "board", purpose: "quarterly_review" })
      .metadata({ confidentiality: "confidential" })
      .addSlide(Slide.title({ title: "T" }))
      .build();

    expect(ir.metadata.audience).toBe("board");
    expect(ir.metadata.purpose).toBe("quarterly_review");
    expect(ir.metadata.confidentiality).toBe("confidential");
  });

  it(".brandKit() sets brand_kit in built IR", () => {
    const ir = PresentationBuilder.create("Test")
      .brandKit({ colors: { primary: "#003366" } })
      .addSlide(Slide.title({ title: "T" }))
      .build();

    expect(ir.brand_kit?.colors?.primary).toBe("#003366");
  });

  it(".generationOptions() sets generation_options in built IR", () => {
    const ir = PresentationBuilder.create("Test")
      .generationOptions({ target_slide_count: 10, density: "balanced" })
      .addSlide(Slide.title({ title: "T" }))
      .build();

    expect(ir.generation_options?.target_slide_count).toBe(10);
    expect(ir.generation_options?.density).toBe("balanced");
  });

  it(".addSlides() appends multiple slides", () => {
    const ir = PresentationBuilder.create("Test")
      .addSlides([
        Slide.title({ title: "First" }),
        Slide.bullets({ title: "Points", items: ["A", "B"] }),
      ])
      .build();

    expect(ir.slides).toHaveLength(2);
    expect(ir.slides[0].slide_type).toBe("title_slide");
    expect(ir.slides[1].slide_type).toBe("bullet_points");
  });

  it(".render() calls client.render with built IR", async () => {
    const mockClient = { render: vi.fn().mockResolvedValue({ id: "r-1" }) };
    const builder = PresentationBuilder.create("Test")
      .addSlide(Slide.title({ title: "T" }));

    await builder.render(mockClient);

    expect(mockClient.render).toHaveBeenCalledOnce();
    const calledIR = mockClient.render.mock.calls[0][0] as PresentationIR;
    expect(calledIR.metadata.title).toBe("Test");
  });

  it(".estimate() calls client.estimate with built IR", async () => {
    const mockClient = { estimate: vi.fn().mockResolvedValue({ total_credits: 5 }) };
    const builder = PresentationBuilder.create("Test")
      .addSlide(Slide.title({ title: "T" }));

    await builder.estimate(mockClient);

    expect(mockClient.estimate).toHaveBeenCalledOnce();
  });
});

describe("Presentation namespace", () => {
  it("Presentation.create is an alias for PresentationBuilder.create", () => {
    const builder = Presentation.create("Test");
    expect(builder).toBeInstanceOf(PresentationBuilder);
  });
});

// ── Slide factories ─────────────────────────────────────────────────────────

describe("Slide factories", () => {
  it("Slide.title produces title_slide with heading element", () => {
    const slide = Slide.title({ title: "Hello", subtitle: "World" });
    expect(slide.slide_type).toBe("title_slide");
    expect(slide.elements).toHaveLength(2);
    expect(slide.elements[0].type).toBe("heading");
    expect(slide.elements[1].type).toBe("subheading");
  });

  it("Slide.title without subtitle produces single heading", () => {
    const slide = Slide.title({ title: "Solo" });
    expect(slide.elements).toHaveLength(1);
  });

  it("Slide.bullets produces bullet_points with heading + bullet_list", () => {
    const slide = Slide.bullets({ title: "Points", items: ["A", "B", "C"] });
    expect(slide.slide_type).toBe("bullet_points");
    expect(slide.elements).toHaveLength(2);
    expect(slide.elements[0].type).toBe("heading");
    expect(slide.elements[1].type).toBe("bullet_list");
  });

  it("Slide.chart produces chart_slide with heading + chart element", () => {
    const slide = Slide.chart({
      title: "Revenue",
      chart: Chart.bar({
        categories: ["Q1", "Q2"],
        series: [{ name: "Rev", values: [10, 15] }],
      }),
    });
    expect(slide.slide_type).toBe("chart_slide");
    expect(slide.elements).toHaveLength(2);
    expect(slide.elements[0].type).toBe("heading");
    expect(slide.elements[1].type).toBe("chart");
    // Verify nested chart data
    const chartEl = slide.elements[1];
    if (chartEl.type === "chart") {
      expect(chartEl.chart_data.chart_type).toBe("bar");
    }
  });

  it("Slide.quote produces quote_slide with pull_quote element", () => {
    const slide = Slide.quote({ text: "Be bold.", attribution: "CEO" });
    expect(slide.slide_type).toBe("quote_slide");
    expect(slide.elements[0].type).toBe("pull_quote");
  });

  it("Slide.table produces table_slide with correct data", () => {
    const slide = Slide.table({
      title: "Results",
      headers: ["Metric", "Value"],
      rows: [["Revenue", "$1B"], ["EBITDA", "$200M"]],
    });
    expect(slide.slide_type).toBe("table_slide");
    const tableEl = slide.elements[1];
    if (tableEl.type === "table") {
      expect(tableEl.content.headers).toEqual(["Metric", "Value"]);
      expect(tableEl.content.rows).toHaveLength(2);
    }
  });

  it("Slide.stats produces stats_callout with metric_group", () => {
    const slide = Slide.stats({
      title: "KPIs",
      metrics: [
        { label: "Revenue", value: "$1.2B", change: 12 },
        { label: "EBITDA", value: "$200M", change: -5 },
      ],
    });
    expect(slide.slide_type).toBe("stats_callout");
    expect(slide.elements[1].type).toBe("metric_group");
  });

  it("Slide.twoColumn produces two_column_text with column elements", () => {
    const slide = Slide.twoColumn({
      title: "Compare",
      left: [Element.bodyText("Left content")],
      right: [Element.bodyText("Right content")],
    });
    expect(slide.slide_type).toBe("two_column_text");
    expect(slide.layout_hint).toBe("two_column");
    expect(slide.elements).toHaveLength(3); // heading + 2 columns
  });

  it("Slide.comparison produces comparison with labeled columns", () => {
    const slide = Slide.comparison({
      title: "A vs B",
      left_label: "Option A",
      left_items: ["Pro 1"],
      right_label: "Option B",
      right_items: ["Pro 2"],
    });
    expect(slide.slide_type).toBe("comparison");
    expect(slide.elements).toHaveLength(3);
  });

  // Finance slide factories
  it("Slide.compTable produces comp_table with table", () => {
    const slide = Slide.compTable({
      title: "Comps",
      headers: ["Company", "EV/EBITDA", "P/E"],
      companies: [["ACME", "12.5x", "18.2x"]],
      median_row: ["Median", "11.0x", "16.5x"],
    });
    expect(slide.slide_type).toBe("comp_table");
    const tableEl = slide.elements[1];
    if (tableEl.type === "table") {
      expect(tableEl.content.footer_row).toEqual(["Median", "11.0x", "16.5x"]);
    }
  });

  it("Slide.dcfSummary produces dcf_summary with assumption table", () => {
    const slide = Slide.dcfSummary({
      title: "DCF Analysis",
      assumptions: [
        { label: "WACC", value: "9.5%" },
        { label: "Terminal Growth", value: "2.0%" },
      ],
      implied_value: "$45.00",
    });
    expect(slide.slide_type).toBe("dcf_summary");
    expect(slide.elements).toHaveLength(3); // heading + table + callout
  });

  it("Slide.dealOverview produces deal_overview", () => {
    const slide = Slide.dealOverview({
      title: "Transaction Overview",
      details: [
        { label: "Target", value: "ACME Corp" },
        { label: "EV", value: "$500M" },
      ],
    });
    expect(slide.slide_type).toBe("deal_overview");
  });

  it("Slide.investmentThesis produces investment_thesis with thesis points", () => {
    const slide = Slide.investmentThesis({
      title: "Thesis",
      thesis_points: ["Market leader", "Strong moat"],
      risks: ["Regulatory risk"],
    });
    expect(slide.slide_type).toBe("investment_thesis");
    // heading + bullet_list (thesis) + subheading (risks) + bullet_list (risks) = 4
    expect(slide.elements).toHaveLength(4);
  });

  it("Slide.waterfall produces waterfall_chart with chart data", () => {
    const slide = Slide.waterfall({
      title: "Bridge",
      categories: ["Start", "+Revenue", "-Costs", "End"],
      values: [100, 50, -30, 120],
    });
    expect(slide.slide_type).toBe("waterfall_chart");
    const chartEl = slide.elements[1];
    if (chartEl.type === "chart") {
      expect(chartEl.chart_data.chart_type).toBe("waterfall");
    }
  });

  it("Slide.raw passes through a raw SlideInput unchanged", () => {
    const raw: SlideInput = {
      slide_type: "appendix",
      elements: [{ type: "heading", content: { text: "Raw" } }],
    };
    expect(Slide.raw(raw)).toBe(raw);
  });

  it("passes through speaker_notes when provided", () => {
    const slide = Slide.title({ title: "T", speaker_notes: "My notes" });
    expect(slide.speaker_notes).toBe("My notes");
  });
});

// ── Element factories ───────────────────────────────────────────────────────

describe("Element factories", () => {
  it("Element.heading creates heading element", () => {
    const el = Element.heading("Title", "h2");
    expect(el.type).toBe("heading");
    if (el.type === "heading") {
      expect(el.content.text).toBe("Title");
      expect(el.content.level).toBe("h2");
    }
  });

  it("Element.bullets creates bullet_list element", () => {
    const el = Element.bullets(["A", "B"], "dash");
    expect(el.type).toBe("bullet_list");
    if (el.type === "bullet_list") {
      expect(el.content.items).toEqual(["A", "B"]);
      expect(el.content.style).toBe("dash");
    }
  });

  it("Element.table creates table element", () => {
    const el = Element.table({
      headers: ["Col1", "Col2"],
      rows: [["A", "B"]],
    });
    expect(el.type).toBe("table");
  });

  it("Element.image creates image element", () => {
    const el = Element.image("https://example.com/img.png", { alt: "Photo", caption: "A photo" });
    expect(el.type).toBe("image");
    if (el.type === "image") {
      expect(el.content.url).toBe("https://example.com/img.png");
      expect(el.content.caption).toBe("A photo");
    }
  });

  it("Element.chart wraps a ChartInput", () => {
    const el = Element.chart(Chart.pie({ labels: ["A", "B"], values: [60, 40] }));
    expect(el.type).toBe("chart");
    if (el.type === "chart") {
      expect(el.chart_data.chart_type).toBe("pie");
    }
  });

  it("Element.kpiCard creates kpi_card element", () => {
    const el = Element.kpiCard({ label: "Revenue", value: "$1B", change: 12, change_direction: "up" });
    expect(el.type).toBe("kpi_card");
  });
});

// ── Chart factories ─────────────────────────────────────────────────────────

describe("Chart factories", () => {
  it("Chart.bar produces bar chart data", () => {
    const chart = Chart.bar({
      categories: ["Q1", "Q2"],
      series: [{ name: "Rev", values: [10, 15] }],
    });
    expect(chart.chart_type).toBe("bar");
  });

  it("Chart.line produces line chart data", () => {
    const chart = Chart.line({
      categories: ["Jan", "Feb"],
      series: [{ name: "Sales", values: [100, 120] }],
      show_markers: true,
    });
    expect(chart.chart_type).toBe("line");
    if (chart.chart_type === "line") {
      expect(chart.show_markers).toBe(true);
    }
  });

  it("Chart.pie produces pie chart data", () => {
    const chart = Chart.pie({
      labels: ["A", "B", "C"],
      values: [50, 30, 20],
      show_percentages: true,
    });
    expect(chart.chart_type).toBe("pie");
  });

  it("Chart.waterfall produces waterfall chart data", () => {
    const chart = Chart.waterfall({
      categories: ["Start", "Delta", "End"],
      values: [100, 20, 120],
    });
    expect(chart.chart_type).toBe("waterfall");
  });

  it("Chart.combo produces combo chart with line_series", () => {
    const chart = Chart.combo({
      categories: ["Q1", "Q2"],
      series: [{ name: "Rev", values: [10, 15] }],
      line_series: [{ name: "Target", values: [12, 12] }],
    });
    expect(chart.chart_type).toBe("combo");
    if (chart.chart_type === "combo") {
      expect(chart.line_series).toHaveLength(1);
    }
  });

  it("Chart.footballField produces football_field chart data", () => {
    const chart = Chart.footballField({
      categories: ["DCF", "Comps", "LBO"],
      low_values: [30, 35, 28],
      high_values: [50, 48, 42],
      mid_values: [40, 42, 35],
    });
    expect(chart.chart_type).toBe("football_field");
  });

  it("Chart.gantt produces gantt chart data", () => {
    const chart = Chart.gantt({
      tasks: [
        { name: "Phase 1", start: "2025-01-01", end: "2025-03-31", progress: 100 },
        { name: "Phase 2", start: "2025-04-01", end: "2025-06-30", progress: 50 },
      ],
    });
    expect(chart.chart_type).toBe("gantt");
  });
});

// ── SSE Streaming ───────────────────────────────────────────────────────────

describe("parseSSELine", () => {
  it("parses a valid data line", () => {
    const event = parseSSELine(
      'data: {"stage":"generating","progress":0.5,"timestamp":"2026-01-01T00:00:00Z"}',
    );
    expect(event).not.toBeNull();
    expect(event?.stage).toBe("generating");
    expect(event?.progress).toBe(0.5);
  });

  it("returns null for non-data lines", () => {
    expect(parseSSELine("event: progress")).toBeNull();
    expect(parseSSELine(": comment")).toBeNull();
    expect(parseSSELine("id: 42")).toBeNull();
  });

  it("returns null for [DONE] sentinel", () => {
    expect(parseSSELine("data: [DONE]")).toBeNull();
  });

  it("returns null for empty data", () => {
    expect(parseSSELine("data: ")).toBeNull();
  });

  it("returns null for malformed JSON", () => {
    expect(parseSSELine("data: {not json}")).toBeNull();
  });
});

describe("streamGeneration", () => {
  afterEach(() => vi.restoreAllMocks());

  it("yields ProgressEvent objects from SSE stream", async () => {
    // Build a mock ReadableStream that emits SSE data
    const sseData = [
      'data: {"stage":"started","progress":0,"timestamp":"2026-01-01T00:00:00Z"}\n\n',
      'data: {"stage":"generating","progress":0.5,"timestamp":"2026-01-01T00:00:01Z"}\n\n',
      'data: {"stage":"complete","progress":1,"timestamp":"2026-01-01T00:00:02Z"}\n\n',
    ];

    const encoder = new TextEncoder();
    let chunkIndex = 0;

    const mockBody = {
      getReader: () => ({
        read: () => {
          if (chunkIndex < sseData.length) {
            return Promise.resolve({
              done: false,
              value: encoder.encode(sseData[chunkIndex++]),
            });
          }
          return Promise.resolve({ done: true, value: undefined });
        },
        releaseLock: vi.fn(),
      }),
    };

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: mockBody,
    }));

    const events: Array<{ stage: string; progress: number }> = [];
    for await (const event of streamGeneration("https://api.test", "dk_test", "job-1")) {
      events.push({ stage: event.stage, progress: event.progress });
    }

    expect(events).toHaveLength(3);
    expect(events[0]).toEqual({ stage: "started", progress: 0 });
    expect(events[1]).toEqual({ stage: "generating", progress: 0.5 });
    expect(events[2]).toEqual({ stage: "complete", progress: 1 });
  });

  it("stops on failed stage", async () => {
    const sseData = [
      'data: {"stage":"started","progress":0,"timestamp":"2026-01-01T00:00:00Z"}\n\n',
      'data: {"stage":"failed","progress":0,"timestamp":"2026-01-01T00:00:01Z"}\n\n',
      'data: {"stage":"should_not_see","progress":0,"timestamp":"2026-01-01T00:00:02Z"}\n\n',
    ];

    const encoder = new TextEncoder();
    let chunkIndex = 0;

    const mockBody = {
      getReader: () => ({
        read: () => {
          if (chunkIndex < sseData.length) {
            return Promise.resolve({
              done: false,
              value: encoder.encode(sseData[chunkIndex++]),
            });
          }
          return Promise.resolve({ done: true, value: undefined });
        },
        releaseLock: vi.fn(),
      }),
    };

    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: mockBody,
    }));

    const events: string[] = [];
    for await (const event of streamGeneration("https://api.test", "dk_test", "job-1")) {
      events.push(event.stage);
    }

    expect(events).toEqual(["started", "failed"]);
    // "should_not_see" was not yielded
  });

  it("throws on non-OK response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      body: null,
      json: () => Promise.resolve({ detail: "Unauthorized" }),
    }));

    const gen = streamGeneration("https://api.test", "dk_test", "job-1");
    await expect(gen.next()).rejects.toThrow();
  });
});
