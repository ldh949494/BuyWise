from decimal import Decimal
from types import SimpleNamespace

from app.schemas.chat import ProductCard, StructuredNeed
from app.services.recommend_service import RecommendService


def make_product(**kwargs):
    defaults = {
        "id": 1,
        "name": "K87 静音红轴机械键盘",
        "price": Decimal("299.00"),
        "image_url": "https://example.com/p.jpg",
        "rating": Decimal("4.8"),
        "sales": 1800,
        "tags": ["低噪音", "无线", "性价比"],
        "suitable_scene": ["宿舍", "写代码"],
        "stock": 20,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_rank_returns_product_cards_sorted_by_score_with_reasons() -> None:
    service = RecommendService()
    need = StructuredNeed(
        intent="商品推荐",
        budget_max=300,
        scenario="宿舍",
        preferences=["低噪音", "无线", "性价比"],
    )
    products = [
        make_product(id=1, name="Best", price=Decimal("299.00"), rating=Decimal("4.8"), sales=1800),
        make_product(
            id=2,
            name="Over Budget",
            price=Decimal("399.00"),
            rating=Decimal("4.9"),
            sales=5000,
            tags=["无线"],
            suitable_scene=["办公"],
            stock=0,
        ),
    ]

    cards = service.rank(products, need)

    assert all(isinstance(card, ProductCard) for card in cards)
    assert [card.name for card in cards] == ["Best", "Over Budget"]
    assert cards[0].score > cards[1].score
    assert cards[0].budget_match is True
    assert cards[0].scenario_match is True
    assert "价格符合预算" in cards[0].reason
    assert "适合宿舍场景" in cards[0].reason
    assert "符合低噪音偏好" in cards[0].reason
    assert "符合无线偏好" in cards[0].reason
    assert "符合性价比偏好" in cards[0].reason
    assert "库存充足" in cards[0].reason
    assert "宿舍场景匹配不明确" not in (cards[1].reason or "")
    assert "超出预算" in cards[1].conflicts
    assert "库存不足" in cards[1].conflicts


def test_rank_handles_json_string_tags_scenes_and_none_values() -> None:
    service = RecommendService()
    need = {
        "budget_max": 500,
        "scenario": "通勤",
        "preferences": ["轻便", "大容量"],
    }
    product = make_product(
        id=3,
        name="CityPack",
        price=Decimal("199.00"),
        rating=None,
        sales=None,
        tags='["轻便", "大容量"]',
        suitable_scene='["通勤", "办公"]',
        stock=None,
    )

    cards = service.rank([product], need)

    assert cards[0].tags == ["轻便", "大容量"]
    assert cards[0].budget_match is True
    assert cards[0].scenario_match is True
    assert "价格符合预算" in cards[0].reason
    assert "适合通勤场景" in cards[0].reason
    assert "符合轻便偏好" in cards[0].reason
    assert "符合大容量偏好" in cards[0].reason


def test_rank_caps_preference_score_at_30_points() -> None:
    service = RecommendService()
    need = {
        "preferences": ["低噪音", "无线", "护眼", "颜值高"],
    }
    product = make_product(
        tags=["低噪音", "无线", "护眼", "颜值高"],
        suitable_scene=None,
        rating=None,
        sales=None,
        stock=None,
    )

    cards = service.rank([product], need)

    assert cards[0].score == 30
    assert "符合颜值高偏好" not in cards[0].reason


def test_rank_uses_reputation_as_tiebreaker_without_reason_noise() -> None:
    service = RecommendService()
    need = {"budget_max": 400, "scenario": "宿舍", "preferences": ["低噪音"]}
    lower_reputation = make_product(id=1, name="Lower", rating=Decimal("4.1"), sales=100)
    higher_reputation = make_product(id=2, name="Higher", rating=Decimal("4.9"), sales=900)

    cards = service.rank([lower_reputation, higher_reputation], need)

    assert [card.name for card in cards] == ["Higher", "Lower"]
    assert "评分" not in cards[0].reason
