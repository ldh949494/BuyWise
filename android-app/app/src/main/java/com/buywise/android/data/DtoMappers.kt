package com.buywise.android.data

internal fun ProductDto.toProduct(): Product {
    val scenes = suitableScene
    return Product(
        id = id.toString(),
        name = name,
        brand = brand ?: platform,
        category = category,
        price = price,
        rating = rating,
        recommendationScore = null,
        headline = description ?: reviewSummary ?: "暂无商品简介",
        tags = tags.ifEmpty { scenes },
        advantages = listOfNotBlank(reviewSummary) + scenes.map { "适合$it" },
        cautions = listOfNotBlank(stockStatus?.let { "库存状态：$it" }),
        imageUrl = imageUrl,
        productUrl = productUrl,
        stockStatus = stockStatus,
        reviewSummary = reviewSummary,
    )
}

internal fun ProductCardDto.toProduct(category: String, fallbackReason: String): Product {
    val resolvedReason = reason ?: description ?: fallbackReason
    return Product(
        id = id.toString(),
        name = name,
        brand = "BuyWise",
        category = category.ifBlank { "推荐商品" },
        price = price,
        rating = rating,
        recommendationScore = score,
        headline = resolvedReason,
        tags = tags,
        advantages = listOfNotBlank(resolvedReason),
        cautions = conflicts,
        imageUrl = imageUrl,
    )
}

internal fun CompareItemDto.toProduct(): Product {
    val resolvedId = productId ?: id ?: 0
    return Product(
        id = resolvedId.toString(),
        name = name,
        brand = "BuyWise",
        category = "对比商品",
        price = price,
        rating = rating,
        recommendationScore = score,
        headline = pros.firstOrNull() ?: "后端已返回对比结果",
        tags = pros.ifEmpty { listOf("对比结果") },
        advantages = pros,
        cautions = cons,
        imageUrl = imageUrl,
    )
}

internal fun FeedbackPromptDto.toPrompt(): FeedbackPrompt =
    FeedbackPrompt(
        orderId = orderId.toString(),
        orderItemId = orderItemId.toString(),
        productId = productId.toString(),
        productName = productName,
    )

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

private fun listOfNotBlank(value: String?): List<String> =
    if (value.isNullOrBlank()) emptyList() else listOf(value)

private fun Double?.displayPrice(): String = this?.let { "¥${formatNumber(it)}" } ?: "暂无"

private fun Double?.displayRating(): String = this?.let { formatNumber(it) } ?: "暂无"

private fun Double?.displayScore(): String = this?.let { formatNumber(it) } ?: "暂无"

private fun formatNumber(value: Double): String =
    if (value % 1.0 == 0.0) value.toInt().toString() else "%.1f".format(value)
