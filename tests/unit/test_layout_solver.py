"""Tests for LayoutRegion and SlideLayoutSolver: kiwisolver constraint wrapper."""

from __future__ import annotations

import kiwisolver
import pytest


class TestLayoutRegion:
    """LayoutRegion wraps kiwisolver Variables with derived properties."""

    def test_creates_kiwisolver_variables(self):
        from deckforge.layout.types import LayoutRegion

        region = LayoutRegion("title")
        assert isinstance(region.left, kiwisolver.Variable)
        assert isinstance(region.top, kiwisolver.Variable)
        assert isinstance(region.width, kiwisolver.Variable)
        assert isinstance(region.height, kiwisolver.Variable)

    def test_variable_names_include_region_name(self):
        from deckforge.layout.types import LayoutRegion

        region = LayoutRegion("header")
        assert "header" in str(region.left)
        assert "header" in str(region.top)

    def test_right_expression(self):
        """right should be left + width (kiwisolver expression)."""
        from deckforge.layout.types import LayoutRegion

        region = LayoutRegion("title")
        right_expr = region.right
        # It should be an expression, not a plain variable
        assert right_expr is not None

    def test_bottom_expression(self):
        """bottom should be top + height (kiwisolver expression)."""
        from deckforge.layout.types import LayoutRegion

        region = LayoutRegion("title")
        bottom_expr = region.bottom
        assert bottom_expr is not None


class TestResolvedPosition:
    """ResolvedPosition alignment checking."""

    def test_is_aligned_to_same_left(self):
        from deckforge.layout.types import ResolvedPosition

        pos1 = ResolvedPosition(x=0.5, y=1.0, width=5.0, height=1.5)
        pos2 = ResolvedPosition(x=0.5, y=3.0, width=5.0, height=2.0)
        assert pos1.is_aligned_to(pos2, "left")

    def test_is_aligned_to_same_top(self):
        from deckforge.layout.types import ResolvedPosition

        pos1 = ResolvedPosition(x=0.5, y=1.0, width=5.0, height=1.5)
        pos2 = ResolvedPosition(x=3.0, y=1.0, width=4.0, height=1.5)
        assert pos1.is_aligned_to(pos2, "top")

    def test_is_not_aligned_beyond_tolerance(self):
        from deckforge.layout.types import ResolvedPosition

        pos1 = ResolvedPosition(x=0.5, y=1.0, width=5.0, height=1.5)
        # 2px at 72 DPI = 0.0278in; use 0.05in which is beyond tolerance
        pos2 = ResolvedPosition(x=0.55, y=1.0, width=5.0, height=1.5)
        assert not pos1.is_aligned_to(pos2, "left")

    def test_is_aligned_within_tolerance(self):
        from deckforge.layout.types import ResolvedPosition

        pos1 = ResolvedPosition(x=0.5, y=1.0, width=5.0, height=1.5)
        # 0.02in is within 0.0278in tolerance
        pos2 = ResolvedPosition(x=0.52, y=1.0, width=5.0, height=1.5)
        assert pos1.is_aligned_to(pos2, "left")

    def test_is_aligned_right_edge(self):
        from deckforge.layout.types import ResolvedPosition

        pos1 = ResolvedPosition(x=0.5, y=1.0, width=5.0, height=1.5)
        pos2 = ResolvedPosition(x=0.5, y=3.0, width=5.0, height=2.0)
        # right = x + width = 5.5 for both
        assert pos1.is_aligned_to(pos2, "right")

    def test_is_aligned_bottom_edge(self):
        from deckforge.layout.types import ResolvedPosition

        pos1 = ResolvedPosition(x=0.5, y=1.0, width=5.0, height=1.5)
        pos2 = ResolvedPosition(x=3.0, y=1.0, width=4.0, height=1.5)
        # bottom = y + height = 2.5 for both
        assert pos1.is_aligned_to(pos2, "bottom")

    def test_custom_tolerance(self):
        from deckforge.layout.types import ResolvedPosition

        pos1 = ResolvedPosition(x=0.5, y=1.0, width=5.0, height=1.5)
        pos2 = ResolvedPosition(x=0.55, y=1.0, width=5.0, height=1.5)
        # 0.05in difference, with 0.1in tolerance -> aligned
        assert pos1.is_aligned_to(pos2, "left", tolerance_inches=0.1)


