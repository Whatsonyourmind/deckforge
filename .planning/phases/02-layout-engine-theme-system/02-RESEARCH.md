# Phase 2: Layout Engine + Theme System - Research

**Researched:** 2026-03-26
**Domain:** Constraint-based slide layout, YAML theme system, text measurement, accessibility
**Confidence:** MEDIUM-HIGH

## Summary

Phase 2 is the highest-risk R&D component in DeckForge. There is no off-the-shelf Python library for constraint-based slide layout -- this must be custom-built on top of kiwisolver (Cassowary constraint solver). The layout engine must convert slide type + content volume into element positions on a 12-column grid for 16:9 slides (13.333" x 7.5"). Text measurement via Pillow's FreeType integration provides bounding box estimation without rendering. The theme system uses YAML definitions with variable references, resolved at render time, with brand kit overlays via deep merge with protected keys.

The critical insight from research is that **simplicity wins over generality**. Rather than building a fully general constraint solver that handles arbitrary layouts, DeckForge should define **layout patterns per slide type** -- predefined constraint sets that the solver applies. Each slide type (title, bullets, two_column, chart, table, etc.) has a known set of layout regions. The solver's job is to **size those regions based on content volume**, not to discover the layout from scratch. This reduces the problem from "general UI layout" to "parameterized template solving" -- dramatically simpler while still adaptive.

