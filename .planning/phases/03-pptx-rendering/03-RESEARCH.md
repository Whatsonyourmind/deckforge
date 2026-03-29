# Phase 3: PPTX Rendering — Research

**Researched:** 2026-03-26
**Confidence:** HIGH (python-pptx is well-understood, battle-tested, only option)

---

## 1. python-pptx Architecture

### Core Object Hierarchy

```
Presentation
  .slide_layouts[]         # from slide master (SlideMaster -> SlideLayout)
  .slide_masters[]         # master slides
  .slides[]                # actual slides
    .slide_layout          # reference to layout
    .shapes[]              # all visual elements on the slide
      .shape_type          # MSO_SHAPE_TYPE enum
      .text_frame          # for text boxes (TextFrame)
        .paragraphs[]      # Paragraph objects
          .runs[]          # Run objects (styled text spans)
            .font          # Font object (name, size, bold, italic, color)
            .text           # the text content
      .table               # for table shapes (Table)
      .chart               # for chart shapes (Chart)
      .image               # for picture shapes
    .notes_slide           # speaker notes
      .notes_text_frame    # TextFrame for notes
    .slide_id              # unique slide identifier
```

### Key Classes and Their Roles

| Class | Import | Purpose |
|-------|--------|---------|
| `Presentation` | `pptx.Presentation()` | Top-level document, holds slides, slide layouts |
| `Slide` | via `prs.slides.add_slide()` | Individual slide |
| `SlideLayout` | via `prs.slide_layouts[index]` | Template layout (title, blank, etc.) |
| `Shape` | via `slide.shapes` | Base for all visual elements |
| `TextFrame` | via `shape.text_frame` | Text container with paragraphs |
| `Paragraph` | via `text_frame.paragraphs[i]` | Paragraph with alignment, level |
| `Run` | via `paragraph.add_run()` | Styled text span within paragraph |
| `Font` | via `run.font` | Font name, size, bold, italic, color, underline |
| `Table` | via `shapes.add_table()` | Grid of cells with rows/columns |
| `Cell` | via `table.cell(row, col)` | Individual table cell |
| `Chart` | via `shapes.add_chart()` | Native editable chart |
| `ChartData` | `pptx.chart.data.ChartData` | Data container for charts |
| `Inches` | `pptx.util.Inches` | Convert inches to EMU (914400 EMU/inch) |
| `Pt` | `pptx.util.Pt` | Convert points to EMU (12700 EMU/pt) |
| `Emu` | `pptx.util.Emu` | Direct EMU value |
| `RGBColor` | `pptx.dml.color.RGBColor` | Color from hex (e.g., `RGBColor(0x0A, 0x1E, 0x3D)`) |

### EMU (English Metric Units)

python-pptx uses EMU internally. Conversion constants:
- **1 inch = 914400 EMU**
- **1 point = 12700 EMU**
- **1 cm = 360000 EMU**

The `Inches()`, `Pt()`, `Cm()`, `Emu()` helpers handle conversion. Our LayoutResult positions are in inches, so `Inches(position.x)` is the direct conversion.

### Creating a Blank Presentation

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu

prs = Presentation()

# Set 16:9 widescreen (13.333" x 7.5")
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
```

---

## 2. Mapping IR Slide Types to python-pptx Slide Layouts

### Strategy: Use Blank Layout Only

python-pptx ships with default slide layouts (Title Slide, Title and Content, Blank, etc.) but these are template-dependent and unreliable across different .pptx templates. Our approach:

**Use layout index 6 (Blank) for ALL slides.** Our layout engine already computes exact positions for every element. Using blank layouts means:
- No placeholder conflicts
- Full control over positioning
- Consistent behavior regardless of template
- Theme backgrounds applied programmatically

```python
blank_layout = prs.slide_layouts[6]  # Blank layout
slide = prs.slides.add_slide(blank_layout)
```

**Alternative approach if blank is not at index 6:** Iterate layouts to find one with no placeholders:

```python
def get_blank_layout(prs):
    for layout in prs.slide_layouts:
        if len(layout.placeholders) == 0:
            return layout
    # Fallback: use last layout or layout with fewest placeholders
    return min(prs.slide_layouts, key=lambda l: len(l.placeholders))
