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

data class BundlePlan(
    val id: String,
    val title: String,
    val budgetTier: String,
    val targetBudget: Double?,
    val totalPrice: Double,
    val budgetStatus: String,
    val budgetDelta: Double?,
    val recommendationLevel: String,
    val scenarioFit: String?,
    val summary: String?,
    val completeness: BundleCompleteness,
    val items: List<BundlePlanItem>,
    val tradeoffs: List<String>,
    val compareHighlights: List<String>,
    val exclusionNotes: List<String>,
    val compatibilityChecks: List<BundleCompatibilityCheck>,
    val availabilityStatus: String,
)

data class BundleCompleteness(
    val includedRequired: Int,
    val expectedRequired: Int,
    val optionalIncluded: Int,
    val missing: List<String>,
    val needsConfirmation: List<String>,
)

data class BundlePlanItem(
    val category: String,
    val product: Product,
    val role: String?,
    val required: Boolean,
    val replaceable: Boolean,
    val locked: Boolean,
    val excluded: Boolean,
)

data class BundleCompatibilityCheck(
    val title: String,
    val status: String,
    val message: String,
)

data class BudgetRange(
    val min: Double? = null,
    val max: Double? = null,
)

data class GuidePreferences(
    val budgetPolicy: String = "slightly_flexible",
    val presentationStyle: String = "compare_options",
    val singleItemBudgets: Map<String, BudgetRange> = emptyMap(),
    val bundleBudgetRange: BudgetRange? = null,
    val priorityTags: List<String> = listOf("静音", "耐用"),
    val excludedTags: List<String> = emptyList(),
    val excludedBrands: List<String> = emptyList(),
    val ownedCategories: List<String> = emptyList(),
    val extraNotes: String? = null,
    val hasSavedPreferences: Boolean = false,
)

data class AppliedPreferenceConstraint(
    val type: String,
    val key: String,
    val label: String,
    val effect: String,
)

data class AppliedPreferences(
    val usedSavedPreferences: Boolean = false,
    val ignoredSavedPreferences: Boolean = false,
    val budgetPolicy: String? = null,
    val presentationStyle: String? = null,
    val summary: List<String> = emptyList(),
    val constraints: List<AppliedPreferenceConstraint> = emptyList(),
) {
    val hasVisibleSummary: Boolean
        get() = summary.isNotEmpty() || ignoredSavedPreferences
}

data class CompareRow(
    val title: String,
    val values: List<String>,
)

data class VisionResult(
    val title: String,
    val confidence: Int,
    val labels: List<String>,
    val similarProducts: List<Product>,
    val fallbackUsed: Boolean = false,
)

data class CartItem(
    val id: String,
    val productId: String,
    val quantity: Int,
    val name: String,
    val unitPrice: Double,
    val lineTotal: Double,
    val imageUrl: String? = null,
)

data class CartState(
    val items: List<CartItem> = emptyList(),
    val totalQuantity: Int = 0,
    val totalPrice: Double = 0.0,
    val isLoading: Boolean = false,
    val message: String? = null,
    val errorMessage: String? = null,
)

data class Address(
    val id: String,
    val receiverName: String,
    val phone: String,
    val detail: String,
    val isDefault: Boolean,
)

data class CheckoutResult(
    val orderId: String,
    val status: String,
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
    val bundlePlans: List<BundlePlan> = emptyList(),
    val partialReply: String = "",
    val chatDraft: String = "",
    val chatMessages: List<GuideChatMessage> = emptyList(),
    val appliedPreferences: AppliedPreferences = AppliedPreferences(),
    val ignoreSavedPreferences: Boolean = false,
    val isStreaming: Boolean = false,
    val errorMessage: String? = null,
    val sessionId: String? = null,
    val compareChatContext: CompareChatContext? = null,
)

data class CompareChatContext(
    val products: List<Product>,
    val summary: String? = null,
    val winnerId: String? = null,
    val userNeed: String? = null,
    val sessionId: String? = null,
)

enum class GuideChatRole {
    USER,
    ASSISTANT,
    SYSTEM,
}

data class GuideChatMessage(
    val id: String,
    val role: GuideChatRole,
    val text: String,
    val recommendations: List<Recommendation> = emptyList(),
    val bundlePlans: List<BundlePlan> = emptyList(),
    val appliedPreferences: AppliedPreferences = AppliedPreferences(),
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
            return copy(message = "最多对比 4 件，先移除一个再添加")
        }
        val nextNeed = if (products.isEmpty()) userNeed?.takeIf { it.isNotBlank() } else this.userNeed
        val nextProducts = products + product
        val nextMessage = if (nextProducts.size < 2) {
            "已选入对比，再选 1 件即可开始"
        } else {
            "已选入对比，可开始比较"
        }
        return copy(products = nextProducts, userNeed = nextNeed, message = nextMessage)
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
    val selectedImageName: String? = null,
)

data class ProductDetailState(
    val product: Product? = null,
    val canRecordPurchase: Boolean = true,
    val tokenRequiredMessage: String? = null,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val orderStatusMessage: String? = null,
    val cartStatusMessage: String? = null,
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

data class AuthTokens(
    val accessToken: String,
    val refreshToken: String,
)

data class AccountState(
    val isLoggedIn: Boolean = false,
    val phoneMasked: String? = null,
    val canUseGuestMode: Boolean = false,
    val phoneInput: String = "",
    val codeInput: String = "",
    val debugOtp: String? = null,
    val guidePreferences: GuidePreferences = GuidePreferences(),
    val preferencesLoading: Boolean = false,
    val preferencesError: String? = null,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
    val statusMessage: String? = null,
)