class TestBoundingBox:
    """BoundingBox data class."""

    def test_basic_creation(self):
        from deckforge.layout.types import BoundingBox

        bb = BoundingBox(width_inches=5.0, height_inches=1.5)
        assert bb.width_inches == pytest.approx(5.0)
        assert bb.height_inches == pytest.approx(1.5)

    def test_min_height_optional(self):
        from deckforge.layout.types import BoundingBox

        bb = BoundingBox(width_inches=5.0, height_inches=1.5)
        assert bb.min_height is None

        bb2 = BoundingBox(width_inches=5.0, height_inches=1.5, min_height=0.5)
        assert bb2.min_height == pytest.approx(0.5)


class TestSlideLayoutSolver:
    """SlideLayoutSolver constraint solving."""

    def test_add_and_solve_basic_constraints(self):
        from deckforge.layout.solver import SlideLayoutSolver
        from deckforge.layout.types import LayoutRegion

        solver = SlideLayoutSolver()
        title = LayoutRegion("title")

        # Set title position with constraints
        solver.add_constraint(title.left == 0.5)
        solver.add_constraint(title.top == 0.5)
        solver.add_constraint(title.width == 12.0)
        solver.add_constraint(title.height == 1.5)

        result = solver.solve([title])
        assert result is not None
        assert "title" in result
        assert result["title"].x == pytest.approx(0.5)
        assert result["title"].y == pytest.approx(0.5)
        assert result["title"].width == pytest.approx(12.0)
        assert result["title"].height == pytest.approx(1.5)

    def test_solve_multiple_regions(self):
        from deckforge.layout.solver import SlideLayoutSolver
        from deckforge.layout.types import LayoutRegion

        solver = SlideLayoutSolver()
        title = LayoutRegion("title")
        body = LayoutRegion("body")

        solver.add_constraint(title.left == 0.5)
        solver.add_constraint(title.top == 0.5)
        solver.add_constraint(title.width == 12.0)
        solver.add_constraint(title.height == 1.5)

        # Body starts below title
        solver.add_constraint(body.left == title.left)
        solver.add_constraint(body.top == title.bottom + 0.25)
        solver.add_constraint(body.width == title.width)
        solver.add_constraint(body.height == 4.0)

        result = solver.solve([title, body])
        assert result is not None
        assert result["body"].y == pytest.approx(2.25)  # 0.5 + 1.5 + 0.25
        assert result["body"].x == pytest.approx(0.5)

    def test_unsatisfiable_returns_none(self):
        """Contradictory constraints should return None, not raise."""
        from deckforge.layout.solver import SlideLayoutSolver
        from deckforge.layout.types import LayoutRegion

        solver = SlideLayoutSolver()
        region = LayoutRegion("conflict")

        solver.add_constraint(region.width == 5.0)
        solver.add_constraint(region.width == 10.0)

        result = solver.solve([region])
        assert result is None

    def test_add_constraints_batch(self):
        from deckforge.layout.solver import SlideLayoutSolver
        from deckforge.layout.types import LayoutRegion

        solver = SlideLayoutSolver()
        title = LayoutRegion("title")

        constraints = [
            title.left == 0.5,
            title.top == 0.5,
            title.width == 12.0,
            title.height == 1.5,
        ]
        solver.add_constraints(constraints)

        result = solver.solve([title])
        assert result is not None
        assert result["title"].width == pytest.approx(12.0)

    def test_reset_clears_solver(self):
        from deckforge.layout.solver import SlideLayoutSolver
        from deckforge.layout.types import LayoutRegion

        solver = SlideLayoutSolver()
        title = LayoutRegion("title")
        solver.add_constraint(title.left == 0.5)
        solver.add_constraint(title.top == 0.5)
        solver.add_constraint(title.width == 12.0)
        solver.add_constraint(title.height == 1.5)

        result1 = solver.solve([title])
        assert result1 is not None

        solver.reset()

        # After reset, solving with new regions should work
        new_region = LayoutRegion("new")
        solver.add_constraint(new_region.left == 1.0)
        solver.add_constraint(new_region.top == 1.0)
        solver.add_constraint(new_region.width == 5.0)
        solver.add_constraint(new_region.height == 3.0)

        result2 = solver.solve([new_region])
        assert result2 is not None
        assert result2["new"].x == pytest.approx(1.0)