```

### Slide Background

Set per-slide background from theme's SlideMaster:

```python
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR

background = slide.background
fill = background.fill
fill.solid()
fill.fore_color.rgb = RGBColor.from_string("0A1E3D")  # hex without #
```

---

## 3. Element Rendering

### 3.1 Text Boxes

Text boxes are the most common element. Created via `shapes.add_textbox()`:

```python
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

txBox = slide.shapes.add_textbox(
    left=Inches(pos.x),
    top=Inches(pos.y),
    width=Inches(pos.width),
    height=Inches(pos.height),
)
tf = txBox.text_frame
tf.word_wrap = True
tf.auto_size = None  # We control sizing via layout engine

# Set vertical alignment
tf.paragraphs[0].alignment = PP_ALIGN.LEFT
```

**Text Formatting via Runs:**

```python
p = tf.paragraphs[0]
p.alignment = PP_ALIGN.LEFT
p.space_before = Pt(0)
p.space_after = Pt(6)

run = p.add_run()
run.text = "Hello World"
run.font.name = "Calibri"
run.font.size = Pt(18)
run.font.bold = True
run.font.italic = False
run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
```

**Bullet Lists:**

```python
for i, item in enumerate(items):
    p = tf.add_paragraph() if i > 0 else tf.paragraphs[0]
    p.text = item
    p.level = 0  # 0-8 indent levels
    p.font.size = Pt(18)
    # Bullet character is automatic at level >= 0
    # Custom bullet: requires lxml manipulation
```

**Word Wrapping:** `tf.word_wrap = True` enables automatic word wrapping within the text box bounds. Combined with our layout engine's text measurement, this produces correctly sized text boxes.

**Auto-size:** Set `tf.auto_size = None` to prevent python-pptx from auto-resizing. We rely on the layout engine for sizing. Other options: `MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT` (shrink box to text), `MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE` (shrink text to fit box — useful as safety net).

### 3.2 Tables

```python
rows, cols = len(data) + 1, len(headers)  # +1 for header row
table_shape = slide.shapes.add_table(
    rows=rows,
    cols=cols,
    left=Inches(pos.x),
    top=Inches(pos.y),
    width=Inches(pos.width),
    height=Inches(pos.height),
)
table = table_shape.table

# Set column widths (distribute evenly or proportionally)
col_width = Inches(pos.width / cols)
for i in range(cols):
    table.columns[i].width = col_width

# Header row
for j, header in enumerate(headers):
    cell = table.cell(0, j)
    cell.text = str(header)
    # Format header cell
    p = cell.text_frame.paragraphs[0]
    p.font.bold = True
    p.font.size = Pt(12)
    p.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    p.alignment = PP_ALIGN.CENTER
    # Cell fill (header background)
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(0x0A, 0x1E, 0x3D)

# Data rows
for i, row in enumerate(data):
    for j, val in enumerate(row):
        cell = table.cell(i + 1, j)
        cell.text = str(val) if val is not None else ""
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(11)
```

**Conditional Formatting:** python-pptx does not have a built-in conditional formatting API. Implement by:
1. Checking IR's `highlight_rows` list
2. Applying `cell.fill.solid()` + color for highlighted rows
3. Applying `cell.fill.solid()` with alternating row colors for zebra striping

**Footer Row:** If `TableContent.footer_row` is set, render the last row with distinct styling (bold, top border, different background).

**Cell Borders:** Requires lxml manipulation for per-cell border control:

```python
from pptx.oxml.ns import qn
from lxml import etree

