package com.buywise.android.data

import java.io.IOException
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject

class CartRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
) {
    val capability: BetaCapability
        get() = apiClient.betaCapability

    @Throws(IOException::class)
    fun fetchCart(): CartState =
        parseCart(apiClient.getJson("/api/v1/cart", requireAuth = true))

    @Throws(IOException::class)
    fun addProduct(product: Product, quantity: Int = 1, sessionId: String? = null): CartState {
        val body = JSONObject()
            .put("product_id", product.id.toInt())
            .put("quantity", quantity)
            .put("source_session_id", sessionId)
            .put("source_label", product.name)
            .toString()
            .toRequestBody(mediaType("application/json; charset=utf-8"))
        return parseCart(apiClient.postJson("/api/v1/cart/items", body, requireAuth = true))
    }

    @Throws(IOException::class)
    fun updateQuantity(item: CartItem, quantity: Int): CartState {
        val body = JSONObject()
            .put("quantity", quantity.coerceIn(1, 99))
            .toString()
            .toRequestBody(mediaType("application/json; charset=utf-8"))
        return parseCart(apiClient.patchJson("/api/v1/cart/items/${item.id}", body, requireAuth = true))
    }

    @Throws(IOException::class)
    fun removeItem(item: CartItem): CartState {
        apiClient.delete("/api/v1/cart/items/${item.id}", requireAuth = true)
        return fetchCart()
    }

    @Throws(IOException::class)
    fun createDefaultAddress(receiverName: String, phone: String, detail: String): Address {
        val body = JSONObject()
            .put("receiver_name", receiverName)
            .put("phone", phone)
            .put("detail", detail)
            .put("is_default", true)
            .toString()
            .toRequestBody(mediaType("application/json; charset=utf-8"))
        return parseAddress(apiClient.postJson("/api/v1/addresses", body, requireAuth = true))
    }

    @Throws(IOException::class)
    fun checkout(sessionId: String? = null): CheckoutResult {
        val body = JSONObject()
            .put("use_default_address", true)
            .put("source_session_id", sessionId)
            .toString()
            .toRequestBody(mediaType("application/json; charset=utf-8"))
        return parseCheckout(apiClient.postJson("/api/v1/cart/checkout", body, requireAuth = true))
    }
}
