# Phase 5 Research: Chart Engine + Finance Vertical

**Researched:** 2026-03-26
**Phase:** 05-chart-engine-finance-vertical
**Requirements:** CHART-01..05, FIN-01..11

---

## 1. Plotly/Kaleido for Static Chart Image Generation

### Architecture

DeckForge already has a `PlaceholderChartRenderer` for 10 chart types deferred to Phase 5. The strategy is to replace these with Plotly-based renderers that generate high-DPI PNG images and embed them into PPTX slides via `slide.shapes.add_picture()`.

### Static Export Pipeline

```python
import plotly.graph_objects as go
import io

fig = go.Figure(...)
img_bytes = fig.to_image(format="png", width=1200, height=675, scale=2)
# scale=2 gives 2400x1350 effective pixels -- crisp at presentation scale

from pptx.util import Inches
slide.shapes.add_picture(
    io.BytesIO(img_bytes),
    Inches(position.x), Inches(position.y),
    Inches(position.width), Inches(position.height),
)
```

### Kaleido v1 Requirements

- Kaleido >=1.0.0 requires Chrome/Chromium installed on the system (not bundled)
- Docker image already includes Chromium via `apt-get install chromium` (per STACK.md)
- Set `CHROME_PATH=/usr/bin/chromium` environment variable
- Adds ~400MB to Docker image (one-time cost, already accounted for)

### Chart Types and Plotly Implementations

| Chart Type | Plotly Class | Key Parameters |
|---|---|---|
| **waterfall** | `go.Waterfall()` | `x`, `y`, `measure` (relative/absolute/total), `connector`, `increasing`/`decreasing` color |
| **heatmap** | `go.Heatmap()` | `z` (2D array), `x`, `y`, `colorscale`, `text`, `texttemplate` |
| **sankey** | `go.Sankey()` | `node.label`, `node.color`, `link.source`, `link.target`, `link.value` |
| **gantt** | `px.timeline()` | `x_start`, `x_end`, `y`, `color` (requires DataFrame) |
| **football_field** | Custom `go.Bar()` horizontal | Stacked horizontal bars with invisible base + range bars |
| **sensitivity_table** | `go.Heatmap()` + annotations | 2D heatmap with text overlay for each cell value |
| **funnel** | `go.Funnel()` | `x` (values), `y` (stages), `marker.color` |
| **treemap** | `go.Treemap()` | `labels`, `parents`, `values`, `marker.colors` |
| **tornado** | `go.Bar()` horizontal | Two opposing horizontal bar series from a center baseline |
| **sunburst** | `go.Sunburst()` | `labels`, `parents`, `values` |

### Theme Integration

All Plotly charts must use DeckForge theme colors:

```python
def plotly_theme_layout(theme: ResolvedTheme) -> dict:
    return {
        "paper_bgcolor": "rgba(0,0,0,0)",  # Transparent -- slide bg handles this
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": theme.typography.body_family,
            "size": theme.typography.scale.get("caption", 14),
            "color": theme.colors.text_primary,
        },
        "margin": {"l": 40, "r": 20, "t": 40, "b": 40},
    }
```

Series colors use `theme.chart_colors` cycling. Positive/negative colors use `theme.colors.positive` / `theme.colors.negative`.

---

## 2. python-pptx Chart Limitations and Workarounds

### Native Chart Types (already implemented in Phase 3)

python-pptx natively supports 14 chart types via `XL_CHART_TYPE`:
- bar, stacked_bar, grouped_bar, horizontal_bar
- line, multi_line
- area, stacked_area
- pie, donut
- scatter, bubble
- combo (via XML injection)
- radar

### Types Requiring Static Image Fallback

| Chart Type | Why No Native Support | Approach |
|---|---|---|
| waterfall | PowerPoint's native waterfall (Office 2016+) not in python-pptx | Plotly `go.Waterfall()` -> PNG |
| heatmap | No native heatmap in PowerPoint | Plotly `go.Heatmap()` -> PNG |
| sankey | No native sankey in PowerPoint | Plotly `go.Sankey()` -> PNG |
| gantt | No native gantt in PowerPoint | Plotly `px.timeline()` -> PNG |
| football_field | Custom financial visualization | Plotly horizontal bars -> PNG |
| sensitivity_table | Custom annotated heatmap | Plotly heatmap + text annotations -> PNG |
| funnel | PowerPoint funnel exists but not in python-pptx | Plotly `go.Funnel()` -> PNG |
| treemap | PowerPoint treemap exists but not in python-pptx | Plotly `go.Treemap()` -> PNG |
| tornado | No native tornado/butterfly chart | Plotly horizontal bars -> PNG |
| sunburst | PowerPoint sunburst exists but not in python-pptx | Plotly `go.Sunburst()` -> PNG |