def set_cell_border(cell, border_color="000000", border_width="12700"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    for edge in ["lnL", "lnR", "lnT", "lnB"]:
        ln = etree.SubElement(tcPr, qn(f"a:{edge}"))
        ln.set("w", border_width)
        solidFill = etree.SubElement(ln, qn("a:solidFill"))
        srgbClr = etree.SubElement(solidFill, qn("a:srgbClr"))
        srgbClr.set("val", border_color)
```

### 3.3 Images

```python
from pptx.util import Inches
import io
import httpx

# From URL: download first
async def download_image(url: str) -> bytes:
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.content

# From base64
import base64
image_bytes = base64.b64decode(content.base64)

# Add to slide
image_stream = io.BytesIO(image_bytes)
pic = slide.shapes.add_picture(
    image_stream,
    left=Inches(pos.x),
    top=Inches(pos.y),
    width=Inches(pos.width),
    height=Inches(pos.height),
)
```

**Image Fit Modes (from ImageContent.fit):**
- `contain`: Scale to fit within bounds, maintaining aspect ratio (default). Calculate scale factor from both dimensions, use the smaller one.
- `cover`: Scale to fill bounds, crop excess. Use the larger scale factor.
- `fill`: Stretch to exact bounds (ignore aspect ratio). Use width and height as-is.

**Contain implementation:**

```python
from PIL import Image as PILImage

def calculate_contain_dimensions(image_bytes, target_w, target_h):
    img = PILImage.open(io.BytesIO(image_bytes))
    img_w, img_h = img.size
    scale = min(target_w / img_w, target_h / img_h)
    final_w = img_w * scale
    final_h = img_h * scale
    # Center within target area
    offset_x = (target_w - final_w) / 2
    offset_y = (target_h - final_h) / 2
    return final_w, final_h, offset_x, offset_y
```

### 3.4 Shapes

```python
from pptx.enum.shapes import MSO_SHAPE

shape_map = {
    "rectangle": MSO_SHAPE.RECTANGLE,
    "circle": MSO_SHAPE.OVAL,
    "rounded_rect": MSO_SHAPE.ROUNDED_RECTANGLE,
    "arrow": MSO_SHAPE.RIGHT_ARROW,
    "line": None,  # Use add_connector instead
}

if content.shape == "line":
    connector = slide.shapes.add_connector(
        MSO_CONNECTOR_TYPE.STRAIGHT,
        Inches(pos.x), Inches(pos.y),
        Inches(pos.x + pos.width), Inches(pos.y + pos.height),
    )
else:
    shape = slide.shapes.add_shape(
        shape_map[content.shape],
        Inches(pos.x), Inches(pos.y),
        Inches(pos.width), Inches(pos.height),
    )
    if content.fill:
        shape.fill.solid()
        shape.fill.fore_color.rgb = RGBColor.from_string(content.fill.lstrip("#"))
    if content.stroke:
        shape.line.color.rgb = RGBColor.from_string(content.stroke.lstrip("#"))
```

---

## 4. Native Editable Charts via python-pptx

### Supported Native Chart Types

python-pptx supports these chart types natively via `XL_CHART_TYPE`:

| IR chart_type | XL_CHART_TYPE | Notes |
|--------------|---------------|-------|
| `bar` | `COLUMN_CLUSTERED` | Vertical bars |
| `stacked_bar` | `COLUMN_STACKED` | Vertical stacked |
| `grouped_bar` | `COLUMN_CLUSTERED` | Same as bar, multi-series |
| `horizontal_bar` | `BAR_CLUSTERED` | Horizontal bars |
| `line` | `LINE_MARKERS` | Line with markers |
| `multi_line` | `LINE_MARKERS` | Same, multiple series |
| `area` | `AREA` | Filled area |
| `stacked_area` | `AREA_STACKED` | Stacked area |
| `pie` | `PIE` | Single-series pie |
| `donut` | `DOUGHNUT` | Ring chart |
| `scatter` | `XY_SCATTER` | X-Y scatter |
| `combo` | `COLUMN_CLUSTERED` + overlay | Bar + line overlay |
| `radar` | `RADAR` | Spider/web chart |
| `bubble` | `BUBBLE` | Bubble chart |
| `funnel` | N/A (build from horizontal bar) | Not native -- use stacked bar workaround |

### Chart Creation Pattern

```python
from pptx.chart.data import CategoryChartData, XyChartData
from pptx.enum.chart import XL_CHART_TYPE

# Category-based charts (bar, line, area, pie)
chart_data = CategoryChartData()
chart_data.categories = ["Q1", "Q2", "Q3", "Q4"]
chart_data.add_series("Revenue", (100, 120, 140, 160))
chart_data.add_series("Profit", (20, 25, 30, 35))

chart_frame = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    Inches(pos.x), Inches(pos.y),
    Inches(pos.width), Inches(pos.height),
    chart_data,
)
chart = chart_frame.chart

