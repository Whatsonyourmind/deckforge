"""Cost estimation endpoint.

POST /v1/estimate returns the credit cost for a given IR payload or prompt.
"""

from __future__ import annotations

import logging
import math

from fastapi import APIRouter, HTTPException, status

from deckforge.api.schemas.deck_schemas import CostEstimateRequest, CostEstimateResponse
from deckforge.services.cost_estimator import CostEstimator

logger = logging.getLogger(__name__)

router = APIRouter(tags=["estimate"])

estimator = CostEstimator()

# Default slide count assumption for prompt-based estimation
DEFAULT_PROMPT_SLIDE_COUNT = 10


@router.post("/estimate", response_model=CostEstimateResponse)
async def estimate_cost(body: CostEstimateRequest) -> CostEstimateResponse:
    """Estimate the credit cost for rendering a presentation.

    Accepts either:
    - ``ir``: A full Presentation IR dict for exact estimation.
    - ``prompt``: A natural language prompt for rough estimation
      (assumes default slide count with NL generation surcharge).
    - If neither is provided, returns 422.
    """
    if body.ir is not None:
        # Exact estimation from IR
        result = estimator.estimate_from_ir(body.ir)
        return CostEstimateResponse(
            base_credits=result.base_credits,
            surcharges=result.surcharges,
            total_credits=result.total_credits,
            breakdown=result.breakdown,
        )
    elif body.prompt is not None:
        # Rough estimation from prompt (assume default slide count + NL surcharge)
        pseudo_ir: dict = {
            "schema_version": "1.0",
            "metadata": {"title": "Estimated"},
            "theme": "executive-dark",
            "slides": [
                {"slide_type": "title_slide", "elements": []}
                for _ in range(DEFAULT_PROMPT_SLIDE_COUNT)
            ],
            "generation_options": {"quality_target": "standard", "tone": "formal"},
        }
        result = estimator.estimate_from_ir(pseudo_ir)
        return CostEstimateResponse(
            base_credits=result.base_credits,
            surcharges=result.surcharges,
            total_credits=result.total_credits,
            breakdown=f"Estimated from prompt ({DEFAULT_PROMPT_SLIDE_COUNT} slides assumed); "
            + result.breakdown,
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide either 'ir' or 'prompt' for cost estimation.",
        )
