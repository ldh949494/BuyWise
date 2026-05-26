package com.buywise.android.data

import java.io.IOException

class OrderRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
) {
    val capability: BetaCapability
        get() = apiClient.betaCapability

    @Throws(IOException::class)
    fun recordPurchase(productId: String): String {
        val created: OrderResponseDto = apiClient.post(
            "/api/v1/orders",
            OrderCreateRequestDto(productId = productId.toInt(), quantity = 1),
            requireAuth = true,
        )
        val shipped = apiClient.postEmpty("/api/v1/orders/${created.id}/advance", requireAuth = true)
        val delivered = apiClient.postEmpty("/api/v1/orders/${created.id}/advance", requireAuth = true)
        return delivered.fulfillmentStatus ?: shipped.fulfillmentStatus ?: "recorded"
    }
}
