package com.buywise.android.data

import android.content.Context
import com.buywise.android.BuildConfig
import java.io.IOException
import okhttp3.OkHttpClient
import okhttp3.sse.EventSource

class ShopRepository(
    private val baseUrl: String = BuildConfig.BUYWISE_API_BASE_URL.trimEnd('/'),
    context: Context? = null,
) {
    private val httpClient = OkHttpClient()
    private val betaToken = BuildConfig.BUYWISE_BETA_TOKEN.takeIf { it.isNotBlank() }
    private val uploadToken = betaToken ?: BuildConfig.BUYWISE_UPLOAD_TOKEN.takeIf { it.isNotBlank() }
    private val apiClient = BuyWiseApiClient(httpClient, baseUrl, betaToken, uploadToken)
    private val tokenStore = context?.let { AuthTokenStore(it) }

    val betaCapability: BetaCapability
        get() = apiClient.betaCapability

    val productRepository = ProductRepository(apiClient)
    val guideRepository = GuideRepository(apiClient, httpClient)
    val guidePreferencesRepository = GuidePreferencesRepository(apiClient)
    val compareRepository = CompareRepository(apiClient)
    val orderRepository = OrderRepository(apiClient)
    val cartRepository = CartRepository(apiClient)
    val feedbackRepository = FeedbackRepository(apiClient)
    val uploadRepository = UploadRepository(apiClient)
    val authRepository: AuthRepository? = tokenStore?.let { AuthRepository(apiClient, it) }

    fun homeState(): HomeState = HomeState(
        heroTitle = "AI 智能购物决策助手",
        heroSubtitle = "告诉我预算、场景和偏好，我帮你找到更适合的商品。",
        products = emptyList(),
        canUseFeedback = betaCapability.canUseUserFeatures,
        tokenRequiredMessage = betaCapability.message,
    )

    fun guideState(query: String): GuideState = GuideState(
        query = query,
        intentSummary = "",
        recommendations = emptyList(),
    )

    fun compareState(): CompareState = CompareState(products = emptyList(), rows = emptyList())

    fun cartState(): CartState = CartState()

    fun visionState(): VisionState = VisionState(result = VisionResult.Empty)

    @Throws(IOException::class)
    fun runVisionDemo(): VisionResult = uploadRepository.runVisionDemo()

    @Throws(IOException::class)
    fun runSpeechDemo(): String = uploadRepository.runSpeechDemo()

    @Throws(IOException::class)
    fun fetchProducts(page: Int = 1, pageSize: Int = 20): List<Product> =
        productRepository.fetchProducts(page, pageSize)

    @Throws(IOException::class)
    fun fetchProductDetail(productId: String): Product =
        productRepository.fetchProductDetail(productId)

    @Throws(IOException::class)
    fun recordPurchase(productId: String): String =
        orderRepository.recordPurchase(productId)

    @Throws(IOException::class)
    fun addProductToCart(product: Product, sessionId: String? = null): CartState =
        cartRepository.addProduct(product, sessionId = sessionId)

    @Throws(IOException::class)
    fun fetchFeedbackPrompts(): List<FeedbackPrompt> =
        feedbackRepository.fetchFeedbackPrompts()

    @Throws(IOException::class)
    fun submitFeedback(prompt: FeedbackPrompt, draft: FeedbackDraft = FeedbackDraft()) {
        feedbackRepository.submitFeedback(prompt, draft)
    }

    @Throws(IOException::class)
    fun compareProducts(productIds: List<String>, userNeed: String? = null): CompareState =
        compareRepository.compareProducts(productIds, userNeed)

    fun streamGuide(
        query: String,
        sessionId: String?,
        ignoreSavedPreferences: Boolean = false,
        onEvent: (ChatStreamEvent) -> Unit,
    ): EventSource =
        guideRepository.streamGuide(query, sessionId, ignoreSavedPreferences, onEvent)

    fun streamGuideFollowUp(
        query: String,
        sessionId: String?,
        ignoreSavedPreferences: Boolean = false,
        onEvent: (ChatStreamEvent) -> Unit,
    ): EventSource =
        guideRepository.streamGuideFollowUp(query, sessionId, ignoreSavedPreferences, onEvent)

    fun streamCompareFollowUp(
        query: String,
        context: CompareChatContext,
        onEvent: (ChatStreamEvent) -> Unit,
    ): EventSource =
        guideRepository.streamCompareFollowUp(query, context, onEvent)
}
