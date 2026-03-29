"""12-column grid system for 16:9 presentation slides."""

from __future__ import annotations


class GridSystem:
    """12-column grid system for computing slide layout geometry.

    Default dimensions target the standard 16:9 widescreen slide format
    (13.333in x 7.5in at 96 DPI = 1280x720px).

    Attributes:
        SLIDE_WIDTH_INCHES: Total slide width (13.333in for 16:9).
        SLIDE_HEIGHT_INCHES: Total slide height (7.5in for 16:9).
        NUM_COLUMNS: Number of grid columns (always 12).
    """

    SLIDE_WIDTH_INCHES: float = 13.333
    SLIDE_HEIGHT_INCHES: float = 7.5
    NUM_COLUMNS: int = 12

    def __init__(
        self,
        *,
        margin_left: float = 0.5,
        margin_right: float = 0.5,
        margin_top: float = 0.5,
        margin_bottom: float = 0.5,
        gutter: float = 0.167,
        theme_spacing: dict[str, float] | None = None,
    ) -> None:
        """Initialize grid system with margins and gutter.

        Args:
            margin_left: Left margin in inches.
            margin_right: Right margin in inches.
            margin_top: Top margin in inches.
            margin_bottom: Bottom margin in inches.
            gutter: Space between columns in inches.
            theme_spacing: Optional dict to override margins/gutter from theme data.
                Supported keys: margin_left, margin_right, margin_top, margin_bottom, gutter.
        """
        # Apply theme overrides if provided
        if theme_spacing:
            margin_left = theme_spacing.get("margin_left", margin_left)
            margin_right = theme_spacing.get("margin_right", margin_right)
            margin_top = theme_spacing.get("margin_top", margin_top)
            margin_bottom = theme_spacing.get("margin_bottom", margin_bottom)
            gutter = theme_spacing.get("gutter", gutter)

        self.margin_left = margin_left
        self.margin_right = margin_right
        self.margin_top = margin_top
        self.margin_bottom = margin_bottom
        self.gutter = gutter

        # Computed geometry
        self.content_left = margin_left
        self.content_top = margin_top
        self.content_width = self.SLIDE_WIDTH_INCHES - margin_left - margin_right
        self.content_height = self.SLIDE_HEIGHT_INCHES - margin_top - margin_bottom
        self.content_right = self.content_left + self.content_width
        self.content_bottom = self.content_top + self.content_height

        # Column width = (content_width - (NUM_COLUMNS - 1) * gutter) / NUM_COLUMNS
        total_gutter_space = (self.NUM_COLUMNS - 1) * self.gutter
        self.column_width = (self.content_width - total_gutter_space) / self.NUM_COLUMNS

    def column_left(self, col: int) -> float:
        """Get the left edge position of a 0-indexed column.

        Args:
            col: Column index (0-11).

        Returns:
            Left edge position in inches from slide left.
        """
        if col < 0 or col >= self.NUM_COLUMNS:
            raise ValueError(f"Column index {col} out of range [0, {self.NUM_COLUMNS - 1}]")
        return self.content_left + col * (self.column_width + self.gutter)

    def column_span_width(self, start_col: int, span: int) -> float:
        """Get the total width of a column span including internal gutters.

        Args:
            start_col: Starting column index (0-indexed).
            span: Number of columns to span.

        Returns:
            Total width in inches including internal gutters.
        """
        if span < 1:
            raise ValueError(f"Span must be >= 1, got {span}")
        if start_col < 0 or start_col + span > self.NUM_COLUMNS:
            raise ValueError(
                f"Column span [{start_col}, {start_col + span}) "
                f"out of range [0, {self.NUM_COLUMNS})"
            )
        # Width = span columns + (span - 1) internal gutters
        return span * self.column_width + (span - 1) * self.gutter
