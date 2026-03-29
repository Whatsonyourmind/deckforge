/**
 * Element and Chart factory helpers -- typed constructors for building
 * slide elements and chart data without manually constructing discriminated unions.
 *
 * @example
 * ```typescript
 * const heading = Element.heading("Revenue Growth");
 * const chart = Chart.bar({ categories: ["Q1","Q2"], series: [{ name: "Rev", values: [10,15] }] });
 * ```
 */

import type {
  // Elements
  ElementInput,
  HeadingLevel,
  TableContent,
  KpiCardContent,
  ImageContent,
  // Chart data
  ChartInput,
  ChartDataSeries,
  SankeyLink,
  GanttTask,
} from "../types";

// ── Element factory ─────────────────────────────────────────────────────────

export const Element = {
  /** Heading element. */
  heading: (text: string, level?: HeadingLevel): ElementInput => ({
    type: "heading",
    content: { text, level },
  }),

  /** Subheading element. */
  subheading: (text: string): ElementInput => ({
    type: "subheading",
    content: { text },
  }),

  /** Body text element. */
  bodyText: (text: string, opts?: { markdown?: boolean }): ElementInput => ({
    type: "body_text",
    content: { text, markdown: opts?.markdown },
  }),

  /** Bullet list element. */
  bullets: (items: string[], style?: "disc" | "dash" | "arrow"): ElementInput => ({
    type: "bullet_list",
    content: { items, style },
  }),

  /** Numbered list element. */
  numberedList: (items: string[], start?: number): ElementInput => ({
    type: "numbered_list",
    content: { items, start },
  }),

  /** Callout box element. */
  callout: (
    text: string,
    style?: "info" | "warning" | "success" | "error",
  ): ElementInput => ({
    type: "callout_box",
    content: { text, style },
  }),

  /** Pull quote element. */
  pullQuote: (text: string, attribution?: string): ElementInput => ({
    type: "pull_quote",
    content: { text, attribution },
  }),

  /** Footnote element. */
  footnote: (text: string, number?: number): ElementInput => ({
    type: "footnote",
    content: { text, number },
  }),

  /** Label element. */
  label: (text: string): ElementInput => ({
    type: "label",
    content: { text },
  }),

  /** Table element. */
  table: (data: TableContent): ElementInput => ({
    type: "table",
    content: data,
  }),

  /** Chart element wrapping a ChartInput. */
  chart: (chartData: ChartInput): ElementInput => ({
    type: "chart",
    chart_data: chartData,
  }),

  /** KPI card element. */
  kpiCard: (data: KpiCardContent): ElementInput => ({
    type: "kpi_card",
    content: data,
  }),

  /** Metric group element. */
  metricGroup: (metrics: KpiCardContent[]): ElementInput => ({
    type: "metric_group",
    content: { metrics },
  }),

  /** Progress bar element. */
  progressBar: (label: string, value: number, max_value?: number): ElementInput => ({
    type: "progress_bar",
    content: { label, value, max_value },
  }),

  /** Gauge element. */
  gauge: (label: string, value: number, opts?: { min?: number; max?: number }): ElementInput => ({
    type: "gauge",
    content: { label, value, min_value: opts?.min, max_value: opts?.max },
  }),

  /** Sparkline element. */
  sparkline: (values: number[], label?: string): ElementInput => ({
    type: "sparkline",
    content: { values, label },
  }),

  /** Image element. */
  image: (url: string, opts?: Omit<ImageContent, "url">): ElementInput => ({
    type: "image",
    content: { url, ...opts },
  }),

  /** Icon element. */
  icon: (name: string, size?: number): ElementInput => ({
    type: "icon",
    content: { name, size },
  }),

  /** Divider element. */
  divider: (style?: "solid" | "dashed" | "dotted"): ElementInput => ({
    type: "divider",
    content: { style },
  }),

  /** Spacer element. */
  spacer: (height?: number): ElementInput => ({
    type: "spacer",
    content: { height },
  }),
} as const;

// ── Chart factory ───────────────────────────────────────────────────────────

