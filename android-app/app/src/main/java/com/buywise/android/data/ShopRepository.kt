package com.buywise.android.data

import com.buywise.android.BuildConfig
import java.io.IOException
import okhttp3.OkHttpClient
import okhttp3.sse.EventSource

class ShopRepository(
    private val baseUrl: String = BuildConfig.BUYWISE_API_BASE_URL.trimEnd('/'),
) {
    private val httpClient = OkHttpClient()
    private val betaToken = BuildConfig.BUYWISE_BETA_TOKEN.takeIf { it.isNotBlank() }
    private val uploadToken = betaToken ?: BuildConfig.BUYWISE_UPLOAD_TOKEN.takeIf { it.isNotBlank() }
    private val apiClient = BuyWiseApiClient(httpClient, baseUrl, betaToken, uploadToken)

    val betaCapability: BetaCapability
        get() = apiClient.betaCapability

    val productRepository = ProductRepository(apiClient)
    val guideRepository = GuideRepository(apiClient, httpClient)
    val compareRepository = CompareRepository(apiClient)
    val orderRepository = OrderRepository(apiClient)
    val feedbackRepository = FeedbackRepository(apiClient)
    val uploadRepository = UploadRepository(apiClient)

    fun homeState(): HomeState = HomeState(
        heroTitle = "更快找到适合你的商品",
        heroSubtitle = "连接 BuyWise 后端，按预算、场景和偏好生成导购建议。",
        products = emptyList(),
        canUseFeedback = betaCapability.canUseUserFeatures,
        tokenRequiredMessage = betaCapability.message,
    )

    fun guideState(query: String): GuideState = GuideState(
        query = query,
        intentSummary = "输入预算、使用场景和偏好后，BuyWise 会从后端生成推荐。",
        recommendations = emptyList(),
    )

    fun compareState(): CompareState = CompareState(products = emptyList(), rows = emptyList())

    fun visionState(): VisionState = VisionState(
        result = VisionResult(
            title = "后端多模态联调",
            confidence = 0,
            labels = listOf("等待联调"),
            similarProducts = emptyList(),
        ),
    )

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
        onEvent: (ChatStreamEvent) -> Unit,
    ): EventSource =
        guideRepository.streamGuide(query, sessionId, onEvent)
}
