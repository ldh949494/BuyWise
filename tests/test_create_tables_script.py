from app.scripts import create_tables


def test_create_tables_script_imports_models() -> None:
    table_names = set(create_tables.Base.metadata.tables)

    assert {
        "products",
        "reviews",
        "price_history",
        "chat_sessions",
        "chat_messages",
        "recommendations",
    }.issubset(table_names)
