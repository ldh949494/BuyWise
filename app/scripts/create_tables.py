"""Compatibility wrapper for database initialization."""

from app.core.database import Base
from app.models import (
    ChatMessage,
    ChatSession,
    PriceHistory,
    Product,
    Recommendation,
    Review,
)

_ = (
    ChatMessage,
    ChatSession,
    PriceHistory,
    Product,
    Recommendation,
    Review,
)


def create_tables() -> None:
    from app.scripts.migrate_database import upgrade_database

    upgrade_database()


if __name__ == "__main__":
    create_tables()
