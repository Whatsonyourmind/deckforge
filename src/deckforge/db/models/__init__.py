"""Import all models so Alembic autogenerate can detect them."""

from deckforge.db.models.api_key import ApiKey
from deckforge.db.models.batch_job import BatchJob
from deckforge.db.models.deck import Deck
from deckforge.db.models.job import Job
from deckforge.db.models.payment_event import PaymentEvent
from deckforge.db.models.usage import CreditReservation, UsageRecord
from deckforge.db.models.user import User
from deckforge.db.models.webhook_registration import WebhookRegistration

__all__ = [
    "User",
    "ApiKey",
    "Deck",
    "Job",
    "BatchJob",
    "WebhookRegistration",
    "UsageRecord",
    "CreditReservation",
    "PaymentEvent",
]
