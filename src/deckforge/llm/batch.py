"""Anthropic Batch API client for bulk LLM jobs.

Provides a thin async wrapper around Anthropic's Message Batches API
(``/v1/messages/batches``). Batch jobs receive a 50% discount on both input
and output tokens, making them ideal for:

* Overnight bulk deck generation (e.g., 100+ pitch decks for a PE fund)
* Report batches (weekly research refresh, portfolio updates)
* Fine-tuning data generation
* Any workload that tolerates up to 24h turnaround

Usage
-----
    from deckforge.llm.batch import BatchLLMJob, BatchStatus
    from deckforge.config import settings

    job = BatchLLMJob(api_key=settings.ANTHROPIC_API_KEY)

    batch_id = await job.submit([
        {
            "custom_id": "deck-001",
            "params": {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": "Build deck..."}],
            },
        },
        ...
    ])

    status = await job.poll(batch_id)
    if status.is_complete:
        async for result in job.fetch_results(batch_id):
            handle(result)

See https://docs.anthropic.com/en/docs/build-with-claude/batch-processing
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator, Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Any

import anthropic

logger = logging.getLogger(__name__)


class BatchState(str, Enum):
    """Coarse-grained lifecycle state for an Anthropic batch job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"
    CANCELED = "canceled"
    EXPIRED = "expired"


# Map Anthropic's processing_status values to our simplified BatchState.
_STATUS_MAP: dict[str, BatchState] = {
    "in_progress": BatchState.PROCESSING,
    "canceling": BatchState.PROCESSING,
    "ended": BatchState.COMPLETE,
}


@dataclass(frozen=True)
class BatchStatus:
    """Snapshot of a batch job's progress."""

    batch_id: str
    state: BatchState
    processing_status: str
    succeeded: int = 0
    errored: int = 0
    canceled: int = 0
    expired: int = 0
    total: int = 0

    @property
    def is_complete(self) -> bool:
        """True if the batch has ended (results are ready to fetch)."""
        return self.state == BatchState.COMPLETE

    @property
    def is_terminal(self) -> bool:
        """True if no more progress will happen (complete, failed, expired)."""
        return self.state in {
            BatchState.COMPLETE,
            BatchState.FAILED,
            BatchState.CANCELED,
            BatchState.EXPIRED,
        }


@dataclass(frozen=True)
class BatchResult:
    """A single message result from a completed batch."""

    custom_id: str
    result_type: str  # "succeeded" | "errored" | "canceled" | "expired"
    message: Any | None = None  # Anthropic Message on success
    error: dict[str, Any] | None = None  # error payload on failure


class BatchLLMJob:
    """Async client for Anthropic's Message Batches API.

    Batch jobs save 50% on token costs compared to synchronous calls, at the
    price of up to 24-hour turnaround. Use for offline workflows only.

    Parameters
    ----------
    api_key:
        Anthropic API key. Pulled from settings.ANTHROPIC_API_KEY by callers.
    client:
        Optional pre-built ``anthropic.AsyncAnthropic`` instance (for tests).
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        client: anthropic.AsyncAnthropic | None = None,
    ) -> None:
        if client is not None:
            self._client = client
        else:
            if not api_key:
                raise ValueError("BatchLLMJob requires an api_key or a client")
            self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def submit(self, requests: Iterable[dict[str, Any]]) -> str:
        """Submit a batch of message requests and return the batch id.

        Each request dict must have:
          * ``custom_id``: caller-supplied identifier (unique within the batch)
          * ``params``: an Anthropic messages.create() parameter dict
                       (model, max_tokens, messages, and optional system blocks)

        Static system blocks in ``params`` may carry ``cache_control`` markers;
        caching is applied per-request within the batch.

        Returns
        -------
        The batch id (e.g. ``msgbatch_01Abc...``) — pass to ``poll`` and
        ``fetch_results``.
        """
        request_list = list(requests)
        if not request_list:
            raise ValueError("submit() requires at least one request")

        for i, req in enumerate(request_list):
            if "custom_id" not in req:
                raise ValueError(f"request[{i}] missing 'custom_id'")
            if "params" not in req:
                raise ValueError(f"request[{i}] missing 'params'")

        logger.info(
            "Submitting Anthropic batch with %d requests (50%% discount)",
            len(request_list),
        )
        batch = await self._client.messages.batches.create(requests=request_list)
        logger.info("Batch submitted: id=%s", batch.id)
        return batch.id

    async def poll(self, batch_id: str) -> BatchStatus:
        """Retrieve the current status of a batch job.

        Returns a ``BatchStatus`` snapshot. Callers should re-poll until
        ``status.is_terminal`` before fetching results.
        """
        batch = await self._client.messages.batches.retrieve(batch_id)
        processing_status = getattr(batch, "processing_status", "unknown")
        state = _STATUS_MAP.get(processing_status, BatchState.PENDING)

        counts = getattr(batch, "request_counts", None)
        succeeded = getattr(counts, "succeeded", 0) if counts else 0
        errored = getattr(counts, "errored", 0) if counts else 0
        canceled = getattr(counts, "canceled", 0) if counts else 0
        expired = getattr(counts, "expired", 0) if counts else 0
        processing = getattr(counts, "processing", 0) if counts else 0
        total = succeeded + errored + canceled + expired + processing

        return BatchStatus(
            batch_id=batch_id,
            state=state,
            processing_status=processing_status,
            succeeded=succeeded,
            errored=errored,
            canceled=canceled,
            expired=expired,
            total=total,
        )

    async def fetch_results(self, batch_id: str) -> AsyncIterator[BatchResult]:
        """Stream results from a completed batch job.

        Yields one ``BatchResult`` per request in the batch. Call only after
        ``poll(batch_id).is_complete`` is True — otherwise Anthropic will
        return a 404 / not-yet-ready error.
        """
        results = await self._client.messages.batches.results(batch_id)
        async for entry in results:
            custom_id = getattr(entry, "custom_id", "")
            result = getattr(entry, "result", None)
            result_type = getattr(result, "type", "unknown") if result else "unknown"
            message = getattr(result, "message", None) if result else None
            error = getattr(result, "error", None) if result else None
            yield BatchResult(
                custom_id=custom_id,
                result_type=result_type,
                message=message,
                error=error if isinstance(error, dict) else None,
            )

    async def cancel(self, batch_id: str) -> BatchStatus:
        """Cancel an in-flight batch job. Returns the updated status."""
        await self._client.messages.batches.cancel(batch_id)
        return await self.poll(batch_id)


__all__ = [
    "BatchLLMJob",
    "BatchResult",
    "BatchState",
    "BatchStatus",
]
