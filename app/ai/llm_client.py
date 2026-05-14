"""Mock-first LLM client wrapper for later provider replacement."""

from __future__ import annotations

from typing import Any


class LLMClient:
    async def chat(self, messages: list[dict]) -> str:
        user_messages = [
            message.get("content", "")
            for message in messages
            if message.get("role") == "user"
        ]
        content = user_messages[-1] if user_messages else ""
        return self.generate_reply(content)

    async def generate_recommendation(self, need: Any, products: list[Any]) -> str:
        if not products:
            return "暂时没有找到完全匹配的商品，可以放宽预算或调整条件"

        category = self._get_value(need, "category")
        scenario = self._get_value(need, "scenario")
        preferences = self._coerce_list(self._get_value(need, "preferences"))

        context_parts = []
        if category:
            context_parts.append(f"{category}")
        if scenario:
            context_parts.append(f"{scenario}场景")
        if preferences:
            context_parts.append("偏好" + "、".join(preferences))

        opening = "根据你的需求"
        if context_parts:
            opening += "（" + "，".join(context_parts) + "）"
        opening += "，我建议优先看："

        product_lines = []
        for index, product in enumerate(products, start=1):
            name = self._get_value(product, "name")
            price = self._get_value(product, "price")
            rating = self._get_value(product, "rating")
            reason = self._get_value(product, "reason")

            details = [f"{index}. {name}"]
            if price is not None:
                details.append(f"价格约{self._format_number(price)}元")
            if rating is not None:
                details.append(f"评分{self._format_number(rating)}")
            if reason:
                details.append(str(reason))
            product_lines.append("，".join(details))

        return opening + "\n" + "\n".join(product_lines)

    async def generate_clarify_question(self, need: Any) -> str:
        missing_fields = self._coerce_list(self._get_value(need, "missing_fields"))
        if not missing_fields:
            return "你还有哪些预算、使用场景或偏好要求？"

        field_names = {
            "category": "商品类型",
            "budget_max": "预算",
            "scenario": "使用场景",
            "preferences": "偏好",
        }
        questions = [field_names.get(field, field) for field in missing_fields]
        return "为了更准确推荐，请补充：" + "、".join(questions) + "。"

    async def generate_compare_summary(self, user_need: Any, products: list[Any]) -> str:
        if not products:
            return "暂时没有找到完全匹配的商品，可以放宽预算或调整条件"

        scenario = self._get_value(user_need, "scenario")
        opening = "这几款商品可以这样对比："
        if scenario:
            opening = f"按{scenario}场景看，这几款商品可以这样对比："

        lines = []
        for product in products:
            name = self._get_value(product, "name")
            price = self._get_value(product, "price")
            rating = self._get_value(product, "rating")
            reason = self._get_value(product, "reason")

            parts = [str(name)]
            if price is not None:
                parts.append(f"价格约{self._format_number(price)}元")
            if rating is not None:
                parts.append(f"评分{self._format_number(rating)}")
            if reason:
                parts.append(str(reason))
            lines.append("，".join(parts))

        return opening + "\n" + "\n".join(lines)

    def generate_reply(self, user_query: str) -> str:
        return f"Mock shopping guidance for: {user_query}"

    def _get_value(self, source: Any, key: str) -> Any:
        if isinstance(source, dict):
            return source.get(key)
        return getattr(source, key, None)

    def _coerce_list(self, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item) for item in value if item]
        return [str(value)]

    def _format_number(self, value: Any) -> str:
        number = float(value)
        return str(int(number)) if number.is_integer() else f"{number:g}"