# Scatter/Bubble charts
xy_data = XyChartData()
series = xy_data.add_series("Series 1")
series.add_data_point(1.0, 2.5)
series.add_data_point(2.0, 3.5)
```

### Chart Formatting

```python
from pptx.dml.color import RGBColor
from pptx.util import Pt

chart = chart_frame.chart

# Title
chart.has_title = True
chart.chart_title.text_frame.text = "Revenue by Quarter"

# Legend
chart.has_legend = True
chart.legend.position = XL_LEGEND_POSITION.BOTTOM
chart.legend.include_in_layout = False

# Series colors (theme-aware)
for i, series in enumerate(chart.series):
    fill = series.format.fill
    fill.solid()
    fill.fore_color.rgb = RGBColor.from_string(theme.chart_colors[i % len(theme.chart_colors)])

# Axis formatting
category_axis = chart.category_axis
value_axis = chart.value_axis
category_axis.tick_labels.font.size = Pt(10)
value_axis.tick_labels.font.size = Pt(10)

# Data labels
plot = chart.plots[0]
plot.has_data_labels = True
data_labels = plot.data_labels
data_labels.font.size = Pt(9)
data_labels.number_format = "0.0"
```

### Combo Charts

python-pptx supports combo charts by adding a secondary chart type overlay:

```python
# Create initial bar chart
chart_data = CategoryChartData()
chart_data.categories = categories
chart_data.add_series("Bars", bar_values)

chart_frame = slide.shapes.add_chart(
    XL_CHART_TYPE.COLUMN_CLUSTERED,
    left, top, width, height,
    chart_data,
)
chart = chart_frame.chart

# Add line overlay on secondary axis
from pptx.chart.data import CategoryChartData as CCD
line_data = CCD()
line_data.categories = categories
line_data.add_series("Line", line_values)

plot = chart.add_chart(XL_CHART_TYPE.LINE_MARKERS, line_data)
```

### Donut Inner Radius

The donut chart's hole size is configurable but requires lxml:

```python
# After creating DOUGHNUT chart:
plot_element = chart._chartSpace.chart.plotArea.plot[0]
plot_element.set(qn("c:holeSize"), str(int(inner_radius * 100)))
```

### Charts NOT Natively Supported

These require static image fallback (Plotly):
- `waterfall` -- build as stacked bar with invisible base series (native workaround possible but complex)
- `heatmap` -- no native equivalent
- `sankey` -- no native equivalent
- `gantt` -- no native equivalent
- `sunburst` -- no native equivalent
- `treemap` -- no native equivalent (PowerPoint 2016+ has treemap but python-pptx doesn't expose it)
- `tornado` -- build from horizontal bar (possible but complex)
- `football_field` -- build from horizontal range bar (possible but complex)
- `sensitivity_table` -- render as formatted table (not a chart)
- `funnel` -- PowerPoint 2016+ has native funnel, but python-pptx doesn't expose it; use horizontal bar approximation

**For Phase 3 scope:** Focus on native chart types. Static fallback (Plotly) charts are Phase 5 (CHART-02, PPTX-03).

---

## 5. Slide Transitions

python-pptx has limited built-in transition support. Transitions require lxml manipulation of the slide XML:

```python
from lxml import etree
from pptx.oxml.ns import qn

