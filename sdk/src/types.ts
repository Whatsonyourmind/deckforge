/**
 * @deckforge/sdk - TypeScript types matching the DeckForge Python IR models.
 *
 * These hand-written types mirror the Pydantic models in src/deckforge/ir/.
 * They provide immediate type safety and IDE autocomplete for SDK consumers.
 */

// ── Enums (string unions for TypeScript ergonomics) ─────────────────────────

/** All 32 slide types (23 universal + 9 finance). */
export type SlideType =
  // Universal (23)
  | "title_slide"
  | "agenda"
  | "section_divider"
  | "key_message"
  | "bullet_points"
  | "two_column_text"
  | "comparison"
  | "timeline"
  | "process_flow"
  | "org_chart"
  | "team_slide"
  | "quote_slide"
  | "image_with_caption"
  | "icon_grid"
  | "stats_callout"
  | "table_slide"
  | "chart_slide"
  | "matrix"
  | "funnel"
  | "map_slide"
  | "thank_you"
  | "appendix"
  | "q_and_a"
  // Finance (9)
  | "dcf_summary"
  | "comp_table"
  | "waterfall_chart"
  | "deal_overview"
  | "returns_analysis"
  | "capital_structure"
  | "market_landscape"
  | "risk_matrix"
  | "investment_thesis";

/** All element types across text, data, visual, and layout categories. */
export type ElementType =
  // Text
  | "heading"
  | "subheading"
  | "body_text"
  | "bullet_list"
  | "numbered_list"
  | "callout_box"
  | "pull_quote"
  | "footnote"
  | "label"
  // Data
  | "table"
  | "chart"
  | "kpi_card"
  | "metric_group"
  | "progress_bar"
  | "gauge"
  | "sparkline"
  // Visual
  | "image"
  | "icon"
  | "shape"
  | "divider"
  | "spacer"
  | "logo"
  | "background"
  // Layout
  | "container"
  | "column"
  | "row"
  | "grid_cell";

/** All chart subtypes -- native editable + static fallback. */
export type ChartType =
  | "bar"
  | "stacked_bar"
  | "grouped_bar"
  | "horizontal_bar"
  | "line"
  | "multi_line"
  | "area"
  | "stacked_area"
  | "pie"
  | "donut"
  | "scatter"
  | "bubble"
  | "combo"
  | "waterfall"
  | "funnel"
  | "treemap"
  | "radar"
  | "tornado"
  | "football_field"
  | "sensitivity_table"
  | "heatmap"
  | "sankey"
  | "gantt"
  | "sunburst";

export type LayoutHint =
  | "full"
  | "split_left"
  | "split_right"
  | "split_top"
  | "two_column"
  | "three_column"
  | "grid_2x2"
  | "grid_3x3"
  | "centered"
  | "title_only"
  | "blank";

export type Transition = "none" | "fade" | "slide" | "push";

export type Purpose =
  | "board_meeting"
  | "investor_update"
  | "sales_pitch"
  | "training"
  | "project_update"
  | "strategy"
  | "research"
  | "deal_memo"
  | "ic_presentation"
  | "quarterly_review"
  | "all_hands"
  | "keynote";

export type Audience =
  | "c_suite"
  | "board"
  | "investors"
  | "team"
  | "clients"
  | "public";

export type Confidentiality =
  | "public"
  | "internal"
  | "confidential"
  | "restricted";

export type Density = "sparse" | "balanced" | "dense";
export type ChartStyle = "minimal" | "detailed" | "annotated";
export type Emphasis = "visual" | "data" | "narrative";
export type QualityTarget = "draft" | "presentation_ready" | "board_ready";
export type Tone = "formal" | "professional" | "conversational" | "bold";
export type HeadingLevel = "h1" | "h2" | "h3";

// ── Chart Data Models ───────────────────────────────────────────────────────

export interface ChartDataSeries {
  name: string;
  values: (number | null)[];
}

export interface SankeyLink {
  source: string;
  target: string;
  value: number;
}

export interface GanttTask {
  name: string;
  start: string;
  end: string;
  progress?: number;
  dependencies?: string[];
}

export interface BarChartData {
  chart_type: "bar";
  categories: string[];
  series: ChartDataSeries[];
  show_values?: boolean;
  title?: string;
}

export interface StackedBarChartData {
  chart_type: "stacked_bar";
  categories: string[];
  series: ChartDataSeries[];
  show_values?: boolean;
  title?: string;
}

