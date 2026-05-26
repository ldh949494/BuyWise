from decimal import Decimal
from types import SimpleNamespace

from app.services.policies.recommendation_scoring_policy import RecommendationScoringPolicy


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


def test_scores_budget_scenario_preferences_stock_and_feedback_reasons() -> None:
    policy = RecommendationScoringPolicy()
    need = {"budget_max": 300, "scenario": "宿舍", "preferences": ["低噪音"], "avoid": ["蓝牙"]}
    product = make_product(feedback_metrics={"weighted_rating": 5.0})

    result = policy.build_score_result(product, need)

    assert result.score == 80.4
    assert result.budget_match is True
    assert result.scenario_match is True
    assert result.tags == ["低噪音", "无线", "性价比"]
    assert result.price == Decimal("299.00")
    assert result.rating == 4.8
    assert result.reasons == ["价格符合预算", "适合宿舍场景", "符合低噪音偏好", "库存充足", "已购反馈满意度高"]
    assert result.conflicts == []


def test_caps_preference_score_at_three_hits() -> None:
    policy = RecommendationScoringPolicy()
    need = {"preferences": ["低噪音", "无线", "护眼", "颜值高"]}
    product = make_product(
        tags=["低噪音", "无线", "护眼", "颜值高"],
        suitable_scene=None,
        rating=None,
        sales=None,
        stock=None,
    )

    result = policy.build_score_result(product, need)

    assert result.score == 30
    assert "符合颜值高偏好" not in result.reasons


def test_scores_conflicts_for_budget_stock_avoid_and_feedback() -> None:
    policy = RecommendationScoringPolicy()
    need = {"budget_max": 300, "avoid": ["噪音"]}
    product = make_product(
        price=Decimal("399.00"),
        stock=0,
        tags=["噪音"],
        feedback_metrics={"weighted_rating": 2.0},
    )

    result = policy.build_score_result(product, need)

    assert result.budget_match is False
    assert result.score == 0
    assert result.conflicts == ["超出预算", "命中避雷项：噪音", "库存不足", "已购反馈满意度偏低"]
