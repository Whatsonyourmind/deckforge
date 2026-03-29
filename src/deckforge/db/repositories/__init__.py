"""Repository singletons for database access.

Usage:
    from deckforge.db.repositories import api_key_repo, deck_repo, job_repo

    deck = await deck_repo.create(session, api_key_id=key_id, ir_snapshot=ir)
"""

from deckforge.db.repositories.api_key import ApiKeyRepository
from deckforge.db.repositories.batch import BatchRepository
from deckforge.db.repositories.deck import DeckRepository
from deckforge.db.repositories.job import JobRepository
from deckforge.db.repositories.webhook import WebhookRepository

api_key_repo = ApiKeyRepository()
batch_repo = BatchRepository()
deck_repo = DeckRepository()
job_repo = JobRepository()
webhook_repo = WebhookRepository()

__all__ = [
    "ApiKeyRepository",
    "BatchRepository",
    "DeckRepository",
    "JobRepository",
    "WebhookRepository",
    "api_key_repo",
    "batch_repo",
    "deck_repo",
    "job_repo",
    "webhook_repo",
]
