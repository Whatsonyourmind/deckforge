"""OraClaw API client — async HTTP client for the intelligence backend.

All methods return None on failure so callers can gracefully fall back
to non-intelligent defaults. This is intentional: DeckForge must render
presentations even when OraClaw is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(10.0, connect=5.0)


class OraClaw:
    """Async client for OraClaw's public API endpoints.

    Args:
        base_url: OraClaw API base URL (e.g., https://oraclaw-api.onrender.com).
        api_key: Optional API key for authenticated endpoints.
    """

    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=_TIMEOUT,
        )

    async def bandit_select(
        self,
        arms: list[dict[str, Any]],
        algorithm: str = "ucb1",
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Select the best arm using Multi-Armed Bandit.

        Args:
            arms: List of {"id": str, "name": str, "pulls": int, "totalReward": float}.
            algorithm: "ucb1", "thompson", or "epsilon-greedy".
            config: Optional {"explorationConstant": float, "rewardDecay": float}.

        Returns:
            Selection result with "selected", "score", "algorithm" or None on failure.
        """
        payload: dict[str, Any] = {"arms": arms, "algorithm": algorithm}
        if config:
            payload["config"] = config
        return await self._post("/api/v1/optimize/bandit", payload)

    async def contextual_bandit_select(
        self,
        arms: list[dict[str, str]],
        context: list[float],
        history: list[dict[str, Any]] | None = None,
        alpha: float = 1.0,
    ) -> dict[str, Any] | None:
        """Select the best arm using Contextual Bandit (LinUCB).

        Args:
            arms: List of {"id": str, "name": str}.
            context: Feature vector (e.g., [audience_type, formality, industry]).
            history: Optional past rewards for learning.
            alpha: Exploration parameter.

        Returns:
            Selection with "selected", "expectedReward", "confidenceWidth" or None.
        """
        payload: dict[str, Any] = {
            "arms": arms,
            "context": context,
            "alpha": alpha,
        }
        if history:
            payload["history"] = history
        return await self._post("/api/v1/optimize/contextual-bandit", payload)

    async def convergence_score(
        self,
        sources: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Compute convergence score across multiple sources.

        Args:
            sources: List of {"id": str, "name": str, "probability": float,
                     "confidence": float, "volume": int}.
            config: Optional weights and thresholds.

        Returns:
            Convergence result with ICM score, agreement metrics, or None.
        """
        payload: dict[str, Any] = {"sources": sources}
        if config:
            payload["config"] = config
        return await self._post("/api/v1/score/convergence", payload)

    async def monte_carlo(
        self,
        simulations: int,
        distribution: str,
        params: dict[str, float],
        iterations: int | None = None,
    ) -> dict[str, Any] | None:
        """Run Monte Carlo simulation.

        Args:
            simulations: Number of simulation runs.
            distribution: "normal", "lognormal", "uniform", "triangular", "beta".
            params: Distribution parameters (mean, stddev, min, max, etc.).
            iterations: Optional number of iterations per simulation.

        Returns:
            Simulation results with statistics, percentiles, histogram, or None.
        """
        payload: dict[str, Any] = {
            "simulations": simulations,
            "distribution": distribution,
            "params": params,
        }
        if iterations:
            payload["iterations"] = iterations
        return await self._post("/api/v1/simulate/montecarlo", payload)

    async def evolve(
        self,
        candidates: list[dict[str, Any]],
        objectives: list[dict[str, Any]],
        config: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Run genetic algorithm optimization.

        Args:
            candidates: Initial population.
            objectives: Optimization objectives.
            config: GA parameters (generations, mutation_rate, etc.).

        Returns:
            Optimized solutions with Pareto frontier, or None.
        """
        payload: dict[str, Any] = {
            "candidates": candidates,
            "objectives": objectives,
        }
        if config:
            payload["config"] = config
        return await self._post("/api/v1/optimize/evolve", payload)

    async def health(self) -> bool:
        """Check if OraClaw API is reachable."""
        try:
            resp = await self._client.get("/api/v1/health")
            return resp.status_code == 200
        except Exception:
            return False

    async def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        """POST to OraClaw with error handling. Returns None on any failure."""
        try:
            resp = await self._client.post(path, json=payload)
            if resp.status_code == 200:
                return resp.json()
            logger.warning(
                "OraClaw %s returned %d: %s",
                path, resp.status_code, resp.text[:200],
            )
            return None
        except httpx.TimeoutException:
            logger.warning("OraClaw %s timed out", path)
            return None
        except Exception:
            logger.warning("OraClaw %s unreachable", path, exc_info=True)
            return None

    async def close(self) -> None:
        await self._client.aclose()


def _create_oraclaw() -> OraClaw | None:
    """Create an OraClaw client from settings, or None if disabled."""
    from deckforge.config import settings

    if not settings.ORACLAW_ENABLED or not settings.ORACLAW_BASE_URL:
        return None
    return OraClaw(
        base_url=settings.ORACLAW_BASE_URL,
        api_key=settings.ORACLAW_API_KEY,
    )


# Lazy singleton — None when OraClaw is disabled
oraclaw: OraClaw | None = None


def get_oraclaw() -> OraClaw | None:
    """Get or create the OraClaw singleton."""
    global oraclaw
    if oraclaw is None:
        oraclaw = _create_oraclaw()
    return oraclaw
