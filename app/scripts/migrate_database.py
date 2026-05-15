"""Apply database migrations."""

from pathlib import Path

from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[2]


def get_alembic_config() -> Config:
    return Config(str(ROOT / "alembic.ini"))


def upgrade_database(revision: str = "head") -> None:
    command.upgrade(get_alembic_config(), revision)


if __name__ == "__main__":
    upgrade_database()
