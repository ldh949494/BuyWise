package com.buywise.android.data

import java.io.IOException

class CompareRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
) {
    @Throws(IOException::class)
    fun compareProducts(productIds: List<String>, userNeed: String? = null): CompareState {
        val ids = productIds.mapNotNull { it.toIntOrNull() }.distinct()
        if (ids.size < 2) {
            return CompareState(
                products = emptyList(),
                rows = emptyList(),
                errorMessage = "至少需要 2 个商品才能对比。",
            )
        }
        val response: CompareResponseDto = apiClient.post(
            "/api/v1/products/compare",
            CompareRequestDto(ids, userNeed ?: "对比这些商品的价格、评分、优点和注意事项"),
        )
        val products = response.items.map { it.toProduct() }
        return CompareState(
            products = products,
            rows = buildCompareRows(products),
            summary = response.summary,
            winnerId = response.winnerId?.toString(),
        )
    }
}
