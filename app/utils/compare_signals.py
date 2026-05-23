"""Shared comparison signal scoring helpers."""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def score_price_signal(product: Any, average_price: float | None, pros: list[str], cons: list[str]) -> float:
    if product.price is None or average_price is None:
        return 0.0
    if Decimal(str(product.price)) < Decimal(str(average_price)):
        pros.append("近期价格更低")
        return 4.0
    cons.append("价格优势不明显")
    return 0.0


def score_review_counts(review_counts: dict[str, int], pros: list[str], cons: list[str]) -> float:
    positive = int(review_counts.get("positive", 0) + review_counts.get("正向", 0))
    negative = int(review_counts.get("negative", 0) + review_counts.get("负向", 0))
    if positive > negative and positive > 0:
        pros.append("用户反馈较好")
        return 4.0
    if negative > positive:
        cons.append("存在负面反馈")
        return -4.0
    return 0.0


def score_verified_feedback(feedback_metrics: dict[str, Any], pros: list[str], cons: list[str]) -> float:
    weighted_rating = feedback_metrics.get("weighted_rating")
    score = 0.0
    if isinstance(weighted_rating, int | float):
        if weighted_rating >= 4.2:
            pros.append("已购反馈满意度高")
            score += 6
        elif weighted_rating <= 2.5:
            cons.append("已购反馈满意度偏低")
            score -= 6
    for tag in feedback_metrics.get("top_pro_tags", [])[:2]:
        pros.append(f"已购反馈提到{tag}")
    for tag in feedback_metrics.get("top_con_tags", [])[:2]:
        cons.append(f"已购反馈提到{tag}")
    return score
