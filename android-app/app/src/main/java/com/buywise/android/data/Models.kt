package com.buywise.android.data

data class Product(
    val id: String,
    val name: String,
    val brand: String?,
    val category: String?,
    val price: Double?,
    val rating: Double?,
    val recommendationScore: Double? = null,
    val headline: String,
    val tags: List<String>,
    val advantages: List<String>,
    val cautions: List<String>,
    val imageUrl: String? = null,
    val productUrl: String? = null,
    val stockStatus: String? = null,
    val reviewSummary: String? = null,
)

data class Recommendation(
    val product: Product,
    val reason: String,
)

data class CompareRow(
    val title: String,
    val values: List<String>,
)

data class VisionResult(
    val title: String,
    val confidence: Int,
    val labels: List<String>,
    val similarProducts: List<Product>,
)

data class HomeState(
    val heroTitle: String,
    val heroSubtitle: String,
    val products: List<Product>,
    val feedbackPrompts: List<FeedbackPrompt> = emptyList(),
    val canUseFeedback: Boolean = true,
    val tokenRequiredMessage: String? = null,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
)

data class GuideState(
    val query: String,
    val intentSummary: String,
    val recommendations: List<Recommendation>,
    val partialReply: String = "",
    val isStreaming: Boolean = false,
    val errorMessage: String? = null,
    val sessionId: String? = null,
)

data class CompareState(
    val products: List<Product>,
    val rows: List<CompareRow>,
    val summary: String? = null,
    val winnerId: String? = null,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
)

data class CompareBasketState(
    val products: List<Product> = emptyList(),
    val userNeed: String? = null,
    val isExpanded: Boolean = false,
    val message: String? = null,
) {
    val hasMixedCategories: Boolean
        get() = products.mapNotNull { it.category?.takeIf(String::isNotBlank) }.distinct().size > 1

    fun toggle(product: Product, userNeed: String? = null): CompareBasketState {
        if (product.id.toIntOrNull() == null) {
            return copy(message = "该商品暂时无法加入对比")
        }
        if (products.any { it.id == product.id }) {
            return copy(products = products.filterNot { it.id == product.id }, message = null)
        }
        if (products.size >= MAX_PRODUCTS) {
            return copy(message = "最多选择 4 个商品")
        }
        val nextNeed = if (products.isEmpty()) userNeed?.takeIf { it.isNotBlank() } else this.userNeed
        return copy(products = products + product, userNeed = nextNeed, message = null)
    }

    companion object {
        const val MAX_PRODUCTS = 4
    }
}

data class VisionState(
    val result: VisionResult,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val recognizedQuery: String? = null,
    val speechText: String? = null,
)

data class ProductDetailState(
    val product: Product? = null,
    val canRecordPurchase: Boolean = true,
    val tokenRequiredMessage: String? = null,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val orderStatusMessage: String? = null,
)

data class FeedbackPrompt(
    val orderId: String,
    val orderItemId: String,
    val productId: String,
    val productName: String,
)

data class FeedbackDraft(
    val rating: Int = 5,
    val content: String = "",
    val prosTags: List<String> = emptyList(),
    val consTags: List<String> = emptyList(),
    val metExpectation: Boolean = true,
)

data class FeedbackUiState(
    val activePromptId: String? = null,
    val drafts: Map<String, FeedbackDraft> = emptyMap(),
    val submittingIds: Set<String> = emptySet(),
    val submitErrors: Map<String, String> = emptyMap(),
    val successMessage: String? = null,
    val canUseFeedback: Boolean = true,
    val tokenRequiredMessage: String? = null,
) {
    fun draftFor(prompt: FeedbackPrompt): FeedbackDraft =
        drafts[prompt.orderItemId] ?: FeedbackDraft()
}

data class BetaCapability(
    val canUseUserFeatures: Boolean,
    val message: String? = null,
) {
    companion object {
        val Enabled = BetaCapability(canUseUserFeatures = true)
        const val TOKEN_REQUIRED_MESSAGE = "购买后反馈功能暂未开启。"
        const val DEBUG_TOKEN_REQUIRED_MESSAGE = "当前构建未配置 BUYWISE_BETA_TOKEN，无法记录购买或提交反馈。"
    }
}
