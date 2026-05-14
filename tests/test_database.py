from sqlalchemy.orm import DeclarativeBase

from app.core.database import Base, SessionLocal, engine, get_db


def test_database_base_is_declarative_base() -> None:
    assert issubclass(Base, DeclarativeBase)


def test_session_local_is_configured() -> None:
    assert SessionLocal.kw["autoflush"] is False
    assert SessionLocal.kw["autocommit"] is False
    assert str(engine.url).startswith("mysql+pymysql://")


def test_get_db_yields_session_and_closes_it() -> None:
    generator = get_db()
    session = next(generator)

    assert session.bind is engine

    try:
        next(generator)
    except StopIteration:
        pass

    assert session.is_active is True