export interface GroupedBarChartData {
  chart_type: "grouped_bar";
  categories: string[];
  series: ChartDataSeries[];
  show_values?: boolean;
  title?: string;
}

export interface HorizontalBarChartData {
  chart_type: "horizontal_bar";
  categories: string[];
  series: ChartDataSeries[];
  show_values?: boolean;
  title?: string;
}

export interface LineChartData {
  chart_type: "line";
  categories: string[];
  series: ChartDataSeries[];
  show_markers?: boolean;
  title?: string;
}

export interface MultiLineChartData {
  chart_type: "multi_line";
  categories: string[];
  series: ChartDataSeries[];
  show_markers?: boolean;
  title?: string;
}

export interface AreaChartData {
  chart_type: "area";
  categories: string[];
  series: ChartDataSeries[];
  title?: string;
}

export interface StackedAreaChartData {
  chart_type: "stacked_area";
  categories: string[];
  series: ChartDataSeries[];
  title?: string;
}

export interface PieChartData {
  chart_type: "pie";
  labels: string[];
  values: number[];
  show_percentages?: boolean;
  title?: string;
}

export interface DonutChartData {
  chart_type: "donut";
  labels: string[];
  values: number[];
  show_percentages?: boolean;
  inner_radius?: number;
  title?: string;
}

export interface ScatterChartData {
  chart_type: "scatter";
  series: ChartDataSeries[];
  x_values: number[];
  title?: string;
}

export interface BubbleChartData {
  chart_type: "bubble";
  series: ChartDataSeries[];
  x_values: number[];
  sizes: number[];
  title?: string;
}

export interface ComboChartData {
  chart_type: "combo";
  categories: string[];
  series: ChartDataSeries[];
  line_series?: ChartDataSeries[];
  title?: string;
}

export interface WaterfallChartData {
  chart_type: "waterfall";
  categories: string[];
  values: number[];
  title?: string;
}

export interface FunnelChartData {
  chart_type: "funnel";
  stages: string[];
  values: number[];
  title?: string;
}

export interface TreemapChartData {
  chart_type: "treemap";
  labels: string[];
  values: number[];
  parents?: string[];
  title?: string;
}

export interface RadarChartData {
  chart_type: "radar";
  axes: string[];
  series: ChartDataSeries[];
  title?: string;
}

export interface TornadoChartData {
  chart_type: "tornado";
  categories: string[];
  low_values: number[];
  high_values: number[];
  base_value?: number;
  title?: string;
}

export interface FootballFieldChartData {
  chart_type: "football_field";
  categories: string[];
  low_values: number[];
  high_values: number[];
  mid_values?: number[];
  title?: string;
}

export interface SensitivityTableData {
  chart_type: "sensitivity_table";
  row_header: string;
  col_header: string;
  row_values: number[];
  col_values: number[];
  data: number[][];
  title?: string;
}

export interface HeatmapChartData {
  chart_type: "heatmap";
  x_labels: string[];
  y_labels: string[];
  data: number[][];
  title?: string;
}

export interface SankeyChartData {
  chart_type: "sankey";
  nodes: string[];
  links: SankeyLink[];
  title?: string;
}

export interface GanttChartData {
  chart_type: "gantt";
  tasks: GanttTask[];
  title?: string;
}

export interface SunburstChartData {
  chart_type: "sunburst";
  labels: string[];
  parents: string[];
  values: number[];
  title?: string;
}

/** Discriminated union of all chart data types on chart_type. */
export type ChartInput =
  | BarChartData
  | StackedBarChartData
  | GroupedBarChartData
  | HorizontalBarChartData
  | LineChartData
  | MultiLineChartData
  | AreaChartData
  | StackedAreaChartData
  | PieChartData
  | DonutChartData
  | ScatterChartData
  | BubbleChartData
  | ComboChartData
  | WaterfallChartData
  | FunnelChartData
  | TreemapChartData
  | RadarChartData
  | TornadoChartData
  | FootballFieldChartData
  | SensitivityTableData
  | HeatmapChartData
  | SankeyChartData
  | GanttChartData
  | SunburstChartData;

// ── Element Content Models ──────────────────────────────────────────────────

export interface HeadingContent {
  text: string;
  level?: HeadingLevel;
}

export interface SubheadingContent {
  text: string;
}

export interface BodyTextContent {
  text: string;
  markdown?: boolean;
}