def set_transition(slide, transition_type, duration_ms=500):
    """Set slide transition via Open XML manipulation."""
    # Transition element goes in the slide element
    slide_element = slide._element

    # Remove existing transition
    for existing in slide_element.findall(qn("p:transition")):
        slide_element.remove(existing)

    if transition_type == "none":
        return

    # Create transition element
    transition = etree.SubElement(slide_element, qn("p:transition"))
    transition.set("spd", "med")  # slow, med, fast
    transition.set("advClick", "1")

    # Transition type mapping
    transition_map = {
        "fade": "fade",
        "slide": "push",   # 'slide' in our IR maps to push in OOXML
        "push": "push",
    }

    ooxml_type = transition_map.get(transition_type, "fade")

    if ooxml_type == "fade":
        etree.SubElement(transition, qn("p:fade"))
    elif ooxml_type == "push":
        push = etree.SubElement(transition, qn("p:push"))
        push.set("dir", "l")  # l=left, r=right, u=up, d=down
```

**IR Mapping:**

| IR Transition | Open XML | Notes |
|---------------|----------|-------|
| `none` | No `<p:transition>` element | Default |
| `fade` | `<p:fade/>` | Cross-fade |
| `slide` | `<p:push dir="l"/>` | Slide from right |
| `push` | `<p:push dir="l"/>` | Push from left |

---

## 6. Speaker Notes

python-pptx has direct API support for speaker notes:

```python
# Access or create notes slide
notes_slide = slide.notes_slide
notes_tf = notes_slide.notes_text_frame

# Clear existing and set new notes
notes_tf.clear()
p = notes_tf.paragraphs[0]
p.text = slide_ir.speaker_notes
p.font.size = Pt(12)
```

This is straightforward -- `slide.notes_slide` auto-creates the notes slide if it doesn't exist. The `notes_text_frame` is a standard TextFrame with paragraph/run formatting.

---

## 7. Font Handling

### System Fonts vs Embedded Fonts

python-pptx references fonts by name (e.g., `"Calibri"`, `"Arial"`). It does NOT embed fonts into the PPTX file. The font must be available on the machine that opens the file.

**Behavior when font is missing:**
1. PowerPoint silently substitutes a similar font
2. This can cause text reflow and layout shifts
3. LibreOffice has different substitution rules than PowerPoint

**Mitigation strategy:**
1. Use standard fonts that are available on Windows, macOS, and LibreOffice: `Calibri`, `Arial`, `Times New Roman`, `Consolas`
2. Our Docker image bundles `fonts-liberation` (Liberation Sans/Serif/Mono -- metric-compatible with Arial/Times/Courier)
3. Theme YAML files specify heading_family, body_family, mono_family
4. Text measurer uses the same fonts for measurement as will be used in the PPTX

**Font embedding via lxml (advanced, optional):**
True font embedding requires manipulating the OOXML package to include .ttf files and font relationship entries. This is complex and not needed for v1 since we use standard fonts.

### Fallback Chain

```python
def resolve_font_name(requested: str) -> str:
    """Map requested font to safe default if not standard."""
    SAFE_FONTS = {
        "Calibri", "Arial", "Times New Roman", "Consolas",
        "Cambria", "Georgia", "Verdana", "Tahoma",
        "Segoe UI", "Trebuchet MS", "Garamond",
    }
    if requested in SAFE_FONTS:
        return requested
    # Fallback mapping for common theme fonts
    FALLBACK = {
        "Helvetica": "Arial",
        "Helvetica Neue": "Arial",
        "SF Pro": "Calibri",
        "Inter": "Calibri",
        "Roboto": "Arial",
        "Open Sans": "Calibri",
    }
    return FALLBACK.get(requested, "Calibri")