**Primary recommendation:** Build the layout engine as a pattern-based constraint system: each slide type defines its layout regions and constraints; kiwisolver solves for actual dimensions based on content measurement; adaptive overflow handling (font reduction, reflow, split) runs as a post-solve verification pass.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LAYOUT-01 | Constraint-based layout solver using kiwisolver on 12-column grid | kiwisolver API verified (Variable, Solver, Constraint with strengths). Grid system maps to constraint variables for column boundaries. |
| LAYOUT-02 | Text measurement via Pillow + FreeType for bounding box calculation | Pillow ImageFont.truetype + getbbox/getlength API verified. DPI conversion formula documented (72pt = 1in, pixel/DPI = inches). |
| LAYOUT-03 | Adaptive content handling: overflow -> reduce font -> reflow -> split to multi-slide | Pillow measurement enables iterative font reduction loop. Kiwisolver re-solve is fast (incremental). Split logic is custom. |
| LAYOUT-04 | Visual hierarchy enforcement (title -> subtitle -> body -> footnote) | Theme font scale defines hierarchy. Constraint strengths (required > strong > medium > weak) enforce ordering. |
| LAYOUT-05 | Consistent spacing verification (+-2px tolerance) and alignment snapping | Kiwisolver constraint inequalities with tolerance bands. Post-solve verification pass checks alignment. |
| LAYOUT-06 | Layout patterns per slide type (title, bullets, two_column, chart, table, etc.) | Pattern-based approach validated by enaml grid_helper architecture. Each slide type = a constraint template. |
| THEME-01 | 15 curated themes defined in YAML with full color/typography/spacing specs | PyYAML + 3-tier design token pattern (reference -> semantic -> component) documented. |
| THEME-02 | Theme registry that loads and resolves variable references ($colors.primary -> #0A1E3D) | Custom variable resolution with recursive string interpolation. Straightforward implementation. |
| THEME-03 | Brand kit overlay system merging on top of themes | Deep merge with protected keys pattern documented. Existing BrandKit IR model aligns. |
| THEME-04 | Slide masters per slide type within each theme | YAML structure maps slide_type -> layout region definitions + style overrides per theme. |
| THEME-05 | Color theory engine with WCAG AA contrast validation (4.5:1 text, 3:1 large) | W3C G18 algorithm verified. wcag-contrast-ratio library available or trivial to implement (~30 lines). |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| kiwisolver | >=1.4.8 | Cassowary constraint solver | 10-500x faster than original Cassowary. C++ core with Python bindings. Used by matplotlib, enaml. The only production Cassowary implementation in Python. |
| Pillow | >=12.1.1 | Text measurement via FreeType | Already in project deps. ImageFont.truetype() + getbbox() provides pixel-accurate text measurement without rendering. |
| PyYAML | >=6.0 | Theme YAML parsing | Already in project deps. Standard YAML parser for Python. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| wcag-contrast-ratio | 0.9 | WCAG contrast validation | Optional -- the algorithm is only ~30 lines. Could use the library or implement inline. Recommend inline for zero-dependency. |
| deepmerge | >=2.0 | Deep dict merge for brand kit overlay | Optional -- recursive merge is ~20 lines. Recommend inline implementation with protected-key support that deepmerge does not natively provide. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| kiwisolver | python-constraint | python-constraint is a CSP solver (discrete domains), not linear constraints. Wrong tool for continuous layout positioning. |
| kiwisolver | Custom linear solver | Reinventing Cassowary is months of work. kiwisolver is battle-tested. |
| Pillow text measurement | fontTools | fontTools provides raw font metrics but requires manual glyph-by-glyph calculation. Pillow wraps FreeType which handles kerning, ligatures, shaping. |
| YAML themes | JSON themes | YAML is more human-readable for theme authors. Supports comments, multi-line strings. |
| wcag-contrast-ratio lib | Inline implementation | Library is tiny (30 lines of actual logic) and has not been updated since Python 2.7 era. Implement inline. |

**Installation (new dependencies):**
```bash
pip install kiwisolver>=1.4.8
```
Note: kiwisolver, Pillow, and PyYAML are already in pyproject.toml. No new dependencies needed.

## Architecture Patterns

### Recommended Project Structure

```
src/deckforge/
  layout/
    __init__.py
    engine.py           # LayoutEngine: orchestrates solve cycle
    solver.py           # SlideLayoutSolver: kiwisolver wrapper
    grid.py             # GridSystem: 12-column grid definitions
    text_measurer.py    # TextMeasurer: Pillow font metrics
    patterns/
      __init__.py
      base.py           # BaseLayoutPattern ABC
      title.py          # TitleSlidePattern
      bullets.py        # BulletPointsPattern
      two_column.py     # TwoColumnPattern
      chart.py          # ChartSlidePattern
      table.py          # TableSlidePattern
      generic.py        # GenericPattern (fallback)
    overflow.py         # AdaptiveOverflowHandler
    types.py            # LayoutResult, ResolvedPosition, etc.
  themes/
    __init__.py
    registry.py         # ThemeRegistry: loads + caches themes
    resolver.py         # ThemeResolver: variable interpolation
    brand_kit_merger.py # BrandKitMerger: deep merge with protected keys
    contrast.py         # ContrastChecker: WCAG AA validation
    types.py            # ResolvedTheme, ThemeColors, ThemeTypography
    data/
      executive-dark.yaml
      corporate-blue.yaml
      minimal-light.yaml
      ... (15 themes)
```

### Pattern 1: Layout Pattern Per Slide Type

**What:** Each slide type has a dedicated LayoutPattern class that generates kiwisolver constraints for its known layout regions. The solver computes actual positions based on content measurements.

**When to use:** Always. This is the core architecture.

**Why:** Reduces the problem from "arbitrary layout" to "parameterized template solving." A title slide always has a title region and subtitle region -- the question is how big they should be given the actual text, not where they should go.

```python
# Source: Architecture pattern derived from enaml grid_helper
from abc import ABC, abstractmethod
from kiwisolver import Variable, Solver, Constraint

class LayoutRegion:
    """A named region on the slide with kiwisolver variables."""
    def __init__(self, name: str):
        self.name = name
        self.left = Variable(f"{name}.left")
        self.top = Variable(f"{name}.top")
        self.width = Variable(f"{name}.width")
        self.height = Variable(f"{name}.height")

    @property
    def right(self):
        return self.left + self.width

    @property
    def bottom(self):
        return self.top + self.height


class BaseLayoutPattern(ABC):
    """Base class for slide-type-specific layout patterns."""

    @abstractmethod
    def create_regions(self) -> list[LayoutRegion]:
        """Define the named regions for this slide type."""
        ...

    @abstractmethod
    def create_constraints(
        self,
        regions: list[LayoutRegion],
        grid: GridSystem,
        measurements: dict[str, BoundingBox],
    ) -> list[Constraint]:
        """Generate constraints based on content measurements."""
        ...


class BulletPointsPattern(BaseLayoutPattern):
    """Layout pattern for bullet_points slide type."""

    def create_regions(self) -> list[LayoutRegion]:
        return [
            LayoutRegion("title"),
            LayoutRegion("subtitle"),
            LayoutRegion("bullets"),
            LayoutRegion("footnote"),
        ]

    def create_constraints(self, regions, grid, measurements):
        title, subtitle, bullets, footnote = regions
        constraints = []

        # Title at top, spanning full content width
        constraints.append(title.left == grid.content_left)
        constraints.append(title.width == grid.content_width)
        constraints.append(title.top == grid.content_top)
        # Title height from text measurement (required)
        constraints.append(title.height == measurements["title"].height)

        # Subtitle below title with spacing
        constraints.append(subtitle.top == title.bottom + grid.spacing)
        constraints.append(subtitle.left == grid.content_left)
        constraints.append(subtitle.width == grid.content_width)

        # Bullets fill remaining space (strong, not required)
        constraints.append(bullets.top == subtitle.bottom + grid.spacing)
        constraints.append(bullets.left == grid.content_left)
        constraints.append(bullets.width == grid.content_width)
        constraints.append(
            (bullets.height >= measurements["bullets"].min_height) | "strong"
        )

        # Footnote at bottom
        constraints.append(footnote.bottom == grid.content_bottom)
        constraints.append(footnote.left == grid.content_left)
        constraints.append(footnote.width == grid.content_width)

        # Bullets fill space between subtitle and footnote
        constraints.append(bullets.bottom <= footnote.top - grid.spacing)

        return constraints
```

### Pattern 2: Grid System as Constraint Variables

**What:** The 12-column grid is defined as a set of kiwisolver variables that establish column boundaries, margins, and gutters. All layout patterns reference these variables rather than hard-coded coordinates.

**When to use:** Every layout operation.

```python
# Source: Adapted from enaml grid_helper + PowerPoint 16:9 dimensions
from kiwisolver import Variable

class GridSystem:
    """12-column grid system for 16:9 slides (13.333" x 7.5")."""

    SLIDE_WIDTH_INCHES = 13.333
    SLIDE_HEIGHT_INCHES = 7.5
    NUM_COLUMNS = 12

    def __init__(
        self,
        margin_left: float = 0.5,   # inches
        margin_right: float = 0.5,
        margin_top: float = 0.5,
        margin_bottom: float = 0.5,
        gutter: float = 0.167,       # inches (~12px at 72 DPI)
    ):
        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.gutter = gutter

        # Derived values (all in inches)
        self.content_left = margin_left
        self.content_top = margin_top
        self.content_width = (
            self.SLIDE_WIDTH_INCHES - margin_left - margin_right
        )
        self.content_height = (
            self.SLIDE_HEIGHT_INCHES - margin_top - margin_bottom
        )
        self.content_bottom = self.SLIDE_HEIGHT_INCHES - margin_bottom
        self.content_right = self.SLIDE_WIDTH_INCHES - margin_right

        # Column width (without gutters)
        total_gutter = gutter * (self.NUM_COLUMNS - 1)
        self.column_width = (self.content_width - total_gutter) / self.NUM_COLUMNS
        self.spacing = 0.167  # standard inter-element spacing

    def column_span_width(self, start_col: int, span: int) -> float:
        """Width of a span of columns (including internal gutters)."""
        col_width = self.column_width * span
        internal_gutters = self.gutter * (span - 1)
        return col_width + internal_gutters

    def column_left(self, col: int) -> float:
        """Left edge of column (0-indexed)."""
        return self.content_left + col * (self.column_width + self.gutter)
```

### Pattern 3: Text Measurement with DPI Conversion

**What:** Measure text bounding boxes using Pillow's FreeType integration, then convert pixel measurements to inches for the layout solver.

**When to use:** Before every layout solve, to provide content measurements.

```python
# Source: Pillow ImageFont API + DPI conversion math
from PIL import ImageFont, ImageDraw, Image

class TextMeasurer:
    """Measure text bounding boxes without rendering full slides."""

    # Pillow renders at 72 DPI by default for TrueType fonts
    # 1 point = 1/72 inch, so at 72 DPI: 1pt = 1px
    MEASUREMENT_DPI = 72

    def __init__(self, font_dir: str = "/usr/share/fonts"):
        self._font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}
        self._font_dir = font_dir

    def _get_font(self, font_name: str, size_pt: int) -> ImageFont.FreeTypeFont:
        key = (font_name, size_pt)
        if key not in self._font_cache:
            # size parameter is in points; at 72 DPI, 1pt = 1px
            self._font_cache[key] = ImageFont.truetype(
                self._resolve_font_path(font_name),
                size=size_pt,
            )
        return self._font_cache[key]

    def measure_text(
        self,
        text: str,
        font_name: str,
        size_pt: int,
        max_width_inches: float | None = None,
    ) -> BoundingBox:
        """Measure text and return bounding box in inches."""
        font = self._get_font(font_name, size_pt)

        if max_width_inches is not None:
            # Word-wrap text to fit within max width
            max_width_px = max_width_inches * self.MEASUREMENT_DPI
            text = self._word_wrap(text, font, max_width_px)

        if "\n" in text:
            # Use ImageDraw for multiline measurement
            img = Image.new("RGB", (1, 1))
            draw = ImageDraw.Draw(img)
            bbox = draw.multiline_textbbox((0, 0), text, font=font)
        else:
            bbox = font.getbbox(text)

        left, top, right, bottom = bbox
        width_px = right - left
        height_px = bottom - top

        # Convert pixels to inches (at 72 DPI: 1px = 1/72 inch)
        return BoundingBox(
            width_inches=width_px / self.MEASUREMENT_DPI,
            height_inches=height_px / self.MEASUREMENT_DPI,
        )
```

### Pattern 4: Solve Cycle Orchestration

**What:** The layout engine orchestrates: measure content -> generate constraints -> solve -> verify -> handle overflow.

**When to use:** Every slide layout operation.

```python
# Source: Derived from enaml LayoutManager pattern
from kiwisolver import Solver

class LayoutEngine:
    """Orchestrates the full layout solve cycle."""

    def __init__(self, text_measurer: TextMeasurer, theme_resolver: ThemeResolver):
        self._measurer = text_measurer
        self._theme_resolver = theme_resolver
        self._patterns: dict[SlideType, BaseLayoutPattern] = {}

    def layout_slide(
        self,
        slide: Slide,
        theme: ResolvedTheme,
        grid: GridSystem,
    ) -> LayoutResult:
        """Solve layout for a single slide. May return multiple slides if split."""
        pattern = self._patterns[slide.slide_type]

        # 1. Measure all text content
        measurements = self._measure_elements(slide, theme)

        # 2. Create regions and constraints
        regions = pattern.create_regions()
        constraints = pattern.create_constraints(regions, grid, measurements)

        # 3. Solve
        solver = Solver()
        for c in constraints:
            solver.addConstraint(c)
        solver.updateVariables()

        # 4. Extract positions
        positions = {
            region.name: ResolvedPosition(
                x=region.left.value(),
                y=region.top.value(),
                width=region.width.value(),
                height=region.height.value(),
            )
            for region in regions
        }

        # 5. Verify overflow and adapt
        return self._verify_and_adapt(slide, positions, theme, grid)
```

### Pattern 5: Theme YAML Structure (3-Tier Design Tokens)

**What:** Themes use a 3-tier token system: reference tokens (raw values), semantic tokens (named references), and component tokens (per-element styles).

**When to use:** All theme definitions.

```yaml
# Source: Design token pattern from materialui.co + presentation domain
# themes/data/executive-dark.yaml

name: "Executive Dark"
description: "Professional dark theme for board presentations"
version: "1.0"

# Tier 1: Reference tokens (raw values)
colors:
  navy_900: "#0A1E3D"
  navy_800: "#122B50"
  navy_700: "#1A3A68"
  white: "#FFFFFF"
  gray_100: "#F5F5F5"
  gray_300: "#D4D4D4"
  gray_500: "#737373"
  blue_500: "#3B82F6"
  green_500: "#22C55E"
  red_500: "#EF4444"
  amber_500: "#F59E0B"

# Tier 2: Semantic tokens (references)
palette:
  primary: "$colors.navy_900"
  secondary: "$colors.blue_500"
  accent: "$colors.green_500"
  background: "$colors.navy_900"
  surface: "$colors.navy_800"
  text_primary: "$colors.white"
  text_secondary: "$colors.gray_300"
  text_muted: "$colors.gray_500"
  positive: "$colors.green_500"
  negative: "$colors.red_500"
  warning: "$colors.amber_500"

typography:
  heading_family: "Montserrat"
  body_family: "Open Sans"
  mono_family: "JetBrains Mono"
  scale:
    h1: 36
    h2: 28
    h3: 22
    subtitle: 18
    body: 14
    caption: 12
    footnote: 10
  weights:
    heading: 700
    subtitle: 600
    body: 400
    caption: 400
  line_height: 1.4

spacing:
  margin_top: 0.5       # inches
  margin_bottom: 0.5
  margin_left: 0.5
  margin_right: 0.5
  gutter: 0.167
  element_gap: 0.167     # between elements
  section_gap: 0.333     # between sections

# Tier 3: Component tokens (per-element/slide-type)
slide_masters:
  title_slide:
    background: "$palette.background"
    title:
      font_family: "$typography.heading_family"
      font_size: "$typography.scale.h1"
      font_weight: "$typography.weights.heading"
      color: "$palette.text_primary"
      alignment: "center"
      region: "center"      # layout pattern hint
    subtitle:
      font_family: "$typography.body_family"
      font_size: "$typography.scale.subtitle"
      color: "$palette.text_secondary"
      alignment: "center"

  bullet_points:
    background: "$palette.surface"
    title:
      font_family: "$typography.heading_family"
      font_size: "$typography.scale.h2"
      color: "$palette.text_primary"
    bullets:
      font_family: "$typography.body_family"
      font_size: "$typography.scale.body"
      color: "$palette.text_primary"
      bullet_color: "$palette.accent"
      indent: 0.25

  two_column_text:
    background: "$palette.surface"
    title:
      font_family: "$typography.heading_family"
      font_size: "$typography.scale.h2"
      color: "$palette.text_primary"
    left_column:
      columns: 6   # out of 12
    right_column:
      columns: 6

  chart_slide:
    background: "$palette.surface"
    title:
      font_family: "$typography.heading_family"
      font_size: "$typography.scale.h2"
      color: "$palette.text_primary"
    chart_area:
      columns: 12  # full width
      min_height: 4.0  # inches

# Chart colors (ordered for data series)
chart_colors:
  - "$palette.secondary"
  - "$palette.accent"
  - "$colors.amber_500"
  - "$colors.red_500"
  - "$colors.gray_300"

# Logo placement defaults
logo:
  max_width: 1.5
  max_height: 0.5
  placement: "bottom_right"
  opacity: 0.8

# Protected keys (cannot be overridden by brand kit)
_protected:
  - spacing
  - typography.scale
  - typography.line_height
```

### Anti-Patterns to Avoid

- **General-purpose constraint layout:** Do NOT try to build a layout engine that discovers element positions from arbitrary constraints. Each slide type has a known structure. Use patterns, not discovery.

- **Hard-coded pixel coordinates:** Do NOT position elements with fixed coordinates. Everything goes through the grid system and solver. This is what makes themes interchangeable.

- **Measuring text after positioning:** Do NOT place text first and then check if it fits. Measure FIRST, then position. The solve cycle must be: measure -> constrain -> solve -> verify.

- **Synchronous font loading on every measurement:** Font loading is expensive. Cache loaded fonts by (name, size) tuple. A single slide with 10 elements should not load 10 separate font objects.

- **Theme variable resolution at YAML load time:** Resolve variables lazily at access time or in a single pass after loading. This allows brand kit overlays to replace token values before resolution.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Constraint solving | Custom linear equation solver | kiwisolver Solver | Cassowary algorithm is complex (incremental simplex). kiwisolver is 40x faster than naive implementations. |
| Font glyph metrics | Manual FreeType FFI bindings | Pillow ImageFont.truetype() | Pillow wraps FreeType with kerning, ligatures, and shaping support. Manual implementation misses edge cases. |
| YAML parsing | Custom config parser | PyYAML safe_load | Standard, secure, handles all YAML types. |
| sRGB luminance | Approximate gamma calculation | W3C G18 exact formula | The sRGB linearization has a piecewise function with threshold at 0.04045. Approximations produce wrong contrast ratios. |

**Key insight:** The layout engine is custom because no library exists for slide layout. But every COMPONENT of the engine (constraint solving, text measurement, YAML parsing, color math) has a standard solution. Hand-roll the orchestration; use libraries for the math.

## Common Pitfalls

### Pitfall 1: Font Metrics Mismatch Between Measurement and Rendering

**What goes wrong:** Text is measured with one font (e.g., "Liberation Sans" in Docker) but rendered with another (e.g., "Arial" in PowerPoint on the user's machine). The bounding boxes are different, causing overflow in the final presentation.

**Why it happens:** Pillow measures with the exact .ttf file available in the container. python-pptx writes font name references into the PPTX XML. PowerPoint uses whatever font the user has installed, which may have different metrics.

**How to avoid:**
1. Bundle theme fonts in the Docker image (Liberation Sans, DejaVu, Open Sans, Montserrat -- all free Google Fonts)
2. Measure with the EXACT font files that the theme specifies
3. Add 5-10% safety margin to text bounding boxes to account for cross-platform font rendering differences
4. Fall back to a known-available metric-compatible font if the specified font is missing

**Warning signs:** Text looks fine in layout preview but overflows when opened in PowerPoint on Windows/Mac.

### Pitfall 2: Kiwisolver Infeasible Constraints

**What goes wrong:** The solver raises `UnsatisfiableConstraint` when constraints are contradictory (e.g., element must be 5 inches tall but only 3 inches of space remain).

**Why it happens:** Content exceeds available space and all constraints are "required" strength. The solver cannot find a solution.

**How to avoid:**
1. Use "strong" strength (not "required") for content size constraints
2. Use "required" only for slide boundaries, margins, and non-overlap rules
3. Catch `UnsatisfiableConstraint` and trigger the overflow cascade (reduce font -> reflow -> split)
4. Always have a fallback: minimum font size (10pt) + slide split as ultimate escape

**Warning signs:** Solver exceptions during testing with long content.

### Pitfall 3: Pillow getbbox Does Not Handle Newlines

**What goes wrong:** `font.getbbox("Line 1\nLine 2")` returns the bounding box of the entire string AS A SINGLE LINE. Newlines are ignored.

**Why it happens:** Pillow's ImageFont.getbbox() is a single-line measurement. Multiline text requires ImageDraw.multiline_textbbox().

**How to avoid:** Always check for newlines. For multiline text:
```python
img = Image.new("RGB", (1, 1))
draw = ImageDraw.Draw(img)
bbox = draw.multiline_textbbox((0, 0), text, font=font)
```
This creates a tiny throwaway image just for measurement -- no actual rendering happens.

**Warning signs:** Single-line bounding boxes for multi-line content; elements that are too short.

### Pitfall 4: DPI Confusion in Text Measurement

**What goes wrong:** Pillow's font size parameter is in "points" but the relationship to pixels depends on DPI. Developers assume 1pt = 1px (true at 72 DPI) or 1pt = 1.33px (true at 96 DPI). Wrong DPI assumption means all bounding boxes are off by ~33%.

**Why it happens:** Pillow's truetype() size parameter is in points. At its default rendering (72 DPI), 1pt = 1px. But if you're converting to inches for slide layout, you need to know the DPI.

**How to avoid:** Standardize on 72 DPI for all Pillow text measurement. At 72 DPI:
- 1 point = 1 pixel
- pixels / 72 = inches
- font size 14pt renders at 14px, which is 14/72 = 0.194 inches

This is the simplest model and avoids all DPI confusion.

**Warning signs:** Layout positions are consistently off by ~33%.

### Pitfall 5: Theme Variable Circular References

**What goes wrong:** A theme YAML contains `$colors.primary` referencing `$palette.main` which references `$colors.primary`. Variable resolution enters infinite recursion.

**Why it happens:** The 3-tier token system allows cross-referencing. Without cycle detection, circular references crash the resolver.

**How to avoid:**
1. Resolve in tier order: reference tokens first, then semantic, then component
2. Track resolution stack; if a variable appears twice during resolution, raise a descriptive error
3. Validate all themes at startup (not at render time) to catch cycles early

**Warning signs:** Stack overflow during theme loading; theme unit tests that hang.

### Pitfall 6: Brand Kit Overriding Protected Properties

**What goes wrong:** A user's brand kit specifies `spacing.margin_left: 0.1` (too narrow) or `typography.scale.body: 8` (too small). The layout breaks because structural constraints are violated.

**Why it happens:** Deep merge without protection replaces any key that matches.

**How to avoid:**
1. Define PROTECTED_KEYS set in theme schema
2. Deep merge skips protected keys (logs a warning if brand kit attempts to override)
3. Protected properties: spacing, typography.scale, typography.line_height, min_font_sizes, grid

**Warning signs:** User themes that produce unreadable or broken layouts.

## Code Examples

Verified patterns from official sources and documentation:

### Kiwisolver Basic Usage

```python
# Source: kiwisolver test_solver.py (GitHub nucleic/kiwi)
from kiwisolver import Variable, Solver

# Create variables for element positions
title_top = Variable("title_top")
title_height = Variable("title_height")
body_top = Variable("body_top")
body_height = Variable("body_height")

# Create solver
solver = Solver()

# Required constraints: slide boundaries
solver.addConstraint(title_top >= 0.5)                     # top margin
solver.addConstraint(title_top + title_height <= 7.0)       # bottom boundary
solver.addConstraint(body_top >= title_top + title_height + 0.167)  # spacing

# Strong constraints: preferred sizes from text measurement
solver.addConstraint((title_height == 0.75) | "strong")     # measured title height
solver.addConstraint((body_height == 3.5) | "strong")       # measured body height

# Weak constraint: body fills available space
solver.addConstraint((body_height == 5.0) | "weak")

# Solve
solver.updateVariables()

# Read results
print(f"Title: top={title_top.value():.3f}, height={title_height.value():.3f}")
print(f"Body:  top={body_top.value():.3f}, height={body_height.value():.3f}")
```

### Pillow Text Measurement

```python
# Source: Pillow ImageFont API docs + getbbox/multiline_textbbox
from PIL import ImageFont, ImageDraw, Image

# Load font (size in points; at 72 DPI: 1pt = 1px)
font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 14)

# Single-line measurement
bbox = font.getbbox("Quarter 3 Revenue Analysis")
left, top, right, bottom = bbox
width_inches = (right - left) / 72
height_inches = (bottom - top) / 72

# Multi-line measurement (getbbox ignores newlines!)
text = "Point 1: Revenue grew 15%\nPoint 2: Margins expanded\nPoint 3: New markets entered"
img = Image.new("RGB", (1, 1))
draw = ImageDraw.Draw(img)
bbox = draw.multiline_textbbox((0, 0), text, font=font)
left, top, right, bottom = bbox
width_inches = (right - left) / 72
height_inches = (bottom - top) / 72

# Word wrapping: break text to fit within max width
def word_wrap(text: str, font: ImageFont.FreeTypeFont, max_width_px: float) -> str:
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        if font.getlength(test_line) <= max_width_px:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)
```

### WCAG AA Contrast Validation

```python
# Source: W3C WCAG 2.1 Technique G18
def relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate relative luminance from RGB (0-255)."""
    def linearize(channel: int) -> float:
        srgb = channel / 255
        if srgb <= 0.04045:
            return srgb / 12.92
        return ((srgb + 0.055) / 1.055) ** 2.4

    return 0.2126 * linearize(r) + 0.7152 * linearize(g) + 0.0722 * linearize(b)


def contrast_ratio(color1: tuple[int, int, int], color2: tuple[int, int, int]) -> float:
    """Calculate WCAG contrast ratio between two RGB colors."""
    l1 = relative_luminance(*color1)
    l2 = relative_luminance(*color2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def passes_wcag_aa(
    fg: tuple[int, int, int],
    bg: tuple[int, int, int],
    is_large_text: bool = False,
) -> bool:
    """Check WCAG AA compliance.

    Normal text: 4.5:1 minimum
    Large text (>=18pt or >=14pt bold): 3:1 minimum
    """
    ratio = contrast_ratio(fg, bg)
    threshold = 3.0 if is_large_text else 4.5
    return ratio >= threshold


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color string to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return (
        int(hex_color[0:2], 16),
        int(hex_color[2:4], 16),
        int(hex_color[4:6], 16),
    )
```

### Theme Variable Resolution

```python
# Source: Custom implementation based on design token pattern
import re
import yaml
from pathlib import Path

VARIABLE_PATTERN = re.compile(r'\$([a-zA-Z_][a-zA-Z0-9_.]*)')

class ThemeResolver:
    """Resolve variable references in theme YAML."""

    def __init__(self, theme_data: dict):
        self._data = theme_data
        self._resolved_cache: dict[str, str | int | float] = {}

    def resolve(self, path: str) -> str | int | float:
        """Resolve a dotted path like 'colors.navy_900' to its value."""
        if path in self._resolved_cache:
            return self._resolved_cache[path]

        # Track resolution stack for cycle detection
        return self._resolve_with_stack(path, set())

    def _resolve_with_stack(self, path: str, stack: set[str]):
        if path in stack:
            raise ValueError(f"Circular reference detected: {path} -> {stack}")
        stack.add(path)

        value = self._get_nested(self._data, path)
        if isinstance(value, str) and value.startswith("$"):
            ref_path = value[1:]  # strip leading $
            value = self._resolve_with_stack(ref_path, stack)

        self._resolved_cache[path] = value
        return value

    def _get_nested(self, data: dict, path: str):
        parts = path.split(".")
        current = data
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                raise KeyError(f"Theme path not found: {path}")
            current = current[part]
        return current

    def resolve_all_variables(self, obj):
        """Recursively resolve all $variable references in a dict/list/str."""
        if isinstance(obj, str):
            return VARIABLE_PATTERN.sub(
                lambda m: str(self.resolve(m.group(1))), obj
            )
        elif isinstance(obj, dict):
            return {k: self.resolve_all_variables(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.resolve_all_variables(item) for item in obj]
        return obj
```

### Deep Merge with Protected Keys

```python
# Source: Custom implementation for brand kit overlay
from copy import deepcopy

PROTECTED_KEYS = frozenset({
    "spacing",
    "typography.scale",
    "typography.line_height",
    "_protected",
})

def deep_merge(
    base: dict,
    overlay: dict,
    protected: frozenset[str] = PROTECTED_KEYS,
    _path: str = "",
) -> dict:
    """Deep merge overlay into base, skipping protected keys."""
    result = deepcopy(base)
    for key, value in overlay.items():
        full_path = f"{_path}.{key}" if _path else key

        # Skip protected keys
        if full_path in protected:
            continue

        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value, protected, full_path)
        else:
            result[key] = deepcopy(value)

    return result
```

### Adaptive Overflow Cascade

```python
# Source: Architecture pattern from PITFALLS.md + text measurement
class AdaptiveOverflowHandler:
    """Handle content that exceeds its layout region."""

    FONT_SIZE_FLOOR = 10  # points - never go below this
    FONT_REDUCTION_STEP = 2  # points per iteration

    def handle_overflow(
        self,
        element,
        region: ResolvedPosition,
        theme: ResolvedTheme,
        measurer: TextMeasurer,
    ) -> OverflowResult:
        """Try cascade: reduce font -> reflow -> split."""
        current_size = theme.get_font_size(element)

        # Step 1: Reduce font size iteratively
        while current_size > self.FONT_SIZE_FLOOR:
            bbox = measurer.measure_text(
                element.text, theme.get_font(element), current_size,
                max_width_inches=region.width,
            )
            if bbox.height_inches <= region.height:
                return OverflowResult(
                    action="font_reduced",
                    new_font_size=current_size,
                )
            current_size -= self.FONT_REDUCTION_STEP

        # Step 2: At minimum font size, check if it fits
        bbox = measurer.measure_text(
            element.text, theme.get_font(element), self.FONT_SIZE_FLOOR,
            max_width_inches=region.width,
        )
        if bbox.height_inches <= region.height:
            return OverflowResult(
                action="font_reduced",
                new_font_size=self.FONT_SIZE_FLOOR,
            )

        # Step 3: Split to multiple slides
        return OverflowResult(
            action="split",
            split_point=self._find_split_point(element, region, theme, measurer),
        )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Fixed slide templates | Constraint-based layout | 2020+ (CSS Grid/Flexbox influence) | Adaptive layouts that handle variable content |
| getsize() for text measurement | getbbox() + getlength() | Pillow 9.2 (2022) | getsize deprecated; getbbox provides precise bounding boxes |
| Approximate contrast checking | W3C G18 exact algorithm | WCAG 2.1 (2018) | Threshold changed from 0.03928 to 0.04045 for sRGB linearization |
| Single-level theme configs | 3-tier design tokens | 2023+ (materialui, figma tokens) | Semantic + component tokens enable theme switching without breakage |
| Template-per-slide-per-theme | Pattern-based layout + theme separation | Current best practice | N slide types x M themes = N patterns + M themes, not N*M templates |

**Deprecated/outdated:**
- `Pillow ImageFont.getsize()`: Deprecated since Pillow 9.2 (2022), removed in Pillow 10+. Use `getbbox()` or `getlength()` instead.
- WCAG sRGB threshold 0.03928: Changed to 0.04045 in May 2021. Negligible practical impact but use the correct value.

## Open Questions

1. **Font bundling strategy for 15 themes**
   - What we know: Docker image already has fonts-liberation and fonts-dejavu-core. Google Fonts (Montserrat, Open Sans, etc.) are free to bundle.
   - What's unclear: How many unique font families across 15 themes? Each TrueType family is 4 files (regular, bold, italic, bold-italic) at ~300KB each. 15 themes x 2 families = ~36MB of fonts.
   - Recommendation: Define a standard font set (6-8 families) shared across themes. Bundle all in Docker image. List available fonts in theme schema.

2. **EMU vs. inches as internal coordinate system**
   - What we know: python-pptx uses EMU internally (914400 per inch). The layout solver needs continuous values for constraints.
   - What's unclear: Should the solver work in inches and convert to EMU at render time, or work in EMU throughout?
   - Recommendation: **Work in inches throughout the layout engine.** Convert to EMU only at the rendering boundary (Phase 3). Inches are human-readable and match the slide dimensions (13.333" x 7.5"). pptx.util.Inches() handles conversion.

3. **How many layout patterns are needed for 32 slide types?**
   - What we know: Many slide types share structural patterns (e.g., "title + content area" covers bullets, chart, image, table).
   - What's unclear: Exact mapping of 32 types to reusable patterns.
   - Recommendation: Start with 6-8 base patterns covering the 23 universal slide types. Finance types (9) can extend these with specialized regions. Estimate: ~10-12 total patterns.

4. **Kiwisolver performance for interactive re-solve**
   - What we know: Kiwisolver is 10-500x faster than original Cassowary. The adaptive overflow loop may re-solve multiple times.
   - What's unclear: Is sub-millisecond solve realistic for a slide with ~15 constraints?
   - Recommendation: Profile early. A single slide should have 20-40 constraints. Cassowary solves this class of problem in microseconds. Performance is not a concern.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest >= 8.3 with pytest-asyncio |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/ -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LAYOUT-01 | Constraint solver produces valid positions on 12-col grid | unit | `pytest tests/unit/test_layout_solver.py -x` | Wave 0 |
| LAYOUT-02 | Text measurement returns accurate bounding boxes in inches | unit | `pytest tests/unit/test_text_measurer.py -x` | Wave 0 |
| LAYOUT-03 | Overflow cascade: font reduce -> reflow -> split | unit | `pytest tests/unit/test_overflow_handler.py -x` | Wave 0 |
| LAYOUT-04 | Visual hierarchy: title font > subtitle > body > footnote | unit | `pytest tests/unit/test_layout_patterns.py::test_visual_hierarchy -x` | Wave 0 |
| LAYOUT-05 | Spacing within +-2px tolerance, alignment snapped | unit | `pytest tests/unit/test_layout_solver.py::test_spacing_tolerance -x` | Wave 0 |
| LAYOUT-06 | Layout patterns produce valid positions per slide type | unit | `pytest tests/unit/test_layout_patterns.py -x` | Wave 0 |
| THEME-01 | Theme YAML loads and contains required sections | unit | `pytest tests/unit/test_theme_registry.py -x` | Wave 0 |
| THEME-02 | Variable references resolve to concrete values | unit | `pytest tests/unit/test_theme_resolver.py -x` | Wave 0 |
| THEME-03 | Brand kit overlay merges correctly with protected keys | unit | `pytest tests/unit/test_brand_kit_merger.py -x` | Wave 0 |
| THEME-04 | Slide masters define styles per slide type per theme | unit | `pytest tests/unit/test_theme_registry.py::test_slide_masters -x` | Wave 0 |
| THEME-05 | WCAG AA contrast validation catches failing pairs | unit | `pytest tests/unit/test_contrast.py -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/unit/ -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before /gsd:verify-work

### Wave 0 Gaps

- [ ] `tests/unit/test_layout_solver.py` -- covers LAYOUT-01, LAYOUT-05
- [ ] `tests/unit/test_text_measurer.py` -- covers LAYOUT-02
- [ ] `tests/unit/test_overflow_handler.py` -- covers LAYOUT-03
- [ ] `tests/unit/test_layout_patterns.py` -- covers LAYOUT-04, LAYOUT-06
- [ ] `tests/unit/test_theme_registry.py` -- covers THEME-01, THEME-04
- [ ] `tests/unit/test_theme_resolver.py` -- covers THEME-02
- [ ] `tests/unit/test_brand_kit_merger.py` -- covers THEME-03
- [ ] `tests/unit/test_contrast.py` -- covers THEME-05
- [ ] `tests/conftest.py` updates -- shared fixtures for fonts, theme data, grid system
- [ ] Font files for testing -- at least one .ttf bundled in tests/fixtures/fonts/

## Sources

### Primary (HIGH confidence)

- [kiwisolver GitHub (nucleic/kiwi)](https://github.com/nucleic/kiwi) - Python API from test files: Variable, Solver, Constraint, strengths
- [kiwisolver PyPI](https://pypi.org/project/kiwisolver/) - v1.4.8, March 2026
- [kiwisolver API docs](https://kiwisolver.readthedocs.io/en/latest/api/python.html) - Solver, Variable, Constraint API
- [kiwisolver basic systems](https://kiwisolver.readthedocs.io/en/latest/basis/basic_systems.html) - Constraint definition tutorial
- [Pillow ImageFont docs](https://pillow.readthedocs.io/en/stable/reference/ImageFont.html) - getbbox, getlength, truetype API
- [W3C WCAG 2.1 Technique G18](https://www.w3.org/WAI/WCAG21/Techniques/general/G18) - Exact luminance and contrast ratio algorithm
- [W3C WCAG 2.1 SC 1.4.3](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html) - 4.5:1 normal text, 3:1 large text thresholds
- [python-pptx util module](https://python-pptx.readthedocs.io/en/latest/api/util.html) - EMU conversion: 914400/inch, 12700/point
- [enaml layout_manager.py](https://github.com/nucleic/enaml/blob/main/enaml/layout/layout_manager.py) - Constraint layout architecture pattern
- [enaml grid_helper.py](https://github.com/nucleic/enaml/blob/main/enaml/layout/grid_helper.py) - Grid-based constraint generation pattern

### Secondary (MEDIUM confidence)

- [wcag-contrast-ratio PyPI](https://pypi.org/project/wcag-contrast-ratio/) - v0.9, MIT license, contrast.rgb() API
- [Design Tokens & Theming (materialui.co)](https://materialui.co/blog/design-tokens-and-theming-scalable-ui-2025) - 3-tier token pattern: reference, semantic, component
- [deepmerge PyPI](https://pypi.org/project/deepmerge/) - Deep dict merge strategies (considered, not recommended)
- [Pillow Issue #6079](https://github.com/python-pillow/Pillow/issues/6079) - truetype size is in points, not pixels
- [Pillow Discussion #6891](https://github.com/python-pillow/Pillow/discussions/6891) - Text resizing and measurement patterns

### Tertiary (LOW confidence)

- [Cassowary Wikipedia](https://en.wikipedia.org/wiki/Cassowary_(software)) - Historical context on Cassowary algorithm
- [kiwisolver examples (clouddefense.ai)](https://www.clouddefense.ai/code/python/example/kiwisolver) - Community code examples

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - kiwisolver, Pillow, PyYAML are all verified, versioned, and already in project deps
- Architecture: MEDIUM-HIGH - Pattern-based constraint layout is well-reasoned from enaml precedent but novel for slide domain
- Pitfalls: HIGH - Text measurement, font metrics, contrast calculation are well-documented domains with known gotchas
- Layout patterns: MEDIUM - The specific constraint sets per slide type need prototyping to validate. Research provides the framework but not the exact constraints.
- Theme YAML structure: MEDIUM - Design token pattern is proven in web/design tooling but DeckForge's specific structure needs validation

**Research date:** 2026-03-26
**Valid until:** 2026-04-26 (stable domain, libraries not fast-moving)