### Waterfall Stacked-Bar Workaround (NOT recommended)

The classic approach is invisible stacked bar series to simulate waterfalls. This is brittle:
- Invisible base series with `no_fill` for gap spacing
- Positive/negative series with different colors
- Running total calculated manually
- Label positioning is fragile with many values

**Decision: Use Plotly static image instead.** Waterfall is complex enough that editability in PowerPoint is not expected by finance professionals. The visual quality from Plotly is higher than a stacked-bar workaround.

---

## 3. Financial Slide Layouts

### comp_table (FIN-01)

A comp table is a python-pptx `Table` element (NOT a chart). Structured as:

| Company | EV/EBITDA | P/E | EV/Revenue | Market Cap |
|---|---|---|---|---|
| Company A | 12.5x | 18.2x | 3.1x | $4.2B |
| Company B | 10.8x | 15.6x | 2.7x | $3.1B |
| **Median** | **11.7x** | **16.9x** | **2.9x** | **$3.7B** |

Key features:
- Header row with primary theme color
- Alternating row colors (surface / background)
- Median/mean row bolded and highlighted (accent color)
- Numeric columns right-aligned
- Financial number formatting (multiples with "x", currency with "$" and "B/M/K")
- Optional conditional formatting (green/red for above/below median)
- Column widths proportional to data content

### dcf_summary (FIN-02)

Two-part layout:
1. **Assumptions table** (left/top): WACC, terminal growth, projection period, terminal value method
2. **Sensitivity matrix** (right/bottom): 2-variable grid (e.g., WACC vs terminal growth) with implied equity values

The sensitivity matrix is a table with conditional color formatting (heatmap-like) -- darker shading for higher values. Implemented as a python-pptx Table with cell-level background colors.

### waterfall_chart (FIN-03)

Uses Plotly `go.Waterfall()` with:
- `measure`: "relative" for line items, "total" for subtotals
- `increasing.marker.color`: theme.colors.positive (green)
- `decreasing.marker.color`: theme.colors.negative (red)
- `totals.marker.color`: theme.colors.primary
- Running total line optional (connector lines)
- Value labels on each bar

### deal_overview (FIN-04)

One-pager layout with multiple sections:
- Deal summary header (target, acquirer, date, value)
- Key metrics grid (EV, equity value, premium, revenue, EBITDA)
- Traffic light indicators (green/yellow/red circles for status items)
- Unit economics section (tables with financial formatting)

Implemented as a complex multi-element slide: text boxes, tables, shape indicators.

### returns_analysis (FIN-05)

- IRR/MOIC/CoC returns matrix (table with scenario rows: base/upside/downside)
- Sensitivity grid for entry/exit multiples vs. hold period
- Color-coded cells (green above threshold, red below)

### capital_structure (FIN-06)

Two components:
1. **Sources & Uses table**: Side-by-side tables showing funding sources and acquisition uses
2. **Debt stack**: Horizontal stacked bar showing debt tranches (senior, mezzanine, equity)

### market_landscape (FIN-07)

- TAM/SAM/SOM concentric circles or nested boxes (shapes with text)
- Competitive positioning scatter plot or quadrant chart
- Market share table

### investment_thesis (FIN-08)

- Numbered thesis points (1-5 typically) with bold headers and supporting text
- Risk/reward framework table (risks column vs. mitigants column)
- Simple bulleted layout with strong visual hierarchy

### risk_matrix (FIN-09)

5x5 or 4x4 grid heatmap with likelihood (x-axis) and impact (y-axis):
- Cells colored: green (low risk), yellow (medium), red (high)
- Risk items plotted as labeled circles or text on the grid
- Implemented as either Plotly heatmap or python-pptx table with colored cells

---

## 4. Financial Number Formatting

### Format Specifications