```

---

## 8. Converting LayoutResult to python-pptx Positions

### Direct Mapping

LayoutResult positions are in inches. python-pptx's `Inches()` helper converts directly:

```python
from pptx.util import Inches

def position_to_pptx(pos: ResolvedPosition):
    """Convert layout engine position (inches) to python-pptx EMU values."""
    return {
        "left": Inches(pos.x),
        "top": Inches(pos.y),
        "width": Inches(pos.width),
        "height": Inches(pos.height),
    }
```

### Element Position from IR

After `LayoutEngine.layout_slide()` runs, each element has a `Position` object with `x, y, width, height` in inches. The renderer reads these directly:

```python
for element in slide.elements:
    if element.position is None:
        continue  # Skip unpositioned elements
    pos = element.position
    # pos.x, pos.y, pos.width, pos.height are all in inches
    # Convert: Inches(pos.x), Inches(pos.y), etc.
```

### Slide Dimensions

PPTX-08 requires 16:9 widescreen: 13.333" x 7.5"

```python
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
```

The layout engine's GridSystem already uses these dimensions (via theme spacing margins within the 13.333" x 7.5" canvas).

---

## 9. PNG Thumbnail Generation (for /v1/render/preview)

### Approach: LibreOffice Headless

The most reliable approach for PPTX-to-PNG is LibreOffice in headless mode:

```bash
libreoffice --headless --convert-to png --outdir /tmp/output /tmp/input.pptx
```

**Limitations:**
- Produces one PNG per slide
- Requires LibreOffice installed in the Docker image
- Adds ~200MB to Docker image (on top of existing Chromium for Kaleido)
- Conversion takes 2-5 seconds for a 10-slide deck

**Docker setup:**

```dockerfile
RUN apt-get update && apt-get install -y libreoffice-impress && rm -rf /var/lib/apt/lists/*
```

### Alternative: python-pptx + Pillow (draw-it-ourselves)

We could render slides to PNG by recreating the slide visually using Pillow. This avoids the LibreOffice dependency but:
- Extremely complex to implement (text rendering, charts, tables, shapes)
- Will never match PowerPoint's rendering fidelity
- Not worth the engineering investment for thumbnails

### Alternative: pdf2image (via LibreOffice)

1. Convert PPTX to PDF via LibreOffice headless
2. Convert PDF pages to PNG via pdf2image (poppler)

```python
import subprocess
import tempfile
from pdf2image import convert_from_path

def pptx_to_thumbnails(pptx_bytes: bytes, max_slides: int = 5) -> list[bytes]:
    with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as f:
        f.write(pptx_bytes)
        pptx_path = f.name

    # Convert to PDF
    subprocess.run([
        "libreoffice", "--headless", "--convert-to", "pdf",
        "--outdir", "/tmp", pptx_path
    ], check=True, timeout=30)

    pdf_path = pptx_path.replace(".pptx", ".pdf")

    # Convert PDF pages to PNG
    images = convert_from_path(pdf_path, first_page=1, last_page=max_slides, dpi=150)

    thumbnails = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        thumbnails.append(buf.getvalue())

    return thumbnails
```

### Recommended Approach

**Use LibreOffice headless -> PDF -> png via pdf2image.** This is the standard approach used by Aither and other production systems. It handles all elements (text, charts, tables, images) with high fidelity.

**Docker additions needed:**
```dockerfile
RUN apt-get update && apt-get install -y \
    libreoffice-impress \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*
```

**pip additions:**
```
pdf2image>=1.17.0
```

---

## 10. Rendering Architecture

### Pipeline Flow

```
IR Presentation
    |
    v
LayoutEngine.layout_presentation(presentation, brand_kit)
    |
    v
list[LayoutResult]   (each has: slide IR + positions dict)
    |
    v
PptxRenderer.render(presentation, layout_results, theme)
    |
    v
For each LayoutResult:
    1. Create blank slide
    2. Set background from SlideMaster
    3. For each element in slide.elements:
        - Look up element.position (filled by layout engine)
        - Dispatch to element renderer by element.type
        - Element renderer creates python-pptx shape at position
    4. Set transition (if specified)
    5. Set speaker notes (if specified)
    |
    v
prs.save(stream) -> bytes
```

### Element Renderer Registry

Mirror the pattern from layout PATTERN_REGISTRY:

```python
ELEMENT_RENDERERS: dict[str, type[BaseElementRenderer]] = {
    "heading": TextRenderer,
    "subheading": TextRenderer,
    "body_text": TextRenderer,
    "bullet_list": BulletListRenderer,
    "numbered_list": NumberedListRenderer,
    "callout_box": CalloutBoxRenderer,
    "pull_quote": PullQuoteRenderer,
    "footnote": TextRenderer,
    "label": TextRenderer,
    "table": TableRenderer,
    "chart": ChartRenderer,
    "kpi_card": KpiCardRenderer,
    "metric_group": MetricGroupRenderer,
    "progress_bar": ProgressBarRenderer,
    "gauge": GaugeRenderer,
    "sparkline": SparklineRenderer,
    "image": ImageRenderer,
    "icon": IconRenderer,
    "shape": ShapeRenderer,
    "divider": DividerRenderer,
    "spacer": SpacerRenderer,
    "logo": LogoRenderer,
    "background": BackgroundRenderer,
}
```

### File Structure

```
src/deckforge/rendering/
    __init__.py
    pptx_renderer.py          # PptxRenderer orchestrator
    element_renderers/
        __init__.py            # ELEMENT_RENDERERS registry
        base.py                # BaseElementRenderer ABC
        text.py                # TextRenderer, BulletListRenderer, etc.
        table.py               # TableRenderer
        chart.py               # ChartRenderer (native editable)
        image.py               # ImageRenderer
        shape.py               # ShapeRenderer, DividerRenderer
        data_viz.py            # KpiCardRenderer, GaugeRenderer, etc.
    chart_renderers/
        __init__.py            # CHART_RENDERERS registry
        base.py                # BaseChartRenderer ABC
        category.py            # Bar, Line, Area charts
        proportional.py        # Pie, Donut
        scatter.py             # Scatter, Bubble
        combo.py               # Combo chart
        radar.py               # Radar chart
    thumbnail.py               # PNG thumbnail generation
    utils.py                   # Color conversion, font resolution, etc.
```

---

## 11. Key Implementation Notes

### Color Conversion

Theme colors are hex strings like `"#0A1E3D"`. python-pptx uses `RGBColor`:

```python
def hex_to_rgb(hex_color: str) -> RGBColor:
    hex_color = hex_color.lstrip("#")
    return RGBColor(
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )
```

### Thread Safety

python-pptx `Presentation` objects are not thread-safe. Each render must create its own `Presentation()` instance. This is already the case since each render task creates a fresh presentation.

### Memory Considerations

A typical 10-slide PPTX with charts and images is 2-10 MB in memory. For the sync render endpoint (API-01, <=10 slides), this is well within acceptable limits. The entire render pipeline (layout + PPTX generation) should complete in under 3 seconds.

### Error Handling

The renderer should catch and wrap python-pptx errors:
- `ValueError` from invalid chart data (e.g., mismatched series lengths)
- `PackageNotFoundError` from corrupt template operations
- `KeyError` from missing XML elements during lxml manipulation

Wrap in a `RenderError` exception with the slide index and element type for debugging.

---

## Sources

- python-pptx 1.0.2 source code and API (training data, verified against PyPI listing)
- python-pptx documentation patterns (Presentation, Slide, Shape, Chart, Table APIs)
- Open XML SDK specification for transition elements
- LibreOffice headless conversion documentation
- pdf2image library documentation
- STACK.md research (verified library versions and architecture decisions)

---

*Researched: 2026-03-26*
*Confidence: HIGH — python-pptx is the sole production-grade option, well-documented, battle-tested*
