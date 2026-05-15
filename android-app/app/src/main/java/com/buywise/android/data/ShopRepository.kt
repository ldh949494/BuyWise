package com.buywise.android.data

class ShopRepository {
    private val products = listOf(
        Product(
            id = "mouse-lite",
            name = "AeroMouse S",
            brand = "Pulse",
            category = "鼠标",
            price = 299,
            score = 95,
            headline = "轻量化无线电竞鼠标，适合 FPS 和长时间追踪。",
            tags = listOf("49g", "8K 回报率", "低延迟"),
            advantages = listOf("握持轻快", "定位稳定", "预算友好"),
            cautions = listOf("大手用户建议先试握"),
        ),
        Product(
            id = "keyboard-75",
            name = "RainKey 75",
            brand = "WOBKEY",
            category = "键盘",
            price = 699,
            score = 92,
            headline = "75% 配列机械键盘，兼顾桌搭和输入效率。",
            tags = listOf("75%", "Gasket", "三模"),
            advantages = listOf("布局紧凑", "声音干净", "适合桌搭"),
            cautions = listOf("预算高于入门款"),
        ),
        Product(
            id = "headset-wireless",
            name = "Cloud Air III",
            brand = "HyperSound",
            category = "耳机",
            price = 799,
            score = 89,
            headline = "舒适型无线耳机，适合语音开黑和长时佩戴。",
            tags = listOf("无线", "低延迟", "舒适佩戴"),
            advantages = listOf("夹力温和", "麦克风清晰", "续航稳"),
            cautions = listOf("便携性一般"),
        ),
        Product(
            id = "monitor-240",
            name = "Focus 27Q240",
            brand = "ViewCore",
            category = "显示器",
            price = 2499,
            score = 88,
            headline = "2K 240Hz 显示器，主打高速竞技场景。",
            tags = listOf("2K", "240Hz", "Fast IPS"),
            advantages = listOf("运动清晰度高", "响应快", "接口完整"),
            cautions = listOf("整机预算占比较高"),
        ),
    )

    fun homeState(): HomeState = HomeState(
        heroTitle = "BuyWise 帮你快速缩小购物范围",
        heroSubtitle = "输入需求后，先结构化偏好，再给出理由明确的导购建议。",
        products = products,
    )

    fun guideState(query: String): GuideState {
        val normalized = query.ifBlank { "300 元以内，适合 FPS 的轻量化无线鼠标" }
        return GuideState(
            query = query,
            intentSummary = "已识别：预算敏感 / 游戏场景 / 偏好低延迟和轻量化",
            recommendations = products.take(3).mapIndexed { index, product ->
                Recommendation(
                    product = product,
                    reason = when (index) {
                        0 -> "最贴合当前需求，价格、手感和性能平衡最好。"
                        1 -> "如果更重视桌面整洁和输入体验，可作为搭配升级。"
                        else -> "如果同时关注语音沟通体验，这款可作为次优补充。"
                    },
                )
            },
        ).copy(
            intentSummary = "围绕“$normalized”生成的 mock 需求画像",
        )
    }

    fun compareState(): CompareState {
        val compared = products.take(3)
        return CompareState(
            products = compared,
            rows = listOf(
                CompareRow("价格", compared.map { "¥${it.price}" }),
                CompareRow("推荐分", compared.map { "${it.score}" }),
                CompareRow("定位", compared.map { it.category }),
                CompareRow("亮点", compared.map { it.tags.take(2).joinToString(" / ") }),
            ),
        )
    }

    fun visionState(): VisionState = VisionState(
        result = VisionResult(
            title = "识别到桌面外设组合",
            confidence = 92,
            labels = listOf("机械键盘", "轻量鼠标", "电竞桌搭"),
            similarProducts = products.drop(1),
        ),
    )

    fun product(productId: String?): Product? = products.firstOrNull { it.id == productId }
}
