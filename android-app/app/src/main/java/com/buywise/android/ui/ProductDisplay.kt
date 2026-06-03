package com.buywise.android.ui

import com.buywise.android.data.Product
object BuyWiseDimens {
    const val CardRadius = 12
    const val HeroRadius = 16
    const val ChipRadius = 999
}

fun Product.displayRecommendationReason(customReason: String? = null): String =
    customReason?.takeIf { it.isNotBlank() }
        ?: headline.takeIf { it.isNotBlank() }
        ?: "价格和口碑都比较稳，适合优先查看。"

fun Product.shortName(): String =
    name.replace("机械键盘", "").replace("键盘", "").trim().takeIf { it.isNotBlank() } ?: name

fun Double?.displayPrice(): String = this?.let { "¥${formatNumber(it)}" } ?: "暂无价格"

fun Double?.displayRating(): String = this?.let { formatNumber(it) } ?: "暂无"

fun formatNumber(value: Double): String =
    if (value % 1.0 == 0.0) value.toInt().toString() else "%.1f".format(value)
