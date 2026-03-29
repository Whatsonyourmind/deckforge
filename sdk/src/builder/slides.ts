/**
 * Slide factory helpers -- typed constructors for all 32 slide types.
 *
 * Each factory function builds a SlideInput with the correct slide_type
 * discriminator and pre-structured elements, so users never have to
 * manually construct element arrays.
 *
 * @example
 * ```typescript
 * const slide = Slide.title({ title: "Q4 Earnings", subtitle: "FY2025" });
 * const slide2 = Slide.bullets({ title: "Key Points", items: ["Revenue up", "Costs down"] });
 * ```
 */

import type {
  ChartInput,
  ElementInput,
  LayoutHint,
  SlideInput,
  Transition,
} from "../types";

// ── Helper types for factory inputs ─────────────────────────────────────────

interface BaseSlideOpts {
  layout_hint?: LayoutHint;
  transition?: Transition;
  speaker_notes?: string;
}

function base(opts: BaseSlideOpts): Pick<SlideInput, "layout_hint" | "transition" | "speaker_notes"> {
  const out: Pick<SlideInput, "layout_hint" | "transition" | "speaker_notes"> = {};
  if (opts.layout_hint) out.layout_hint = opts.layout_hint;
  if (opts.transition) out.transition = opts.transition;
  if (opts.speaker_notes) out.speaker_notes = opts.speaker_notes;
  return out;
}

// ── The Slide factory object ────────────────────────────────────────────────