export interface BulletListContent {
  items: string[];
  style?: "disc" | "dash" | "arrow";
}

export interface NumberedListContent {
  items: string[];
  start?: number;
}

export interface CalloutBoxContent {
  text: string;
  style?: "info" | "warning" | "success" | "error";
}

export interface PullQuoteContent {
  text: string;
  attribution?: string;
}

export interface FootnoteContent {
  text: string;
  number?: number;
}

export interface LabelContent {
  text: string;
}

export interface TableContent {
  headers: string[];
  rows: (string | number | null)[][];
  footer_row?: (string | number | null)[];
  highlight_rows?: number[];
  sortable?: boolean;
}

export interface KpiCardContent {
  label: string;
  value: string | number;
  change?: number;
  change_direction?: "up" | "down" | "flat";
}

export interface MetricGroupContent {
  metrics: KpiCardContent[];
}

export interface ProgressBarContent {
  label: string;
  value: number;
  max_value?: number;
}

export interface GaugeContent {
  label: string;
  value: number;
  min_value?: number;
  max_value?: number;
}

export interface SparklineContent {
  values: number[];
  label?: string;
}

export interface ImageContent {
  url: string;
  alt?: string;
  caption?: string;
}

// ── Element Input (discriminated on type) ───────────────────────────────────

interface BaseElementFields {
  layout_hint?: LayoutHint;
  style_overrides?: Record<string, unknown>;
}

export interface HeadingElement extends BaseElementFields {
  type: "heading";
  content: HeadingContent;
}

export interface SubheadingElement extends BaseElementFields {
  type: "subheading";
  content: SubheadingContent;
}

export interface BodyTextElement extends BaseElementFields {
  type: "body_text";
  content: BodyTextContent;
}

export interface BulletListElement extends BaseElementFields {
  type: "bullet_list";
  content: BulletListContent;
}

export interface NumberedListElement extends BaseElementFields {
  type: "numbered_list";
  content: NumberedListContent;
}

export interface CalloutBoxElement extends BaseElementFields {
  type: "callout_box";
  content: CalloutBoxContent;
}

export interface PullQuoteElement extends BaseElementFields {
  type: "pull_quote";
  content: PullQuoteContent;
}

export interface FootnoteElement extends BaseElementFields {
  type: "footnote";
  content: FootnoteContent;
}

export interface LabelElement extends BaseElementFields {
  type: "label";
  content: LabelContent;
}

export interface TableElement extends BaseElementFields {
  type: "table";
  content: TableContent;
}

export interface ChartElement extends BaseElementFields {
  type: "chart";
  chart_data: ChartInput;
}

export interface KpiCardElement extends BaseElementFields {
  type: "kpi_card";
  content: KpiCardContent;
}

export interface MetricGroupElement extends BaseElementFields {
  type: "metric_group";
  content: MetricGroupContent;
}

export interface ProgressBarElement extends BaseElementFields {
  type: "progress_bar";
  content: ProgressBarContent;
}

export interface GaugeElement extends BaseElementFields {
  type: "gauge";
  content: GaugeContent;
}

export interface SparklineElement extends BaseElementFields {
  type: "sparkline";
  content: SparklineContent;
}

export interface ImageElement extends BaseElementFields {
  type: "image";
  content: ImageContent;
}

export interface IconElement extends BaseElementFields {
  type: "icon";
  content: { name: string; size?: number };
}

export interface ShapeElement extends BaseElementFields {
  type: "shape";
  content: { shape: string; fill?: string; width?: number; height?: number };
}

export interface DividerElement extends BaseElementFields {
  type: "divider";
  content?: { style?: "solid" | "dashed" | "dotted" };
}

export interface SpacerElement extends BaseElementFields {
  type: "spacer";
  content?: { height?: number };
}

export interface LogoElement extends BaseElementFields {
  type: "logo";
  content: { url: string; max_width?: number; max_height?: number };
}

export interface BackgroundElement extends BaseElementFields {
  type: "background";
  content: { color?: string; image_url?: string; opacity?: number };
}

export interface ContainerElement extends BaseElementFields {
  type: "container";
  content: { children: ElementInput[] };
}

export interface ColumnElement extends BaseElementFields {
  type: "column";
  content: { children: ElementInput[] };
}

export interface RowElement extends BaseElementFields {
  type: "row";
  content: { children: ElementInput[] };
}

