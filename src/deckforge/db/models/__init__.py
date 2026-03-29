"""Import all models so Alembic autogenerate can detect them."""

from deckforge.db.models.api_key import ApiKey
from deckforge.db.models.deck import Deck
from deckforge.db.models.job import Job
from deckforge.db.models.user import User

__all__ = ["User", "ApiKey", "Deck", "Job"]
