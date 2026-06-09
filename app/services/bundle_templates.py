"""Bundle scenario templates."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScenarioTemplate:
    key: str
    title_prefix: str
    required_categories: list[str]
    optional_categories: list[str] = field(default_factory=list)
    budget_weights: dict[str, float] = field(default_factory=dict)
    optional_budget_weights: dict[str, float] = field(default_factory=dict)
    roles: dict[str, str] = field(default_factory=dict)
    scenario_fit: str = "覆盖当前场景的核心需求"
    default_budget: float = 3000.0
    confirmation_prompts: dict[str, str] = field(default_factory=dict)


DESKTOP_TEMPLATE = ScenarioTemplate(
    key="desktop",
    title_prefix="桌面",
    required_categories=["电脑", "显示器", "机械键盘", "鼠标", "蓝牙耳机"],
    optional_categories=["台灯", "支架", "拓展坞", "插排"],
    budget_weights={"电脑": 0.55, "显示器": 0.22, "机械键盘": 0.07, "鼠标": 0.04, "蓝牙耳机": 0.08},
    optional_budget_weights={"台灯": 0.04, "支架": 0.03, "拓展坞": 0.04, "插排": 0.02},
    roles={
        "电脑": "性能核心",
        "显示器": "显示体验",
        "机械键盘": "输入体验",
        "鼠标": "指针控制",
        "蓝牙耳机": "会议与降噪",
        "台灯": "学习照明",
        "支架": "桌面人体工学",
        "拓展坞": "接口扩展",
        "插排": "供电补齐",
    },
    scenario_fit="学习、办公、编程和日常桌面使用",
    default_budget=6000.0,
    confirmation_prompts={"显示器": "是否已有显示器", "电脑": "是否已有电脑或主机"},
)
TRAVEL_TEMPLATE = ScenarioTemplate(
    key="travel",
    title_prefix="出行",
    required_categories=["防晒", "上衣", "外套", "裤装", "鞋履", "双肩包"],
    optional_categories=["充电宝", "墨镜", "帽子", "泳装", "洗护"],
    budget_weights={"防晒": 0.08, "上衣": 0.15, "外套": 0.2, "裤装": 0.14, "鞋履": 0.2, "双肩包": 0.16},
    optional_budget_weights={"充电宝": 0.06, "墨镜": 0.05, "帽子": 0.03, "泳装": 0.05, "洗护": 0.03},
    roles={
        "防晒": "防晒保护",
        "上衣": "主穿搭",
        "外套": "早晚温差与造型",
        "裤装": "下装搭配",
        "鞋履": "步行舒适",
        "双肩包": "随身收纳",
        "充电宝": "补电保障",
        "墨镜": "强光防护",
        "帽子": "遮阳补充",
        "泳装": "水上活动",
        "洗护": "旅行护理",
    },
    scenario_fit="旅行、度假、户外暴晒和轻量收纳",
    default_budget=2500.0,
    confirmation_prompts={"泳装": "是否包含水上活动", "外套": "是否需要早晚防风"},
)
GENERAL_TEMPLATE = ScenarioTemplate(
    key="general",
    title_prefix="场景",
    required_categories=[],
    optional_categories=[],
    scenario_fit="按当前场景、预算和偏好组合核心品类",
    default_budget=3000.0,
)