export interface GridCellElement extends BaseElementFields {
  type: "grid_cell";
  content: { children: ElementInput[]; row?: number; col?: number };
}

/** Discriminated union of all element types on the type field. */
export type ElementInput =
  | HeadingElement
  | SubheadingElement
  | BodyTextElement
  | BulletListElement
  | NumberedListElement
  | CalloutBoxElement
  | PullQuoteElement
  | FootnoteElement
  | LabelElement
  | TableElement
  | ChartElement
  | KpiCardElement
  | MetricGroupElement
  | ProgressBarElement
  | GaugeElement
  | SparklineElement
  | ImageElement
  | IconElement
  | ShapeElement
  | DividerElement
  | SpacerElement
  | LogoElement
  | BackgroundElement
  | ContainerElement
  | ColumnElement
  | RowElement
  | GridCellElement;

// ── Slide Input ─────────────────────────────────────────────────────────────

export interface SlideInput {
  slide_type: SlideType;
  elements: ElementInput[];
  layout_hint?: LayoutHint;
  transition?: Transition;
  speaker_notes?: string;
  build_animations?: number[];
}

// ── Brand Kit ───────────────────────────────────────────────────────────────

export interface BrandColors {
  primary: string;
  secondary?: string;
  accent?: string[];
  background?: string;
  text?: string;
  muted?: string;
}

export interface BrandFonts {
  heading?: string;
  body?: string;
  mono?: string;
  caption?: string;
}

export interface LogoConfig {
  url: string;
  placement?:
    | "top_left"
    | "top_right"
    | "bottom_left"
    | "bottom_right"
    | "center";
  max_width?: number;
  max_height?: number;
}

export interface FooterConfig {
  text?: string;
  include_page_numbers?: boolean;
  include_date?: boolean;
  include_logo?: boolean;
}

export interface BrandKit {
  colors?: BrandColors;
  fonts?: BrandFonts;
  logo?: LogoConfig;
  footer?: FooterConfig;
  tone?: Tone;
}

// ── Presentation Metadata ───────────────────────────────────────────────────

export interface PresentationMetadata {
  title: string;
  subtitle?: string;
  author?: string;
  company?: string;
  date?: string;
  language?: string;
  purpose?: Purpose;
  audience?: Audience;
  confidentiality?: Confidentiality;
}

// ── Generation Options ──────────────────────────────────────────────────────

export interface GenerationOptions {
  target_slide_count?: number | number[];
  density?: Density;
  chart_style?: ChartStyle;
  emphasis?: Emphasis;
  quality_target?: QualityTarget;
}

// ── Top-level Presentation IR ───────────────────────────────────────────────

export interface PresentationIR {
  schema_version: "1.0";
  metadata: PresentationMetadata;
  brand_kit?: BrandKit;
  theme?: string;
  slides: SlideInput[];
  generation_options?: GenerationOptions;
}

// ── API Response Types ──────────────────────────────────────────────────────

export interface RenderResult {
  id: string;
  status: string;
  job_id?: string;
  ir?: Record<string, unknown>;
  download_url?: string;
  quality_score?: number;
}

export interface JobStatus {
  id: string;
  status: string;
  progress: number;
  job_type: string;
  created_at: string;
  result?: Record<string, unknown>;
}

export interface CostEstimate {
  base_credits: number;
  surcharges: Record<string, number>;
  total_credits: number;
}

export interface ProgressEvent {
  stage: string;
  progress: number;
  timestamp: string;
  detail?: Record<string, unknown>;
}

export interface DeckListItem {
  id: string;
  title: string;
  slide_count: number;
  created_at: string;
  updated_at: string;
}

export interface DeckListResponse {
  items: DeckListItem[];
  total: number;
  page: number;
  page_size: number;
}

export interface DeckDetail {
  id: string;
  title: string;
  slide_count: number;
  created_at: string;
  updated_at: string;
  ir: PresentationIR;
  quality_score?: number;
}

export interface GenerateStartResponse {
  job_id: string;
  status: string;
  message?: string;
}

// ── Client Options ──────────────────────────────────────────────────────────

export interface DeckForgeOptions {
  apiKey: string;
  baseUrl?: string;
  timeout?: number;
  maxRetries?: number;
}

export interface ListDecksOptions {
  page?: number;
  page_size?: number;
}

export interface GenerateOptions {
  model?: string;
  target_slide_count?: number;
  density?: Density;
  quality_target?: QualityTarget;
}
