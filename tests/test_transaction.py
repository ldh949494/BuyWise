import pytest

from app.core.transaction import unit_of_work


class FakeDb:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self.refreshed = []

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def refresh(self, entity) -> None:
        self.refreshed.append(entity)


def test_unit_of_work_commits_and_refreshes_registered_entities() -> None:
    db = FakeDb()
    entity = object()

    with unit_of_work(db) as uow:
        uow.refresh_after_commit(entity)

    assert db.committed is True
    assert db.rolled_back is False
    assert db.refreshed == [entity]


def test_unit_of_work_rolls_back_on_error() -> None:
    db = FakeDb()

    with pytest.raises(RuntimeError):
        with unit_of_work(db):
            raise RuntimeError("write failed")

    assert db.committed is False
    assert db.rolled_back is True
