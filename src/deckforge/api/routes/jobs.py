"""Job status endpoint -- query async job progress and results."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, status

from deckforge.api.deps import DbSession
from deckforge.api.middleware.auth import CurrentApiKey
from deckforge.api.schemas.responses import JobResponse
from deckforge.db.repositories import job_repo

router = APIRouter(tags=["jobs"])


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    responses={
        404: {"description": "Job not found"},
    },
)
async def get_job(
    job_id: uuid.UUID,
    db: DbSession,
    api_key: CurrentApiKey,
) -> JobResponse:
    """Retrieve the status and progress of an async job."""
    job = await job_repo.get_by_id(db, job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found.",
        )

    return JobResponse(
        id=str(job.id),
        status=job.status,
        progress=job.progress,
        job_type=job.job_type,
        created_at=job.created_at.isoformat() if job.created_at else "",
        result=job.result,
    )
