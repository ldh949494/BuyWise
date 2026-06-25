package com.buywise.android.data

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class ProductListResponseDto(
    val items: List<ProductDto> = emptyList(),
)

@Serializable
data class ProductDto(
    val id: Int,
    val name: String = "未命名商品",
    val brand: String? = null,
    val category: String? = null,
    val platform: String? = null,
    val price: Double? = null,
    val rating: Double? = null,
    val description: String? = null,
    val tags: List<String> = emptyList(),
    @SerialName("suitable_scene") val suitableScene: List<String> = emptyList(),
    @SerialName("image_url") val imageUrl: String? = null,
    @SerialName("product_url") val productUrl: String? = null,
    @SerialName("stock_status") val stockStatus: String? = null,
    @SerialName("review_summary") val reviewSummary: String? = null,
)

@Serializable
data class ProductCardDto(
    val id: Int,
    val name: String = "未命名商品",
    val price: Double? = null,
    val rating: Double? = null,
    val score: Double? = null,
    val reason: String? = null,
    val description: String? = null,
    val tags: List<String> = emptyList(),
    val conflicts: List<String> = emptyList(),
    @SerialName("image_url") val imageUrl: String? = null,
)

@Serializable
data class CompareRequestDto(
    @SerialName("product_ids") val productIds: List<Int>,
    @SerialName("user_need") val userNeed: String,
)

@Serializable
data class CompareResponseDto(
    val items: List<CompareItemDto> = emptyList(),
    val summary: String? = null,
    @SerialName("winner_id") val winnerId: Int? = null,
)

@Serializable
data class CompareItemDto(
    val id: Int? = null,
    @SerialName("product_id") val productId: Int? = null,
    val name: String = "未命名商品",
    val price: Double? = null,
    val rating: Double? = null,
    val score: Double? = null,
    val pros: List<String> = emptyList(),
    val cons: List<String> = emptyList(),
    @SerialName("image_url") val imageUrl: String? = null,
)

@Serializable
data class CompareFollowUpProductDto(
    val id: Int,
    @SerialName("product_id") val productId: Int,
    val name: String,
    val price: Double? = null,
    val rating: Double? = null,
    val score: Double? = null,
    val pros: List<String> = emptyList(),
    val cons: List<String> = emptyList(),
)

@Serializable
data class CompareFollowUpRequestDto(
    val message: String,
    val items: List<CompareFollowUpProductDto>,
    val summary: String? = null,
    @SerialName("winner_id") val winnerId: Int? = null,
    @SerialName("user_need") val userNeed: String? = null,
    @SerialName("session_id") val sessionId: String? = null,
)

@Serializable
data class OrderCreateRequestDto(
    @SerialName("product_id") val productId: Int,
    val quantity: Int = 1,
)

@Serializable
data class OrderResponseDto(
    val id: Int,
    @SerialName("fulfillment_status") val fulfillmentStatus: String? = null,
)

@Serializable
data class CartItemAddRequestDto(
    @SerialName("product_id") val productId: Int,
    val quantity: Int = 1,
    @SerialName("source_session_id") val sourceSessionId: String? = null,
    @SerialName("source_label") val sourceLabel: String? = null,
)

@Serializable
data class CartItemUpdateRequestDto(
    val quantity: Int,
)

@Serializable
data class CheckoutRequestDto(
    @SerialName("use_default_address") val useDefaultAddress: Boolean = true,
    @SerialName("source_session_id") val sourceSessionId: String? = null,
)

@Serializable
data class CheckoutResponseDto(
    @SerialName("checkout_session_id") val checkoutSessionId: Int,
    val order: OrderResponseDto,
)

@Serializable
data class AddressCreateRequestDto(
    @SerialName("receiver_name") val receiverName: String,
    val phone: String,
    val detail: String,
    @SerialName("is_default") val isDefault: Boolean = true,
)

@Serializable
data class FeedbackPromptListResponseDto(
    val items: List<FeedbackPromptDto> = emptyList(),
)

