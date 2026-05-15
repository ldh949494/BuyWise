from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_alembic_files_exist() -> None:
    assert (ROOT / "alembic.ini").is_file()
    assert (ROOT / "alembic" / "env.py").is_file()
    assert (ROOT / "alembic" / "script.py.mako").is_file()


def test_initial_migration_covers_current_tables() -> None:
    migration = ROOT / "alembic" / "versions" / "20260515_0001_initial_schema.py"
    text = migration.read_text(encoding="utf-8")

    for table_name in {
        "products",
        "reviews",
        "price_history",
        "chat_sessions",
        "chat_messages",
        "recommendations",
    }:
        assert f'"{table_name}"' in text