| Format | Input | Output | Pattern |
|---|---|---|---|
| Currency (USD) | 1234567.89 | $1.2M | `$` prefix, magnitude suffix (K/M/B/T) |
| Currency (full) | 1234567.89 | $1,234,567.89 | `$` prefix, comma separators |
| Percentage | 0.1523 | 15.2% | Multiply by 100, 1 decimal, `%` suffix |
| Basis points | 0.0025 | 25bps | Multiply by 10000, integer, `bps` suffix |
| Multiple | 12.456 | 12.5x | 1 decimal, `x` suffix |
| Multiple (turn) | 3.0 | 3.0x | Always 1 decimal, `x` suffix |
| Ratio | 0.75 | 0.75 | 2 decimals, no suffix |
| Year | 2024 | 2024 | Integer, no formatting |

### Implementation: FinancialFormatter class

```python
class FinancialFormatter:
    """Formats numbers for financial presentations."""

    @staticmethod
    def currency(value: float, symbol: str = "$", precision: int = 1, compact: bool = True) -> str:
        if compact:
            return _compact_currency(value, symbol, precision)
        return f"{symbol}{value:,.{precision}f}"

    @staticmethod
    def percentage(value: float, precision: int = 1, is_decimal: bool = True) -> str:
        pct = value * 100 if is_decimal else value
        return f"{pct:.{precision}f}%"

    @staticmethod
    def multiple(value: float, precision: int = 1) -> str:
        return f"{value:.{precision}f}x"

    @staticmethod
    def basis_points(value: float, is_decimal: bool = True) -> str:
        bps = value * 10000 if is_decimal else value
        return f"{int(round(bps))}bps"
```

Magnitude suffix logic for compact currency:
- abs(value) >= 1e12: `T` (trillion)
- abs(value) >= 1e9: `B` (billion)
- abs(value) >= 1e6: `M` (million)
- abs(value) >= 1e3: `K` (thousand)
- else: raw number with commas

Negative values: parentheses `($1.2M)` or minus sign `-$1.2M` (configurable).

---

## 5. CSV/Excel Data Ingestion

### Dependencies

- `pandas>=2.2`: CSV/Excel reading, column type inference, data manipulation
- `openpyxl>=3.1`: Excel .xlsx reading (pandas dependency for Excel files)

Both need to be added to pyproject.toml.

### Auto-Detection Strategy

```python
import pandas as pd

def ingest_tabular_data(file_path_or_bytes, file_type: str = "auto") -> pd.DataFrame:
    """Read CSV or Excel and return cleaned DataFrame."""
    if file_type == "csv" or file_path.endswith(".csv"):
        df = pd.read_csv(file_path_or_bytes)
    else:
        df = pd.read_excel(file_path_or_bytes, engine="openpyxl")
    return df
```

### Column Type Inference

For auto-mapping to finance slide types:

1. **Detect column types**: numeric, percentage, currency, text, date
2. **Heuristics**:
   - Column header contains "EV/EBITDA", "P/E", "multiple" -> multiple format
   - Column header contains "$", "revenue", "market cap", "value" -> currency format
   - Values contain "%" or are 0-1 range -> percentage format
   - Column header contains "company", "name", "ticker" -> text (row label)
   - First column is text, rest numeric -> comp table candidate
   - Two text headers + 2D numeric grid -> sensitivity matrix candidate

3. **Auto-mapping output**: Returns a `DataMapping` object describing:
   - Detected slide type (comp_table, sensitivity_table, etc.)
   - Column roles (label, metric, highlight)
   - Suggested formatting per column

### Supported File Types

| Type | Extension | Library |
|---|---|---|
| CSV | .csv | pandas (built-in) |
| TSV | .tsv | pandas with `sep="\t"` |
| Excel | .xlsx | pandas + openpyxl |
| Excel (legacy) | .xls | pandas + xlrd (not supported, .xlsx only) |

---

## 6. Conditional Formatting for Finance

### Color Rules

| Condition | Color | Use Case |
|---|---|---|
| Positive value | theme.colors.positive (green) | Revenue growth, positive delta |
| Negative value | theme.colors.negative (red) | Losses, negative delta |
| Above median | Light green background | Comp table above-median metrics |
| Below median | Light red background | Comp table below-median metrics |
| Traffic light: green | #27AE60 circle | Status indicator: on track |
| Traffic light: yellow | #F39C12 circle | Status indicator: at risk |
| Traffic light: red | #E74C3C circle | Status indicator: off track |
| Heatmap gradient | theme.colors.positive -> warning -> negative | Risk matrix, sensitivity matrix |

### Implementation: ConditionalFormatter

