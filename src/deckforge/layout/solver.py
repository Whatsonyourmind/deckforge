"""Kiwisolver constraint solver wrapper for slide layout."""

from __future__ import annotations

import logging
from typing import Any

import kiwisolver

from deckforge.layout.types import LayoutRegion, ResolvedPosition

logger = logging.getLogger(__name__)


class SlideLayoutSolver:
    """Wraps kiwisolver.Solver to manage layout constraints and variable solving.

    Usage:
        solver = SlideLayoutSolver()
        title = LayoutRegion("title")
        solver.add_constraint(title.left == 0.5)
        solver.add_constraint(title.width == 12.0)
        result = solver.solve([title])
        # result["title"] -> ResolvedPosition(x=0.5, ...)
    """

    def __init__(self) -> None:
        self._solver = kiwisolver.Solver()
        self._constraints: list[Any] = []
        self._infeasible = False

    def add_constraint(self, constraint: Any) -> None:
        """Add a single constraint to the solver.

        Args:
            constraint: A kiwisolver constraint (e.g., region.left == 0.5).
        """
        try:
            self._solver.addConstraint(constraint)
        except kiwisolver.UnsatisfiableConstraint as e:
            logger.warning("Unsatisfiable constraint on add: %s", e)
            self._infeasible = True
        self._constraints.append(constraint)

    def add_constraints(self, constraints: list[Any]) -> None:
        """Add multiple constraints at once.

        Args:
            constraints: List of kiwisolver constraints.
        """
        for constraint in constraints:
            self.add_constraint(constraint)

    def solve(self, regions: list[LayoutRegion]) -> dict[str, ResolvedPosition] | None:
        """Solve all constraints and return resolved positions.

        Args:
            regions: List of LayoutRegion instances whose variables are constrained.

        Returns:
            Dictionary mapping region name to ResolvedPosition, or None if
            constraints are unsatisfiable.
        """
        if self._infeasible:
            return None

        try:
            self._solver.updateVariables()
        except kiwisolver.UnsatisfiableConstraint as e:
            logger.warning("Unsatisfiable constraint: %s", e)
            return None

        result: dict[str, ResolvedPosition] = {}
        for region in regions:
            result[region.name] = ResolvedPosition(
                x=region.left.value(),
                y=region.top.value(),
                width=region.width.value(),
                height=region.height.value(),
            )
        return result

    def reset(self) -> None:
        """Reset the solver, clearing all constraints for reuse."""
        self._solver = kiwisolver.Solver()
        self._constraints.clear()
        self._infeasible = False