export const Slide = {
  // ── Universal slides (23) ───────────────────────────────────────────────

  /** Title slide with heading and optional subtitle. */
  title: (opts: { title: string; subtitle?: string } & BaseSlideOpts): SlideInput => ({
    slide_type: "title_slide",
    elements: [
      { type: "heading", content: { text: opts.title } },
      ...(opts.subtitle
        ? [{ type: "subheading", content: { text: opts.subtitle } } as ElementInput]
        : []),
    ],
    ...base(opts),
  }),

  /** Agenda slide with numbered list of items. */
  agenda: (opts: { title: string; items: string[] } & BaseSlideOpts): SlideInput => ({
    slide_type: "agenda",
    elements: [
      { type: "heading", content: { text: opts.title } },
      { type: "numbered_list", content: { items: opts.items } },
    ],
    ...base(opts),
  }),

  /** Section divider with a single key message. */
  sectionDivider: (opts: { title: string; subtitle?: string } & BaseSlideOpts): SlideInput => ({
    slide_type: "section_divider",
    elements: [
      { type: "heading", content: { text: opts.title, level: "h1" } },
      ...(opts.subtitle
        ? [{ type: "subheading", content: { text: opts.subtitle } } as ElementInput]
        : []),
    ],
    ...base(opts),
  }),

  /** Key message slide with prominent text. */
  keyMessage: (opts: { message: string; supporting?: string } & BaseSlideOpts): SlideInput => ({
    slide_type: "key_message",
    elements: [
      { type: "heading", content: { text: opts.message } },
      ...(opts.supporting
        ? [{ type: "body_text", content: { text: opts.supporting } } as ElementInput]
        : []),
    ],
    ...base(opts),
  }),

  /** Bullet points slide. */
  bullets: (opts: { title: string; items: string[] } & BaseSlideOpts): SlideInput => ({
    slide_type: "bullet_points",
    elements: [
      { type: "heading", content: { text: opts.title } },
      { type: "bullet_list", content: { items: opts.items } },
    ],
    ...base(opts),
  }),

  /** Two-column text layout. */
  twoColumn: (
    opts: {
      title: string;
      left: ElementInput[];
      right: ElementInput[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "two_column_text",
    elements: [
      { type: "heading", content: { text: opts.title } },
      { type: "column", content: { children: opts.left } },
      { type: "column", content: { children: opts.right } },
    ],
    layout_hint: opts.layout_hint ?? "two_column",
    transition: opts.transition,
    speaker_notes: opts.speaker_notes,
  }),

  /** Side-by-side comparison. */
  comparison: (
    opts: {
      title: string;
      left_label: string;
      left_items: string[];
      right_label: string;
      right_items: string[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "comparison",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "column",
        content: {
          children: [
            { type: "subheading", content: { text: opts.left_label } },
            { type: "bullet_list", content: { items: opts.left_items } },
          ],
        },
      },
      {
        type: "column",
        content: {
          children: [
            { type: "subheading", content: { text: opts.right_label } },
            { type: "bullet_list", content: { items: opts.right_items } },
          ],
        },
      },
    ],
    layout_hint: opts.layout_hint ?? "two_column",
    transition: opts.transition,
    speaker_notes: opts.speaker_notes,
  }),

  /** Timeline / milestones. */
  timeline: (
    opts: { title: string; milestones: { date: string; label: string }[] } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "timeline",
    elements: [
      { type: "heading", content: { text: opts.title } },
      ...opts.milestones.map(
        (m): ElementInput => ({
          type: "callout_box",
          content: { text: `${m.date}: ${m.label}`, style: "info" },
        }),
      ),
    ],
    ...base(opts),
  }),

  /** Process flow / step-by-step. */
  processFlow: (
    opts: { title: string; steps: string[] } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "process_flow",
    elements: [
      { type: "heading", content: { text: opts.title } },
      { type: "numbered_list", content: { items: opts.steps } },
    ],
    ...base(opts),
  }),

  /** Org chart. */
  orgChart: (
    opts: {
      title: string;
      members: { name: string; role: string }[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "org_chart",
    elements: [
      { type: "heading", content: { text: opts.title } },
      ...opts.members.map(
        (m): ElementInput => ({
          type: "label",
          content: { text: `${m.name} -- ${m.role}` },
        }),
      ),
    ],
    ...base(opts),
  }),

  /** Team slide with member names and roles. */
  team: (
    opts: {
      title: string;
      members: { name: string; role: string; image_url?: string }[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "team_slide",
    elements: [
      { type: "heading", content: { text: opts.title } },
      ...opts.members.map(
        (m): ElementInput => ({
          type: "label",
          content: { text: `${m.name} -- ${m.role}` },
        }),
      ),
    ],
    ...base(opts),
  }),

  /** Quote slide with attribution. */
  quote: (opts: { text: string; attribution?: string } & BaseSlideOpts): SlideInput => ({
    slide_type: "quote_slide",
    elements: [
      { type: "pull_quote", content: { text: opts.text, attribution: opts.attribution } },
    ],
    ...base(opts),
  }),

  /** Image with optional caption. */
  image: (
    opts: { title: string; url: string; caption?: string; alt?: string } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "image_with_caption",
    elements: [
      { type: "heading", content: { text: opts.title } },
      { type: "image", content: { url: opts.url, alt: opts.alt, caption: opts.caption } },
    ],
    ...base(opts),
  }),

  /** Icon grid -- small icon+label items. */
  iconGrid: (
    opts: {
      title: string;
      icons: { name: string; label: string }[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "icon_grid",
    elements: [
      { type: "heading", content: { text: opts.title } },
      ...opts.icons.map(
        (i): ElementInput => ({
          type: "icon",
          content: { name: i.name },
        }),
      ),
    ],
    layout_hint: opts.layout_hint ?? "grid_3x3",
    transition: opts.transition,
    speaker_notes: opts.speaker_notes,
  }),

  /** Stats callout -- big numbers with labels. */
  stats: (
    opts: {
      title: string;
      metrics: { label: string; value: string | number; change?: number }[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "stats_callout",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "metric_group",
        content: {
          metrics: opts.metrics.map((m) => ({
            label: m.label,
            value: m.value,
            change: m.change,
          })),
        },
      },
    ],
    ...base(opts),
  }),

  /** Table slide with headers and rows. */
  table: (
    opts: {
      title: string;
      headers: string[];
      rows: (string | number | null)[][];
      footer_row?: (string | number | null)[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "table_slide",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "table",
        content: {
          headers: opts.headers,
          rows: opts.rows,
          footer_row: opts.footer_row,
        },
      },
    ],
    ...base(opts),
  }),

  /** Chart slide -- wraps any ChartInput. */
  chart: (
    opts: { title: string; chart: ChartInput } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "chart_slide",
    elements: [
      { type: "heading", content: { text: opts.title } },
      { type: "chart", chart_data: opts.chart },
    ],
    ...base(opts),
  }),

  /** Matrix / 2D grid layout. */
  matrix: (
    opts: {
      title: string;
      x_label: string;
      y_label: string;
      items: { label: string; x: number; y: number }[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "matrix",
    elements: [
      { type: "heading", content: { text: opts.title } },
      { type: "label", content: { text: `X: ${opts.x_label} | Y: ${opts.y_label}` } },
      ...opts.items.map(
        (item): ElementInput => ({
          type: "label",
          content: { text: `${item.label} (${item.x}, ${item.y})` },
        }),
      ),
    ],
    ...base(opts),
  }),

  /** Funnel visualization. */
  funnel: (
    opts: {
      title: string;
      stages: { label: string; value: number }[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "funnel",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "chart",
        chart_data: {
          chart_type: "funnel" as const,
          stages: opts.stages.map((s) => s.label),
          values: opts.stages.map((s) => s.value),
        },
      },
    ],
    ...base(opts),
  }),

  /** Map slide. */
  map: (opts: { title: string; description?: string } & BaseSlideOpts): SlideInput => ({
    slide_type: "map_slide",
    elements: [
      { type: "heading", content: { text: opts.title } },
      ...(opts.description
        ? [{ type: "body_text", content: { text: opts.description } } as ElementInput]
        : []),
    ],
    ...base(opts),
  }),

  /** Thank-you / closing slide. */
  thankYou: (opts: { title?: string; message?: string } & BaseSlideOpts): SlideInput => ({
    slide_type: "thank_you",
    elements: [
      { type: "heading", content: { text: opts.title ?? "Thank You" } },
      ...(opts.message
        ? [{ type: "body_text", content: { text: opts.message } } as ElementInput]
        : []),
    ],
    ...base(opts),
  }),

  /** Appendix slide with supplementary content. */
  appendix: (
    opts: { title: string; content: ElementInput[] } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "appendix",
    elements: [
      { type: "heading", content: { text: opts.title } },
      ...opts.content,
    ],
    ...base(opts),
  }),

  /** Q&A slide. */
  qAndA: (opts: { title?: string; contact?: string } & BaseSlideOpts): SlideInput => ({
    slide_type: "q_and_a",
    elements: [
      { type: "heading", content: { text: opts.title ?? "Questions?" } },
      ...(opts.contact
        ? [{ type: "body_text", content: { text: opts.contact } } as ElementInput]
        : []),
    ],
    ...base(opts),
  }),

  // ── Finance slides (9) ─────────────────────────────────────────────────

  /** DCF summary with key assumptions. */
  dcfSummary: (
    opts: {
      title: string;
      assumptions: { label: string; value: string | number }[];
      implied_value?: string;
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "dcf_summary",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "table",
        content: {
          headers: ["Assumption", "Value"],
          rows: opts.assumptions.map((a) => [a.label, String(a.value)]),
        },
      },
      ...(opts.implied_value
        ? [
            {
              type: "callout_box",
              content: { text: `Implied Value: ${opts.implied_value}`, style: "success" as const },
            } as ElementInput,
          ]
        : []),
    ],
    ...base(opts),
  }),

  /** Comparable companies table. */
  compTable: (
    opts: {
      title: string;
      headers: string[];
      companies: (string | number | null)[][];
      median_row?: (string | number | null)[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "comp_table",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "table",
        content: {
          headers: opts.headers,
          rows: opts.companies,
          footer_row: opts.median_row,
        },
      },
    ],
    ...base(opts),
  }),

  /** Waterfall chart slide. */
  waterfall: (
    opts: {
      title: string;
      categories: string[];
      values: number[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "waterfall_chart",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "chart",
        chart_data: {
          chart_type: "waterfall" as const,
          categories: opts.categories,
          values: opts.values,
        },
      },
    ],
    ...base(opts),
  }),

  /** Deal overview slide. */
  dealOverview: (
    opts: {
      title: string;
      details: { label: string; value: string }[];
      summary?: string;
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "deal_overview",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "table",
        content: {
          headers: ["", ""],
          rows: opts.details.map((d) => [d.label, d.value]),
        },
      },
      ...(opts.summary
        ? [{ type: "body_text", content: { text: opts.summary } } as ElementInput]
        : []),
    ],
    ...base(opts),
  }),

  /** Returns analysis slide. */
  returnsAnalysis: (
    opts: {
      title: string;
      scenarios: { label: string; irr: string; moic: string }[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "returns_analysis",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "table",
        content: {
          headers: ["Scenario", "IRR", "MOIC"],
          rows: opts.scenarios.map((s) => [s.label, s.irr, s.moic]),
        },
      },
    ],
    ...base(opts),
  }),

  /** Capital structure slide. */
  capitalStructure: (
    opts: {
      title: string;
      layers: { label: string; amount: string; rate?: string }[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "capital_structure",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "table",
        content: {
          headers: ["Layer", "Amount", "Rate"],
          rows: opts.layers.map((l) => [l.label, l.amount, l.rate ?? "--"]),
        },
      },
    ],
    ...base(opts),
  }),

  /** Market landscape / TAM-SAM-SOM or competitive overview. */
  marketLandscape: (
    opts: {
      title: string;
      segments: { label: string; value: string; description?: string }[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "market_landscape",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "metric_group",
        content: {
          metrics: opts.segments.map((s) => ({
            label: s.label,
            value: s.value,
          })),
        },
      },
    ],
    ...base(opts),
  }),

  /** Risk matrix slide. */
  riskMatrix: (
    opts: {
      title: string;
      risks: { label: string; impact: number; likelihood: number }[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "risk_matrix",
    elements: [
      { type: "heading", content: { text: opts.title } },
      {
        type: "table",
        content: {
          headers: ["Risk", "Impact", "Likelihood"],
          rows: opts.risks.map((r) => [r.label, r.impact, r.likelihood]),
        },
      },
    ],
    ...base(opts),
  }),

  /** Investment thesis slide. */
  investmentThesis: (
    opts: {
      title: string;
      thesis_points: string[];
      risks?: string[];
    } & BaseSlideOpts,
  ): SlideInput => ({
    slide_type: "investment_thesis",
    elements: [
      { type: "heading", content: { text: opts.title } },
      { type: "bullet_list", content: { items: opts.thesis_points } },
      ...(opts.risks
        ? [
            { type: "subheading", content: { text: "Key Risks" } } as ElementInput,
            { type: "bullet_list", content: { items: opts.risks } } as ElementInput,
          ]
        : []),
    ],
    ...base(opts),
  }),

  // ── Raw / escape hatch ─────────────────────────────────────────────────

  /** Create a raw SlideInput directly. For advanced usage or custom types. */
  raw: (input: SlideInput): SlideInput => input,
} as const;