@Serializable
data class FeedbackPromptDto(
    @SerialName("order_id") val orderId: Int,
    @SerialName("order_item_id") val orderItemId: Int,
    @SerialName("product_id") val productId: Int,
    @SerialName("product_name") val productName: String = "已购商品",
)

@Serializable
data class FeedbackSubmitRequestDto(
    @SerialName("order_item_id") val orderItemId: Int,
    val rating: Int,
    val content: String,
    @SerialName("pros_tags") val prosTags: List<String>,
    @SerialName("cons_tags") val consTags: List<String>,
    @SerialName("met_expectation") val metExpectation: Boolean,
)

@Serializable
data class GuideStreamRequestDto(
    @SerialName("session_id") val sessionId: String? = null,
    @SerialName("session_token") val sessionToken: String? = null,
    val message: String,
    @SerialName("ignore_saved_preferences") val ignoreSavedPreferences: Boolean = false,
)

@Serializable
data class EmptyRequestDto(val value: String? = null)

@Serializable
data class GuideSessionCreateResponseDto(
    @SerialName("session_id") val sessionId: String,
    @SerialName("session_token") val sessionToken: String? = null,
)

@Serializable
data class GuideSessionListResponseDto(
    val items: List<GuideSessionSummaryDto> = emptyList(),
)

@Serializable
data class GuideSessionSummaryDto(
    @SerialName("session_id") val sessionId: String,
    val title: String? = null,
    @SerialName("updated_at") val updatedAt: String? = null,
    @SerialName("created_at") val createdAt: String? = null,
    @SerialName("last_message") val lastMessage: String? = null,
)

@Serializable
data class VisionRequestDto(
    @SerialName("image_url") val imageUrl: String,
)

@Serializable
data class VisionResponseDto(
    val category: String? = null,
    val features: List<String> = emptyList(),
    val query: String? = null,
    val colors: List<String> = emptyList(),
    val materials: List<String> = emptyList(),
    val shape: String? = null,
    val style: String? = null,
    @SerialName("brand_cues") val brandCues: List<String> = emptyList(),
    val confidence: Double? = null,
    @SerialName("detected_objects") val detectedObjects: List<String> = emptyList(),
)

@Serializable
data class VisualSearchRequestDto(
    @SerialName("image_url") val imageUrl: String,
    val message: String? = null,
    @SerialName("top_k") val topK: Int = 8,
)

@Serializable
data class VisualSearchResponseDto(
    val recognized: VisionResponseDto,
    val products: List<ProductCardDto> = emptyList(),
    @SerialName("fallback_used") val fallbackUsed: Boolean = false,
)

@Serializable
data class SpeechRequestDto(
    @SerialName("audio_url") val audioUrl: String,
)

@Serializable
data class SpeechResponseDto(
    val text: String = "",
)

@Serializable
data class OtpRequestDto(
    @SerialName("phone") val phone: String,
)

@Serializable
data class OtpRequestResponseDto(
    @SerialName("phone_masked") val phoneMasked: String,
    @SerialName("debug_otp") val debugOtp: String? = null,
)

@Serializable
data class OtpVerifyRequestDto(
    @SerialName("phone") val phone: String,
    @SerialName("code") val code: String,
    @SerialName("device_name") val deviceName: String? = null,
)

@Serializable
data class AuthUser(
    @SerialName("id") val id: Int,
    @SerialName("phone_masked") val phoneMasked: String,
)

@Serializable
data class AuthTokenResponseDto(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
    @SerialName("expires_in") val expiresIn: Int,
    @SerialName("user") val user: AuthUser,
) {
    fun toTokens(): AuthTokens = AuthTokens(accessToken, refreshToken)
}

@Serializable
data class RefreshRequestDto(
    @SerialName("refresh_token") val refreshToken: String,
)

@Serializable
data class RefreshResponseDto(
    @SerialName("access_token") val accessToken: String,
    @SerialName("refresh_token") val refreshToken: String,
) {
    fun toTokens(): AuthTokens = AuthTokens(accessToken, refreshToken)
}

@Serializable
data class LogoutRequestDto(
    @SerialName("refresh_token") val refreshToken: String,
)
