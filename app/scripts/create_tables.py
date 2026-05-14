"""Create database tables for all SQLAlchemy models."""

from app.core.database import Base, engine
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
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