```python
class ConditionalFormatter:
    """Applies conditional formatting rules to table cells."""

    @staticmethod
    def pos_neg_color(value: float, theme: ResolvedTheme) -> str:
        """Return color hex based on positive/negative value."""
        if value > 0:
            return theme.colors.positive
        elif value < 0:
            return theme.colors.negative
        return theme.colors.text_muted

    @staticmethod
    def median_highlight(value: float, median: float, theme: ResolvedTheme) -> str:
        """Return background color for above/below median."""
        if value > median:
            return _lighten(theme.colors.positive, 0.85)  # light green bg
        elif value < median:
            return _lighten(theme.colors.negative, 0.85)  # light red bg
        return theme.colors.surface

    @staticmethod
    def heatmap_gradient(value: float, min_val: float, max_val: float, theme: ResolvedTheme) -> str:
        """Return color on gradient from negative (low) to positive (high)."""
        ratio = (value - min_val) / (max_val - min_val) if max_val != min_val else 0.5
        return _interpolate_color(theme.colors.negative, theme.colors.positive, ratio)
```

### Cell-Level Application in python-pptx

```python
cell.fill.solid()
cell.fill.fore_color.rgb = RGBColor.from_string(color.lstrip("#"))
```

Each cell in a comp table or sensitivity matrix gets its own fill color based on the conditional formatting rule.

---

## 7. Chart Type Recommender (CHART-03)

### Algorithm

Given a data shape, recommend the best chart type:

```python
def recommend_chart_type(data: dict) -> str:
    """Suggest optimal chart type based on data characteristics."""

    # Single series, few categories (<=6) -> pie/donut
    # Single series, many categories (>6) -> bar
    # Multiple series, time-based categories -> line
    # Multiple series, non-time categories -> grouped_bar
    # Values that sum to whole (bridge) -> waterfall
    # 2D matrix data -> heatmap or sensitivity_table
    # Flow/relationship data -> sankey
    # Date range data -> gantt
    # Hierarchical data -> treemap or sunburst
    # Low/high range data -> football_field or tornado
```

Decision tree based on:
1. Number of series
2. Number of categories
3. Whether categories are temporal
4. Whether data represents ranges (low/high)
5. Whether data is hierarchical (parents)
6. Whether data represents flows (source/target)

---

## 8. Aither Reference: Financial Slide Patterns

Aither's `generate_deck.py` (referenced in STACK.md as 865-line production renderer) uses these patterns for financial slides that DeckForge should follow:

- **Comp tables**: python-pptx Table with explicit column widths, right-aligned numerics, header row in brand color
- **Waterfall**: Originally stacked-bar workaround, later migrated to static image embedding
- **Formatting**: Central formatting function applied per-cell based on column metadata
- **Layout**: Fixed coordinate positioning (DeckForge improves on this with constraint-based layout)

DeckForge's approach is architecturally superior (layout engine + theme system), but the rendering patterns are the same: tables for structured data, static images for complex visualizations, cell-level formatting for conditional coloring.

---

## Key Dependencies to Add

```toml
# Add to pyproject.toml [project.dependencies]
"plotly>=6.1",
"kaleido>=1.0.0",
"pandas>=2.2",
"openpyxl>=3.1",
```

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Kaleido Chrome not found in Docker | Low | High | Already in Dockerfile, add health check |
| Plotly chart quality insufficient for print | Low | Medium | scale=2 gives 2x DPI, test with projector resolution |
| pandas memory usage for large files | Medium | Low | Limit file size to 10MB in API, stream for larger |
| Financial formatting edge cases | Medium | Medium | Extensive test cases for each format type |
| Sensitivity matrix color interpolation | Low | Low | Use HSL interpolation for smooth gradients |

---

## Decision Summary

| Decision | Choice | Rationale |
|---|---|---|
| Waterfall approach | Plotly static image (NOT stacked-bar) | Higher visual quality, simpler code, finance pros don't need editability |
| Sensitivity matrix | python-pptx Table with cell coloring | Editable in PowerPoint, text values visible |
| Football field | Plotly horizontal bars | Complex range visualization, not editable natively |
| Comp table | python-pptx Table | Must be editable, standard table rendering |
| Risk matrix | python-pptx Table with colored cells | Simple grid, editable, conditional colors per cell |
| Chart recommender | Rule-based decision tree | No ML needed, deterministic, fast |
| Data ingestion | pandas + openpyxl | Industry standard, auto-detect column types |
| Image export | PNG at scale=2 (2x DPI) | Crisp at presentation scale, transparent background |
