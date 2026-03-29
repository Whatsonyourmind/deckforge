"""DeckForge IR enum types — all enumerations used across the IR schema."""

from __future__ import annotations

from enum import Enum


class SlideType(str, Enum):
    """All 32 slide types (23 universal + 9 finance)."""

    # Universal (23)
    TITLE_SLIDE = "title_slide"
    AGENDA = "agenda"
    SECTION_DIVIDER = "section_divider"
    KEY_MESSAGE = "key_message"
    BULLET_POINTS = "bullet_points"
    TWO_COLUMN_TEXT = "two_column_text"
    COMPARISON = "comparison"
    TIMELINE = "timeline"
    PROCESS_FLOW = "process_flow"
    ORG_CHART = "org_chart"
    TEAM_SLIDE = "team_slide"
    QUOTE_SLIDE = "quote_slide"
    IMAGE_WITH_CAPTION = "image_with_caption"
    ICON_GRID = "icon_grid"
    STATS_CALLOUT = "stats_callout"
    TABLE_SLIDE = "table_slide"
    CHART_SLIDE = "chart_slide"
    MATRIX = "matrix"
    FUNNEL = "funnel"
    MAP_SLIDE = "map_slide"
    THANK_YOU = "thank_you"
    APPENDIX = "appendix"
    Q_AND_A = "q_and_a"

    # Finance vertical (9)
    DCF_SUMMARY = "dcf_summary"
    COMP_TABLE = "comp_table"
    WATERFALL_CHART = "waterfall_chart"
    DEAL_OVERVIEW = "deal_overview"
    RETURNS_ANALYSIS = "returns_analysis"
    CAPITAL_STRUCTURE = "capital_structure"
    MARKET_LANDSCAPE = "market_landscape"
    RISK_MATRIX = "risk_matrix"
    INVESTMENT_THESIS = "investment_thesis"


class ElementType(str, Enum):
    """All element types across text, data, visual, and layout categories."""

    # Text
    HEADING = "heading"
    SUBHEADING = "subheading"
    BODY_TEXT = "body_text"
    BULLET_LIST = "bullet_list"
    NUMBERED_LIST = "numbered_list"
    CALLOUT_BOX = "callout_box"
    PULL_QUOTE = "pull_quote"
    FOOTNOTE = "footnote"
    LABEL = "label"

    # Data
    TABLE = "table"
    CHART = "chart"
    KPI_CARD = "kpi_card"
    METRIC_GROUP = "metric_group"
    PROGRESS_BAR = "progress_bar"
    GAUGE = "gauge"
    SPARKLINE = "sparkline"

    # Visual
    IMAGE = "image"
    ICON = "icon"
    SHAPE = "shape"
    DIVIDER = "divider"
    SPACER = "spacer"
    LOGO = "logo"
    BACKGROUND = "background"

    # Layout
    CONTAINER = "container"
    COLUMN = "column"
    ROW = "row"
    GRID_CELL = "grid_cell"


class ChartType(str, Enum):
    """All chart subtypes — native editable + static fallback."""

    BAR = "bar"
    STACKED_BAR = "stacked_bar"
    GROUPED_BAR = "grouped_bar"
    HORIZONTAL_BAR = "horizontal_bar"
    LINE = "line"
    MULTI_LINE = "multi_line"
    AREA = "area"
    STACKED_AREA = "stacked_area"
    PIE = "pie"
    DONUT = "donut"
    SCATTER = "scatter"
    BUBBLE = "bubble"
    COMBO = "combo"
    WATERFALL = "waterfall"
    FUNNEL = "funnel"
    TREEMAP = "treemap"
    RADAR = "radar"
    TORNADO = "tornado"
    FOOTBALL_FIELD = "football_field"
    SENSITIVITY_TABLE = "sensitivity_table"

    # Static fallback
    HEATMAP = "heatmap"
    SANKEY = "sankey"
    GANTT = "gantt"
    SUNBURST = "sunburst"


class LayoutHint(str, Enum):
    FULL = "full"
    SPLIT_LEFT = "split_left"
    SPLIT_RIGHT = "split_right"
    SPLIT_TOP = "split_top"
    TWO_COLUMN = "two_column"
    THREE_COLUMN = "three_column"
    GRID_2X2 = "grid_2x2"
    GRID_3X3 = "grid_3x3"
    CENTERED = "centered"
    TITLE_ONLY = "title_only"
    BLANK = "blank"


class Transition(str, Enum):
    NONE = "none"
    FADE = "fade"
    SLIDE = "slide"
    PUSH = "push"


class Purpose(str, Enum):
    BOARD_MEETING = "board_meeting"
    INVESTOR_UPDATE = "investor_update"
    SALES_PITCH = "sales_pitch"
    TRAINING = "training"
    PROJECT_UPDATE = "project_update"
    STRATEGY = "strategy"
    RESEARCH = "research"
    DEAL_MEMO = "deal_memo"
    IC_PRESENTATION = "ic_presentation"
    QUARTERLY_REVIEW = "quarterly_review"
    ALL_HANDS = "all_hands"
    KEYNOTE = "keynote"


class Audience(str, Enum):
    C_SUITE = "c_suite"
    BOARD = "board"
    INVESTORS = "investors"
    TEAM = "team"
    CLIENTS = "clients"
    PUBLIC = "public"


class Confidentiality(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class Density(str, Enum):
    SPARSE = "sparse"
    BALANCED = "balanced"
    DENSE = "dense"


class ChartStyle(str, Enum):
    MINIMAL = "minimal"
    DETAILED = "detailed"
    ANNOTATED = "annotated"


class Emphasis(str, Enum):
    VISUAL = "visual"
    DATA = "data"
    NARRATIVE = "narrative"


class QualityTarget(str, Enum):
    DRAFT = "draft"
    PRESENTATION_READY = "presentation_ready"
    BOARD_READY = "board_ready"


class Tone(str, Enum):
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    BOLD = "bold"


class HeadingLevel(str, Enum):
    H1 = "h1"
    H2 = "h2"
    H3 = "h3"