export const Chart = {
  /** Bar chart. */
  bar: (opts: {
    categories: string[];
    series: ChartDataSeries[];
    show_values?: boolean;
    title?: string;
  }): ChartInput => ({ chart_type: "bar", ...opts }),

  /** Stacked bar chart. */
  stackedBar: (opts: {
    categories: string[];
    series: ChartDataSeries[];
    show_values?: boolean;
    title?: string;
  }): ChartInput => ({ chart_type: "stacked_bar", ...opts }),

  /** Grouped bar chart. */
  groupedBar: (opts: {
    categories: string[];
    series: ChartDataSeries[];
    show_values?: boolean;
    title?: string;
  }): ChartInput => ({ chart_type: "grouped_bar", ...opts }),

  /** Horizontal bar chart. */
  horizontalBar: (opts: {
    categories: string[];
    series: ChartDataSeries[];
    show_values?: boolean;
    title?: string;
  }): ChartInput => ({ chart_type: "horizontal_bar", ...opts }),

  /** Line chart. */
  line: (opts: {
    categories: string[];
    series: ChartDataSeries[];
    show_markers?: boolean;
    title?: string;
  }): ChartInput => ({ chart_type: "line", ...opts }),

  /** Multi-line chart. */
  multiLine: (opts: {
    categories: string[];
    series: ChartDataSeries[];
    show_markers?: boolean;
    title?: string;
  }): ChartInput => ({ chart_type: "multi_line", ...opts }),

  /** Area chart. */
  area: (opts: {
    categories: string[];
    series: ChartDataSeries[];
    title?: string;
  }): ChartInput => ({ chart_type: "area", ...opts }),

  /** Stacked area chart. */
  stackedArea: (opts: {
    categories: string[];
    series: ChartDataSeries[];
    title?: string;
  }): ChartInput => ({ chart_type: "stacked_area", ...opts }),

  /** Pie chart. */
  pie: (opts: {
    labels: string[];
    values: number[];
    show_percentages?: boolean;
    title?: string;
  }): ChartInput => ({ chart_type: "pie", ...opts }),

  /** Donut chart. */
  donut: (opts: {
    labels: string[];
    values: number[];
    show_percentages?: boolean;
    inner_radius?: number;
    title?: string;
  }): ChartInput => ({ chart_type: "donut", ...opts }),

  /** Scatter chart. */
  scatter: (opts: {
    series: ChartDataSeries[];
    x_values: number[];
    title?: string;
  }): ChartInput => ({ chart_type: "scatter", ...opts }),

  /** Bubble chart. */
  bubble: (opts: {
    series: ChartDataSeries[];
    x_values: number[];
    sizes: number[];
    title?: string;
  }): ChartInput => ({ chart_type: "bubble", ...opts }),

  /** Combo chart (bar + line). */
  combo: (opts: {
    categories: string[];
    series: ChartDataSeries[];
    line_series?: ChartDataSeries[];
    title?: string;
  }): ChartInput => ({ chart_type: "combo", ...opts }),

  /** Waterfall chart. */
  waterfall: (opts: {
    categories: string[];
    values: number[];
    title?: string;
  }): ChartInput => ({ chart_type: "waterfall", ...opts }),

  /** Funnel chart. */
  funnel: (opts: {
    stages: string[];
    values: number[];
    title?: string;
  }): ChartInput => ({ chart_type: "funnel", ...opts }),

  /** Treemap chart. */
  treemap: (opts: {
    labels: string[];
    values: number[];
    parents?: string[];
    title?: string;
  }): ChartInput => ({ chart_type: "treemap", ...opts }),

  /** Radar chart. */
  radar: (opts: {
    axes: string[];
    series: ChartDataSeries[];
    title?: string;
  }): ChartInput => ({ chart_type: "radar", ...opts }),

  /** Tornado / sensitivity chart. */
  tornado: (opts: {
    categories: string[];
    low_values: number[];
    high_values: number[];
    base_value?: number;
    title?: string;
  }): ChartInput => ({ chart_type: "tornado", ...opts }),

  /** Football field valuation chart. */
  footballField: (opts: {
    categories: string[];
    low_values: number[];
    high_values: number[];
    mid_values?: number[];
    title?: string;
  }): ChartInput => ({ chart_type: "football_field", ...opts }),

  /** Sensitivity table. */
  sensitivityTable: (opts: {
    row_header: string;
    col_header: string;
    row_values: number[];
    col_values: number[];
    data: number[][];
    title?: string;
  }): ChartInput => ({ chart_type: "sensitivity_table", ...opts }),

  /** Heatmap chart. */
  heatmap: (opts: {
    x_labels: string[];
    y_labels: string[];
    data: number[][];
    title?: string;
  }): ChartInput => ({ chart_type: "heatmap", ...opts }),

  /** Sankey flow chart. */
  sankey: (opts: {
    nodes: string[];
    links: SankeyLink[];
    title?: string;
  }): ChartInput => ({ chart_type: "sankey", ...opts }),

  /** Gantt chart. */
  gantt: (opts: {
    tasks: GanttTask[];
    title?: string;
  }): ChartInput => ({ chart_type: "gantt", ...opts }),

  /** Sunburst chart. */
  sunburst: (opts: {
    labels: string[];
    parents: string[];
    values: number[];
    title?: string;
  }): ChartInput => ({ chart_type: "sunburst", ...opts }),
} as const;
