from app.services import readiness_service


class FakeDb:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, statement):
        return None

    def scalars(self, statement):
        return FakeScalars()


class FakeScalars:
    def all(self):
        return [1, 2]


class FakeProduct:
    def __init__(self, product_id: int) -> None:
        self.id = product_id


class FakeProductRepository:
    def __init__(self, db) -> None:
        self.db = db

    def get_all(self):
        return [FakeProduct(1), FakeProduct(2)]


class FakeProductStore:
    def indexed_product_ids(self):
        return [1, 2]

    def count(self):
        return 2


class FakeSettings:
    def validate_production(self):
        return None


def test_validate_readiness_fails_when_expected_active_product_count_differs() -> None:
    service = readiness_service.ReadinessService(
        app_settings=FakeSettings(),
        session_factory=lambda: FakeDb(),
        product_repository_type=FakeProductRepository,
        product_store=FakeProductStore(),
    )

    report = service.validate_readiness(include_details=True, expected_active_products=50)

    assert report["status"] == "not_ready"
    assert report["checks"]["products"]["status"] == "failed"
    assert report["checks"]["products"]["product_count"] == 2
    assert "Expected 50 active products" in report["checks"]["products"]["detail"]
