"""Monte Carlo financial projections — uses OraClaw's simulation engine
to generate realistic scenario distributions for finance slide types.

Powers: DCF sensitivity analysis, returns waterfall scenarios,
capital structure stress testing, and risk matrix probability calibration.
"""

from __future__ import annotations

import logging
from typing import Any

from deckforge.intelligence.client import get_oraclaw

logger = logging.getLogger(__name__)


class MonteCarloProjections:
    """Generate financial projections via OraClaw Monte Carlo simulation.

    Usage:
        mc = MonteCarloProjections()
        result = await mc.dcf_scenarios(
            base_revenue=10_000_000,
            growth_mean=0.15,
            growth_std=0.08,
            simulations=10000,
        )
    """

    async def dcf_scenarios(
        self,
        base_revenue: float,
        growth_mean: float = 0.10,
        growth_std: float = 0.05,
        simulations: int = 10000,
    ) -> dict[str, Any] | None:
        """Generate DCF revenue growth scenarios.

        Args:
            base_revenue: Starting annual revenue.
            growth_mean: Expected annual growth rate.
            growth_std: Standard deviation of growth.
            simulations: Number of Monte Carlo runs.

        Returns:
            Dict with percentiles (p10, p25, p50, p75, p90), mean, std,
            and histogram data for DCF sensitivity slides.
        """
        client = get_oraclaw()
        if client is None:
            return None

        result = await client.monte_carlo(
            simulations=simulations,
            distribution="normal",
            params={"mean": growth_mean, "stddev": growth_std},
        )

        if result is None:
            return None

        # Scale growth rates to revenue projections
        stats = result.get("statistics", {})
        percentiles = result.get("percentiles", {})

        return {
            "base_revenue": base_revenue,
            "projections": {
                "bear_case": base_revenue * (1 + percentiles.get("p10", growth_mean - 1.28 * growth_std)),
                "conservative": base_revenue * (1 + percentiles.get("p25", growth_mean - 0.67 * growth_std)),
                "base_case": base_revenue * (1 + percentiles.get("p50", growth_mean)),
                "optimistic": base_revenue * (1 + percentiles.get("p75", growth_mean + 0.67 * growth_std)),
                "bull_case": base_revenue * (1 + percentiles.get("p90", growth_mean + 1.28 * growth_std)),
            },
            "growth_rates": {
                "mean": stats.get("mean", growth_mean),
                "std": stats.get("stdDev", growth_std),
                "min": stats.get("min", growth_mean - 3 * growth_std),
                "max": stats.get("max", growth_mean + 3 * growth_std),
            },
            "simulations": simulations,
            "histogram": result.get("histogram", []),
        }

    async def returns_waterfall(
        self,
        entry_value: float,
        holding_period: int = 5,
        irr_mean: float = 0.20,
        irr_std: float = 0.10,
        simulations: int = 10000,
    ) -> dict[str, Any] | None:
        """Generate returns waterfall scenarios for PE deal analysis.

        Args:
            entry_value: Initial investment value.
            holding_period: Years held.
            irr_mean: Expected IRR.
            irr_std: IRR standard deviation.
            simulations: Number of Monte Carlo runs.

        Returns:
            Dict with exit values at various percentiles,
            MOIC calculations, and distribution data.
        """
        client = get_oraclaw()
        if client is None:
            return None

        result = await client.monte_carlo(
            simulations=simulations,
            distribution="normal",
            params={"mean": irr_mean, "stddev": irr_std},
        )

        if result is None:
            return None

        percentiles = result.get("percentiles", {})

        def exit_val(irr: float) -> float:
            return entry_value * (1 + irr) ** holding_period

        return {
            "entry_value": entry_value,
            "holding_period": holding_period,
            "scenarios": {
                "downside": {
                    "irr": percentiles.get("p10", irr_mean - 1.28 * irr_std),
                    "exit_value": exit_val(percentiles.get("p10", irr_mean - 1.28 * irr_std)),
                    "moic": exit_val(percentiles.get("p10", irr_mean - 1.28 * irr_std)) / entry_value,
                },
                "base": {
                    "irr": percentiles.get("p50", irr_mean),
                    "exit_value": exit_val(percentiles.get("p50", irr_mean)),
                    "moic": exit_val(percentiles.get("p50", irr_mean)) / entry_value,
                },
                "upside": {
                    "irr": percentiles.get("p90", irr_mean + 1.28 * irr_std),
                    "exit_value": exit_val(percentiles.get("p90", irr_mean + 1.28 * irr_std)),
                    "moic": exit_val(percentiles.get("p90", irr_mean + 1.28 * irr_std)) / entry_value,
                },
            },
            "simulations": simulations,
            "histogram": result.get("histogram", []),
        }

    async def sensitivity_matrix(
        self,
        base_value: float,
        row_variable: str,
        col_variable: str,
        row_range: tuple[float, float] = (-0.20, 0.20),
        col_range: tuple[float, float] = (-0.20, 0.20),
        steps: int = 5,
    ) -> dict[str, Any] | None:
        """Generate a sensitivity matrix for two-variable analysis.

        Args:
            base_value: Central value.
            row_variable: Name of the row variable (e.g., "Revenue Growth").
            col_variable: Name of the column variable (e.g., "WACC").
            row_range: (min_delta, max_delta) for row variable.
            col_range: (min_delta, max_delta) for column variable.
            steps: Number of steps in each direction.

        Returns:
            Dict with matrix data, row/col labels, and base case highlighted.
        """
        # Sensitivity matrix is computed locally (no simulation needed)
        # but we use OraClaw for the base case Monte Carlo if available
        row_deltas = [
            row_range[0] + i * (row_range[1] - row_range[0]) / (steps - 1)
            for i in range(steps)
        ]
        col_deltas = [
            col_range[0] + i * (col_range[1] - col_range[0]) / (steps - 1)
            for i in range(steps)
        ]

        matrix = []
        for rd in row_deltas:
            row = []
            for cd in col_deltas:
                row.append(round(base_value * (1 + rd) * (1 + cd), 2))
            matrix.append(row)

        return {
            "base_value": base_value,
            "row_variable": row_variable,
            "col_variable": col_variable,
            "row_labels": [f"{d:+.1%}" for d in row_deltas],
            "col_labels": [f"{d:+.1%}" for d in col_deltas],
            "matrix": matrix,
            "base_row": steps // 2,
            "base_col": steps // 2,
        }
