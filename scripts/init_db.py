def init_db() -> None:
    from app.scripts.migrate_database import upgrade_database

    upgrade_database()


if __name__ == "__main__":
    init_db()
