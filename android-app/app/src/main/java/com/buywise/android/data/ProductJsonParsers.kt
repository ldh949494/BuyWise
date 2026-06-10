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
    val resolvedCategory = json.optStringOrNull("category") ?: category.ifBlank { "推荐商品" }
    return Product(
        id = json.optInt("id").toString(),
        name = json.optString("name", "未命名商品"),
        brand = json.optStringOrNull("brand") ?: json.optStringOrNull("platform") ?: "BuyWise",
        category = resolvedCategory,
        price = json.optDoubleOrNull("price"),
        rating = json.optDoubleOrNull("rating"),
        recommendationScore = json.optDoubleOrNull("score"),
        headline = reason,
        tags = json.optJSONArray("tags").toStringList(),
        advantages = listOfNotBlank(reason),
        cautions = conflicts,
        imageUrl = json.optStringOrNull("image_url"),
        productUrl = json.optStringOrNull("product_url"),
        stockStatus = json.optStringOrNull("stock_status"),
    )
}

internal fun parseBundlePlan(json: JSONObject): BundlePlan {
    val items = json.optJSONArray("items")
    val checks = json.optJSONArray("compatibility_checks")
    return BundlePlan(
        id = json.optString("id", json.optString("title", "bundle-plan")),
        title = json.optString("title", "组合方案"),
        budgetTier = json.optString("budget_tier"),
        targetBudget = json.optDoubleOrNull("target_budget"),
        totalPrice = json.optDoubleOrNull("total_price") ?: 0.0,
        budgetStatus = json.optString("budget_status"),
        budgetDelta = json.optDoubleOrNull("budget_delta"),
        recommendationLevel = json.optString("recommendation_level", "medium"),
        scenarioFit = json.optStringOrNull("scenario_fit"),
        summary = json.optStringOrNull("summary"),
        completeness = parseBundleCompleteness(json.optJSONObject("completeness")),
        items = (0 until (items?.length() ?: 0)).mapNotNull { index ->
            items?.optJSONObject(index)?.let(::parseBundlePlanItem)
        },
        tradeoffs = json.optJSONArray("tradeoffs").toStringList(),
        compareHighlights = json.optJSONArray("compare_highlights").toStringList(),
        exclusionNotes = json.optJSONArray("exclusion_notes").toStringList(),
        compatibilityChecks = (0 until (checks?.length() ?: 0)).mapNotNull { index ->
            checks?.optJSONObject(index)?.let(::parseBundleCompatibilityCheck)
        },
        availabilityStatus = json.optString("availability_status", "available"),
    )
}

private fun parseBundleCompleteness(json: JSONObject?): BundleCompleteness =
    BundleCompleteness(
        includedRequired = json?.optInt("included_required") ?: 0,
        expectedRequired = json?.optInt("expected_required") ?: 0,
        optionalIncluded = json?.optInt("optional_included") ?: 0,
        missing = json?.optJSONArray("missing").toStringList(),
        needsConfirmation = json?.optJSONArray("needs_confirmation").toStringList(),
    )

private fun parseBundlePlanItem(json: JSONObject): BundlePlanItem {
    val category = json.optString("category", "推荐商品")
    val productJson = json.optJSONObject("product") ?: JSONObject()
    val role = json.optStringOrNull("role")
    return BundlePlanItem(
        category = category,
        product = parseProductCard(productJson, category, role ?: productJson.optString("name", "方案商品")),
        role = role,
        required = json.optBoolean("required", true),
        replaceable = json.optBoolean("replaceable", true),
        locked = json.optBoolean("locked", false),
        excluded = json.optBoolean("excluded", false),
    )
}

private fun parseBundleCompatibilityCheck(json: JSONObject): BundleCompatibilityCheck =
    BundleCompatibilityCheck(
        title = json.optString("title", "搭配检查"),
        status = json.optString("status", "needs_confirmation"),
        message = json.optString("message", "需要确认"),
    )

internal fun parseCompareItem(json: JSONObject): Product {
    val pros = json.optJSONArray("pros").toStringList().cleanMarkdownTextList()
    val cons = json.optJSONArray("cons").toStringList().cleanMarkdownTextList()
    return Product(
        id = (json.optIntOrNull("product_id") ?: json.optInt("id")).toString(),
        name = json.optString("name", "未命名商品"),
        brand = "BuyWise",
        category = "对比商品",
        price = json.optDoubleOrNull("price"),
        rating = json.optDoubleOrNull("rating"),
        recommendationScore = json.optDoubleOrNull("score"),
        headline = pros.firstOrNull() ?: "已生成对比结果",
        tags = pros.ifEmpty { listOf("对比结果") },
        advantages = pros,
        cautions = cons,
        imageUrl = json.optStringOrNull("image_url"),
    )
}

internal fun parseCart(json: JSONObject): CartState {
    val itemsJson = json.optJSONArray("items")
    val items = (0 until (itemsJson?.length() ?: 0)).mapNotNull { index ->
        itemsJson?.optJSONObject(index)?.let(::parseCartItem)
    }
    return CartState(
        items = items,
        totalQuantity = json.optInt("total_quantity", items.sumOf { it.quantity }),
        totalPrice = json.optDoubleOrNull("total_price") ?: items.sumOf { it.lineTotal },
    )
}

internal fun parseCartItem(json: JSONObject): CartItem =
    CartItem(
        id = json.optInt("id").toString(),
        productId = json.optInt("product_id").toString(),
        quantity = json.optInt("quantity", 1),
        name = json.optString("name_snapshot", "购物车商品"),
        unitPrice = json.optDoubleOrNull("unit_price_snapshot") ?: 0.0,
        lineTotal = json.optDoubleOrNull("line_total") ?: 0.0,
        imageUrl = json.optStringOrNull("image_url_snapshot"),
    )

internal fun parseAddress(json: JSONObject): Address =
    Address(
        id = json.optInt("id").toString(),
        receiverName = json.optString("receiver_name", "收货人"),
        phone = json.optString("phone"),
        detail = json.optString("detail"),
        isDefault = json.optBoolean("is_default", false),
    )

internal fun parseCheckout(json: JSONObject): CheckoutResult {
    val order = json.optJSONObject("order") ?: JSONObject()
    return CheckoutResult(
        orderId = order.optInt("id").toString(),
        status = order.optString("fulfillment_status", "created"),
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
