package com.buywise.android.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import android.content.Context
import com.buywise.android.data.CartItem
import com.buywise.android.data.CartState
import com.buywise.android.data.CompareBasketState
import com.buywise.android.data.CompareChatContext
import com.buywise.android.data.CompareState
import com.buywise.android.data.FeedbackDraft
import com.buywise.android.data.FeedbackPrompt
import com.buywise.android.data.FeedbackUiState
import com.buywise.android.data.GuideState
import com.buywise.android.data.HomeState
import com.buywise.android.data.Product
import com.buywise.android.data.ProductDetailState
import com.buywise.android.data.ShopRepository
import com.buywise.android.data.VisionState

class BuyWiseViewModel(
    private val repository: ShopRepository = ShopRepository(),
) : ViewModel() {
    private val homeViewModel = HomeViewModel.from(repository)
    private val compareViewModel = CompareViewModel.from(repository)
    private val productDetailViewModel = ProductDetailViewModel.from(repository)
    private val cartViewModel = CartViewModel.from(repository)
    private val guideViewModel = GuideViewModel(
        repository.guideRepository,
        repository.guideSessionStore,
        repository.guideState(""),
        onCartUpdated = { cart, message -> cartViewModel.applyServerCart(cart, message) },
        onCartRefreshRequested = { cartViewModel.refresh() },
    )
    private val feedbackViewModel = FeedbackViewModel.from(repository)
    private val uploadViewModel = UploadViewModel.from(repository)
    private val accountViewModel = AccountViewModel(repository.authRepository, repository.guidePreferencesRepository, viewModelScope)

    val homeState: HomeState get() = homeViewModel.state
    val compareState: CompareState get() = compareViewModel.state
    val compareBasketState: CompareBasketState get() = compareViewModel.basketState
    val visionState: VisionState get() = uploadViewModel.state
    val guideState: GuideState get() = guideViewModel.state
    val productDetailState: ProductDetailState get() = productDetailViewModel.state
    val cartState: CartState get() = cartViewModel.state
    val feedbackState: FeedbackUiState get() = feedbackViewModel.state
    val accountState get() = accountViewModel.state

    init {
        accountViewModel.restoreSession()
        loadHomeProducts()
    }

    fun loadHomeProducts() {
        homeViewModel.loadProducts { products ->
            refreshFeedbackPrompts()
        }
    }

    fun loadCompare(productIds: List<String>, userNeed: String? = null) {
        compareViewModel.loadCompare(productIds, userNeed)
    }

    fun refreshCompare() {
        compareViewModel.refresh()
    }

    fun toggleCompareBasket(product: Product, userNeed: String? = null) {
        compareViewModel.toggleBasket(product, userNeed)
    }

    fun setCompareBasketExpanded(isExpanded: Boolean) {
        compareViewModel.setBasketExpanded(isExpanded)
    }

    fun clearCompareBasket() {
        compareViewModel.clearBasket()
    }

    fun clearCompareBasketMessage() {
        compareViewModel.clearBasketMessage()
    }

    fun isInCompareBasket(productId: String): Boolean =
        compareViewModel.isInBasket(productId)

    fun startCompareFromBasket(): Boolean =
        compareViewModel.startCompareFromBasket()

    fun loadProductDetail(productId: String?) {
        productDetailViewModel.loadProductDetail(productId, cachedProduct(productId))
    }

    fun recordPurchase(productId: String) {
        productDetailViewModel.recordPurchase(productId) { refreshFeedbackPrompts() }
    }

    fun refreshCart() {
        cartViewModel.refresh()
    }

    fun addProductToCart(product: Product) {
        cartViewModel.addProduct(product, guideState.sessionId) { message ->
            productDetailViewModel.setCartStatus(message)
        }
    }

    fun updateCartItemQuantity(item: CartItem, quantity: Int) {
        cartViewModel.updateQuantity(item, quantity)
    }

    fun removeCartItem(item: CartItem) {
        cartViewModel.removeItem(item)
    }

    fun checkoutCart() {
        cartViewModel.checkout(guideState.sessionId) {
            refreshFeedbackPrompts()
        }
    }

    fun clearCartMessage() {
        cartViewModel.clearMessage()
    }

    fun refreshFeedbackPrompts() {
        feedbackViewModel.refreshPrompts { prompts ->
            homeViewModel.setFeedbackPrompts(prompts)
        }
    }

    fun toggleFeedbackForm(prompt: FeedbackPrompt) {
        feedbackViewModel.toggleForm(prompt)
    }

    fun updateFeedbackDraft(prompt: FeedbackPrompt, draft: FeedbackDraft) {
        feedbackViewModel.updateDraft(prompt, draft)
    }

    fun submitFeedback(prompt: FeedbackPrompt) {
        feedbackViewModel.submitFeedback(prompt) {
            homeViewModel.removeFeedbackPrompt(prompt.orderItemId)
        }
    }

    fun updateGuideQuery(query: String) {
        guideViewModel.updateQuery(query)
    }

    fun startGuideFromHome(query: String): Boolean {
        val normalized = query.trim()
        if (normalized.isBlank()) {
            homeViewModel.setError("先输入品类、商品名或需求，再开始导购。")
            return false
        }
        guideViewModel.useQuery(normalized)
        guideViewModel.submitQuery()
        return true
    }

    fun updateGuideChatDraft(draft: String) {
        guideViewModel.updateChatDraft(draft)
    }

    fun appendGuideChatDraft(text: String, sourceLabel: String) {
        guideViewModel.appendChatDraft(text, sourceLabel)
    }

    fun addGuideChatSystemMessage(text: String) {
        guideViewModel.addChatSystemMessage(text)
    }

    fun prepareGuideChatDraft() {
        guideViewModel.prepareChatDraft()
    }

    fun prepareCompareChatDraft() {
        val products = compareState.products.take(4)
        if (products.size < 2) {
            guideViewModel.prepareChatDraft()
            return
        }
        val productNames = products.joinToString("、") { it.name }
        val summary = compareState.summary?.takeIf { it.isNotBlank() }
        val draft = buildString {
            append("继续帮我对比这几个商品：")
            append(productNames)
            append("。我的关注点是价格、风险和真实评价，帮我判断哪个更适合。")
            if (summary != null) {
                append(" 当前对比摘要：")
                append(summary)
            }
        }
        guideViewModel.useCompareChatContext(
            CompareChatContext(
                products = products,
                summary = compareState.summary,
                winnerId = compareState.winnerId,
                userNeed = compareViewModel.basketState.userNeed,
                sessionId = guideState.sessionId,
            ),
            draft,
        )
    }

    fun submitGuideQuery() {
        guideViewModel.submitQuery()
    }

    fun sendGuideChatMessage() {
        guideViewModel.sendChatMessage()
    }

    fun startNewGuideConversation() {
        guideViewModel.startNewConversation()
    }

    fun loadGuideSessionHistory() {
        guideViewModel.loadSessionHistory()
    }

    fun openGuideSession(sessionId: String) {
        guideViewModel.openSession(sessionId)
    }

    fun runPendingGuideRefresh() {
        guideViewModel.runPendingRefresh()
    }

    fun setGuideIgnoreSavedPreferences(value: Boolean) {
        guideViewModel.setIgnoreSavedPreferences(value)
    }

    fun runVisionDemo() {
        uploadViewModel.runVisionDemo()
    }

    fun runVisionDemoForGuideChat() {
        uploadViewModel.runVisionDemo(
            onRecognized = { result -> guideViewModel.appendChatDraft(result.title, "图片") },
            onError = { message -> guideViewModel.addChatSystemMessage(message) },
        )
    }

    fun recognizeImage(filename: String, contentType: String, bytes: ByteArray) {
        uploadViewModel.recognizeImage(filename, contentType, bytes)
    }

    fun recognizeImageForGuideChat(filename: String, contentType: String, bytes: ByteArray) {
        uploadViewModel.recognizeImage(
            filename = filename,
            contentType = contentType,
            bytes = bytes,
            onRecognized = { result -> guideViewModel.appendChatDraft(result.title, "图片") },
            onError = { message -> guideViewModel.addChatSystemMessage(message) },
        )
    }

    fun runSpeechDemo() {
        uploadViewModel.runSpeechDemo()
    }

    fun runSpeechDemoForGuideChat() {
        uploadViewModel.runSpeechDemo(
            onRecognized = { text -> guideViewModel.appendChatDraft(text, "语音") },
            onError = { message -> guideViewModel.addChatSystemMessage(message) },
        )
    }

    fun transcribeAudio(filename: String, contentType: String, bytes: ByteArray) {
        uploadViewModel.transcribeAudio(filename, contentType, bytes)
    }

    fun transcribeAudioForGuideChat(filename: String, contentType: String, bytes: ByteArray) {
        uploadViewModel.transcribeAudio(
            filename = filename,
            contentType = contentType,
            bytes = bytes,
            onRecognized = { text -> guideViewModel.appendChatDraft(text, "语音") },
            onError = { message -> guideViewModel.addChatSystemMessage(message) },
        )
    }

    fun useVisionQueryInGuide() {
        val query = visionState.recognizedQuery ?: visionState.speechText ?: return
        guideViewModel.useQuery(query)
    }

    fun updateAccountPhone(value: String) {
        accountViewModel.updatePhone(value)
    }

    fun updateAccountCode(value: String) {
        accountViewModel.updateCode(value)
    }

    fun requestAccountOtp() {
        accountViewModel.requestOtp()
    }

    fun verifyAccountOtp(onLoggedIn: () -> Unit = {}) {
        accountViewModel.verifyOtp {
            cartViewModel.refresh()
            refreshFeedbackPrompts()
            onLoggedIn()
        }
    }

    fun enterGuestMode(onEntered: () -> Unit = {}) {
        accountViewModel.enterGuestMode(onEntered)
    }

    fun logoutAccount() {
        accountViewModel.logout()
    }

    fun loadGuidePreferences() {
        accountViewModel.loadGuidePreferences()
    }

    fun updateGuideBudgetPolicy(value: String) {
        accountViewModel.updateBudgetPolicy(value)
    }

    fun updateGuidePresentationStyle(value: String) {
        accountViewModel.updatePresentationStyle(value)
    }

    fun toggleGuidePriorityTag(tag: String) {
        accountViewModel.togglePriorityTag(tag)
    }

    fun toggleGuideExcludedTag(tag: String) {
        accountViewModel.toggleExcludedTag(tag)
    }

    fun toggleGuideOwnedCategory(category: String) {
        accountViewModel.toggleOwnedCategory(category)
    }

    fun updateGuideBundleBudgetMax(value: String) {
        accountViewModel.updateBundleBudgetMax(value)
    }

    fun clearGuidePreferences() {
        accountViewModel.clearGuidePreferences()
    }

    fun product(productId: String?): Product? =
        productDetailState.product?.takeIf { it.id == productId } ?: cachedProduct(productId)

    override fun onCleared() {
        homeViewModel.clear()
        guideViewModel.clear()
        compareViewModel.clear()
        productDetailViewModel.clear()
        cartViewModel.clear()
        feedbackViewModel.clear()
        uploadViewModel.clear()
        super.onCleared()
    }

    private fun cachedProduct(productId: String?): Product? =
        homeState.products.firstOrNull { it.id == productId }
            ?: guideState.recommendations.firstOrNull { it.product.id == productId }?.product
            ?: compareState.products.firstOrNull { it.id == productId }
            ?: uploadViewModel.product(productId)

    companion object {
        fun factory(context: Context): ViewModelProvider.Factory =
            object : ViewModelProvider.Factory {
                @Suppress("UNCHECKED_CAST")
                override fun <T : ViewModel> create(modelClass: Class<T>): T =
                    BuyWiseViewModel(ShopRepository(context = context.applicationContext)) as T
            }
    }
}
