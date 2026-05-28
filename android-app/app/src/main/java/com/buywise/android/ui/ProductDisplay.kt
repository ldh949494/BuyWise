package com.buywise.android.ui

import com.buywise.android.data.Product
object BuyWiseDimens {
    const val CardRadius = 18
    const val HeroRadius = 24
    const val ChipRadius = 999
}

fun Product.displayBrandCategory(): String =
    listOfNotNull(brand?.takeIf { it.isNotBlank() }, category?.takeIf { it.isNotBlank() })
        .joinToString(" / ")
        .ifBlank { "精选商品" }

fun Product.displayMatchPercent(): String = "${matchPercent()}%"

fun Product.matchPercent(): Int {
    recommendationScore?.let { return it.coerceIn(0.0, 100.0).toInt() }
    val fallback = listOf(92, 89, 86, 84, 81)
    val key = id.toIntOrNull() ?: (name.hashCode() and Int.MAX_VALUE)
    return fallback[key % fallback.size]
}

fun Product.displayPlatform(): String {
    val text = listOfNotNull(brand, category, name, tags.joinToString(" ")).joinToString(" ")
    return when {
        "耳机" in text || "音频" in text -> "天猫精选"
        "键盘" in text || "机械" in text -> "京东自营"
        "电脑" in text || "显示器" in text -> "品牌官方"
        else -> "平台优选"
    }
}

fun Product.displaySales(): String {
    val fallback = listOf("已售 1.2w+", "已售 8600+", "已售 5200+", "已售 3100+")
    val key = id.toIntOrNull() ?: (name.hashCode() and Int.MAX_VALUE)
    return fallback[key % fallback.size]
}

fun Product.displayStockLabel(): String =
    stockStatus?.takeIf { it.isNotBlank() } ?: "现货可选"

fun Product.displayRecommendationReason(customReason: String? = null): String =
    customReason?.takeIf { it.isNotBlank() }
        ?: headline.takeIf { it.isNotBlank() }
        ?: "价格、口碑和使用场景匹配度较高，适合作为优先候选。"

fun Product.displayFitTags(customReason: String? = null): List<String> {
    val text = listOfNotNull(
        category,
        headline,
        reviewSummary,
        customReason,
        tags.joinToString(" "),
        advantages.joinToString(" "),
    ).joinToString(" ").lowercase()
    val result = mutableListOf<String>()
    if (price != null && price <= 300.0) result += "预算友好"
    if ("宿舍" in text || "dorm" in text) result += "宿舍适配"
    if ("静音" in text || "低噪" in text || "quiet" in text) result += "低噪优先"
    if ("代码" in text || "编程" in text || "coding" in text) result += "写代码"
    if ("性价比" in text || "value" in text) result += "性价比"
    result += tags.filter { it.length <= 8 }
    return result.distinct().take(4)
}

fun Product.fitLevel(): String {
    val text = listOf(category, headline, tags.joinToString(" "), advantages.joinToString(" ")).joinToString(" ")
    return when {
        "宿舍" in text || "静音" in text || "低噪" in text -> "高"
        matchPercent() >= 88 -> "高"
        matchPercent() >= 84 -> "中"
        else -> "一般"
    }
}

fun Product.noiseLevel(): String {
    val text = listOf(category, headline, tags.joinToString(" "), advantages.joinToString(" ")).joinToString(" ")
    return when {
        "静音" in text || "低噪" in text || "quiet" in text -> "高"
        "键盘" in text || "耳机" in text -> "中"
        else -> "一般"
    }
}

fun Product.shortName(): String =
    name.replace("机械键盘", "").replace("键盘", "").trim().takeIf { it.isNotBlank() } ?: name

fun Double?.displayPrice(): String = this?.let { "¥${formatNumber(it)}" } ?: "暂无价格"

fun Double?.displayRating(): String = this?.let { formatNumber(it) } ?: "暂无"

fun formatNumber(value: Double): String =
    if (value % 1.0 == 0.0) value.toInt().toString() else "%.1f".format(value)
