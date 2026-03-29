/**
 * @deckforge/sdk -- TypeScript SDK for the DeckForge presentation API.
 *
 * @example
 * ```typescript
 * import { DeckForge } from '@deckforge/sdk';
 *
 * const client = new DeckForge({ apiKey: 'dk_...' });
 * const result = await client.render(presentationIR);
 * ```
 */

// Client
export { DeckForge } from "./client";

// Errors
export {
  DeckForgeError,
  AuthenticationError,
  ValidationError,
  RateLimitError,
  InsufficientCreditsError,
  NotFoundError,
} from "./errors";

// Types (re-export everything for SDK consumers)
export type {
  // Enums as string unions
  SlideType,
  ElementType,
  ChartType,
  LayoutHint,
  Transition,
  Purpose,
  Audience,
  Confidentiality,
  Density,
  ChartStyle,
  Emphasis,
  QualityTarget,
  Tone,
  HeadingLevel,
  // Chart data
  ChartDataSeries,
  SankeyLink,
  GanttTask,
  BarChartData,
  StackedBarChartData,
  GroupedBarChartData,
  HorizontalBarChartData,
  LineChartData,
  MultiLineChartData,
  AreaChartData,
  StackedAreaChartData,
  PieChartData,
  DonutChartData,
  ScatterChartData,
  BubbleChartData,
  ComboChartData,
  WaterfallChartData,
  FunnelChartData,
  TreemapChartData,
  RadarChartData,
  TornadoChartData,
  FootballFieldChartData,
  SensitivityTableData,
  HeatmapChartData,
  SankeyChartData,
  GanttChartData,
  SunburstChartData,
  ChartInput,
  // Element content
  HeadingContent,
  SubheadingContent,
  BodyTextContent,
  BulletListContent,
  NumberedListContent,
  CalloutBoxContent,
  PullQuoteContent,
  FootnoteContent,
  LabelContent,
  TableContent,
  KpiCardContent,
  MetricGroupContent,
  ProgressBarContent,
  GaugeContent,
  SparklineContent,
  ImageContent,
  // Elements
  ElementInput,
  // Slides
  SlideInput,
  // Brand kit
  BrandColors,
  BrandFonts,
  LogoConfig,
  FooterConfig,
  BrandKit,
  // Presentation
  PresentationMetadata,
  GenerationOptions,
  PresentationIR,
  // API responses
  RenderResult,
  JobStatus,
  CostEstimate,
  ProgressEvent,
  DeckListItem,
  DeckListResponse,
  DeckDetail,
  GenerateStartResponse,
  // Options
  DeckForgeOptions,
  ListDecksOptions,
  GenerateOptions,
} from "./types";
