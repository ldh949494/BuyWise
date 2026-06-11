from decimal import Decimal
from types import SimpleNamespace

from app.ai.rag_policy import RagFallbackPolicy, RagFilterPolicy, RagRerankPolicy


def product(**kwargs):
    defaults = {"id": 1, "name": "K87", "category": "机械键盘", "price": Decimal("329.00"), "stock": 10}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_fallback_policy_relaxes_budget_and_lists_adjacent_categories() -> None:
    policy = RagFallbackPolicy(
        budget_multiplier=Decimal("1.15"),
        budget_delta=Decimal("50"),
        adjacent_categories={"学习用品": ["台灯", "机械键盘"]},
    )

    assert policy.list_stages() == [
        "fallback_budget",
        "fallback_relaxed",
        "fallback_keyword",
        "fallback_adjacent",
        "fallback_popular",
    ]
    assert policy.get_page_size(20) == 60
    assert policy.get_relaxed_budget(400) == Decimal("460.00")
    assert policy.list_adjacent_categories("学习用品") == ["台灯", "机械键盘"]


def test_filter_policy_keeps_diagnostics_reasons_by_stage() -> None:
    policy = RagFilterPolicy(RagFallbackPolicy())
    need = {"category": "机械键盘", "budget_max": 400}
    products = [
        product(id=1),
        product(id=2, category="蓝牙耳机"),
        product(id=3, price=Decimal("499.00")),
        product(id=4, stock=0),
    ]

    strict, strict_reasons = policy.get_filtered_products(products, need)
    relaxed, relaxed_reasons = policy.get_filtered_products([products[2]], need, stage="fallback_relaxed")
    keyword, keyword_reasons = policy.get_filtered_products([products[1]], need, stage="fallback_keyword")
    adjacent, adjacent_reasons = policy.get_filtered_products([products[1]], need, stage="fallback_adjacent")
    popular, popular_reasons = policy.get_filtered_products([products[1]], need, stage="fallback_popular")

    assert [item.id for item in strict] == [1]
    assert dict(strict_reasons) == {"category_mismatch": 1, "over_budget": 1, "out_of_stock": 1}
    assert [item.id for item in relaxed] == [3]
    assert dict(relaxed_reasons) == {}
    assert [item.id for item in keyword] == [2]
    assert dict(keyword_reasons) == {}
    assert [item.id for item in adjacent] == [2]
    assert dict(adjacent_reasons) == {}
    assert [item.id for item in popular] == [2]
    assert dict(popular_reasons) == {}


def test_rerank_policy_maps_ranked_cards_back_to_products() -> None:
    class FakeReranker:
        def rank(self, products, need):
            return [SimpleNamespace(id=2), SimpleNamespace(id=1), SimpleNamespace(id=999)]

    products = [product(id=1), product(id=2)]

    assert [item.id for item in RagRerankPolicy(FakeReranker()).rank_products(products, {})] == [2, 1]
    assert RagRerankPolicy().rank_products(products, {}) == products
