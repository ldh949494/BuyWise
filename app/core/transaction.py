"""Transaction boundary helpers."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator


class UnitOfWork:
    def __init__(self, db: Any) -> None:
        self.db = db
        self._refresh_after_commit: list[Any] = []

    def refresh_after_commit(self, *entities: Any) -> None:
        self._refresh_after_commit.extend(entity for entity in entities if entity is not None)

    def commit(self) -> None:
        self.db.commit()
        for entity in self._refresh_after_commit:
            self.db.refresh(entity)

    def rollback(self) -> None:
        self.db.rollback()


@contextmanager
def unit_of_work(db: Any) -> Iterator[UnitOfWork]:
    uow = UnitOfWork(db)
    try:
        yield uow
        uow.commit()
    except Exception:
        uow.rollback()
        raise
