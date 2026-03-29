"""Repository singletons for database access.

Usage:
    from deckforge.db.repositories import api_key_repo, deck_repo, job_repo

    deck = await deck_repo.create(session, api_key_id=key_id, ir_snapshot=ir)
"""

from deckforge.db.repositories.api_key import ApiKeyRepository
from deckforge.db.repositories.deck import DeckRepository
from deckforge.db.repositories.job import JobRepository

api_key_repo = ApiKeyRepository()
deck_repo = DeckRepository()
job_repo = JobRepository()

__all__ = [
    "ApiKeyRepository",
    "DeckRepository",
    "JobRepository",
    "api_key_repo",
    "deck_repo",
    "job_repo",
]
