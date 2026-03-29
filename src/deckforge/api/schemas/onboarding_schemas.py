"""Pydantic schemas for the developer onboarding flow.

Covers signup (create user + API key) and onboarding status tracking.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class SignupRequest(BaseModel):
    """Request body for POST /v1/onboard/signup."""

    email: EmailStr = Field(description="Developer email address")
    name: str = Field(
        min_length=1,
        max_length=200,
        description="Developer name",
    )
    tier: Literal["starter", "pro"] = Field(
        default="starter",
        description="Billing tier to start with",
    )


class SignupResponse(BaseModel):
    """Response for POST /v1/onboard/signup.

    Contains the API key (shown only once) and quick-start instructions.
    """

    user_id: str = Field(description="UUID of the created user")
    api_key: str = Field(
        description="The API key -- shown only once, store securely"
    )
    tier: str = Field(description="Selected billing tier")
    credits: int = Field(description="Monthly credit limit for this tier")
    next_steps: list[str] = Field(
        description="Quick-start instructions to get to first deck"
    )


class OnboardingStatusResponse(BaseModel):
    """Response for GET /v1/onboard/status/{user_id}.

    Tracks onboarding milestones to guide developers to first deck.
    """

    steps_completed: list[str] = Field(
        description="Onboarding steps the developer has completed"
    )
    next_step: str = Field(
        description="Suggested next action"
    )
    time_elapsed_seconds: int = Field(
        description="Seconds since account creation"
    )
