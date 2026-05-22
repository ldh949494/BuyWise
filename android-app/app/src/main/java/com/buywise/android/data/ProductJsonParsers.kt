package com.buywise.android.data

import org.json.JSONArray
import org.json.JSONObject

internal fun parseProductRead(json: JSONObject): Product {
    val description = json.optStringOrNull("description")
    val reviewSummary = json.optStringOrNull("review_summary")
    val scenes = json.optJSONArray("suitable_scene").toStringList()
    return Product(
        id = json.optInt("id").toString(),
        name = json.optString("name", "未命名商品"),
        brand = json.optStringOrNull("brand") ?: json.optStringOrNull("platform"),
        category = json.optStringOrNull("category"),
        price = json.optDoubleOrNull("price"),
        rating = json.optDoubleOrNull("rating"),
        recommendationScore = null,
        headline = description ?: reviewSummary ?: "暂无商品简介",
        tags = json.optJSONArray("tags").toStringList().ifEmpty { scenes },
        advantages = listOfNotBlank(reviewSummary) + scenes.map { "适合$it" },
        cautions = listOfNotBlank(json.optStringOrNull("stock_status")?.let { "库存状态：$it" }),
        imageUrl = json.optStringOrNull("image_url"),
        productUrl = json.optStringOrNull("product_url"),
        stockStatus = json.optStringOrNull("stock_status"),
        reviewSummary = reviewSummary,
    )
}

internal fun parseProductCard(json: JSONObject, category: String, reason: String): Product {
    val conflicts = json.optJSONArray("conflicts").toStringList()
    return Product(
        id = json.optInt("id").toString(),
        name = json.optString("name", "未命名商品"),
        brand = "BuyWise",
        category = category.ifBlank { "推荐商品" },
        price = json.optDoubleOrNull("price"),
        rating = json.optDoubleOrNull("rating"),
        recommendationScore = json.optDoubleOrNull("score"),
        headline = reason,
        tags = json.optJSONArray("tags").toStringList(),
        advantages = listOfNotBlank(reason),
        cautions = conflicts,
        imageUrl = json.optStringOrNull("image_url"),
    )
}

internal fun parseCompareItem(json: JSONObject): Product {
    val pros = json.optJSONArray("pros").toStringList()
    val cons = json.optJSONArray("cons").toStringList()
    return Product(
        id = (json.optIntOrNull("product_id") ?: json.optInt("id")).toString(),
        name = json.optString("name", "未命名商品"),
        brand = "BuyWise",
        category = "对比商品",
        price = json.optDoubleOrNull("price"),
        rating = json.optDoubleOrNull("rating"),
        recommendationScore = json.optDoubleOrNull("score"),
        headline = pros.firstOrNull() ?: "后端已返回对比结果",
        tags = pros.ifEmpty { listOf("对比结果") },
        advantages = pros,
        cautions = cons,
        imageUrl = json.optStringOrNull("image_url"),
    )
}

internal fun buildCompareRows(products: List<Product>): List<CompareRow> {
    if (products.isEmpty()) {
        return emptyList()
    }
    return listOf(
        CompareRow("价格", products.map { it.price.displayPrice() }),
        CompareRow("评分", products.map { it.rating.displayRating() }),
        CompareRow("推荐分", products.map { it.recommendationScore.displayScore() }),
        CompareRow("优点", products.map { it.advantages.take(2).joinToString(" / ").ifBlank { "暂无" } }),
        CompareRow("注意事项", products.map { it.cautions.take(2).joinToString(" / ").ifBlank { "暂无" } }),
    )
}

private fun JSONArray?.toStringList(): List<String> {
    if (this == null) {
        return emptyList()
    }
    return (0 until length()).mapNotNull { index -> optString(index).takeIf { it.isNotBlank() } }
}

private fun listOfNotBlank(value: String?): List<String> =
    if (value.isNullOrBlank()) emptyList() else listOf(value)

private fun JSONObject.optStringOrNull(name: String): String? =
    if (has(name) && !isNull(name)) optString(name).takeIf { it.isNotBlank() } else null

private fun JSONObject.optDoubleOrNull(name: String): Double? =
    if (has(name) && !isNull(name)) optDouble(name) else null

private fun JSONObject.optIntOrNull(name: String): Int? =
    if (has(name) && !isNull(name)) optInt(name) else null

private fun Double?.displayPrice(): String = this?.let { "¥${formatNumber(it)}" } ?: "暂无"

private fun Double?.displayRating(): String = this?.let { formatNumber(it) } ?: "暂无"

private fun Double?.displayScore(): String = this?.let { formatNumber(it) } ?: "暂无"

private fun formatNumber(value: Double): String =
    if (value % 1.0 == 0.0) value.toInt().toString() else "%.1f".format(value)
