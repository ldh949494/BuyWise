package com.buywise.android.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import android.content.Context
import com.buywise.android.data.CompareBasketState
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
    private val guideViewModel = GuideViewModel.from(repository)
    private val compareViewModel = CompareViewModel.from(repository)
    private val productDetailViewModel = ProductDetailViewModel.from(repository)
    private val feedbackViewModel = FeedbackViewModel.from(repository)
    private val uploadViewModel = UploadViewModel.from(repository)
    private val accountViewModel = AccountViewModel(repository.authRepository, viewModelScope)

    val homeState: HomeState get() = homeViewModel.state
    val compareState: CompareState get() = compareViewModel.state
    val compareBasketState: CompareBasketState get() = compareViewModel.basketState
    val visionState: VisionState get() = uploadViewModel.state
    val guideState: GuideState get() = guideViewModel.state
    val productDetailState: ProductDetailState get() = productDetailViewModel.state
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

    fun submitGuideQuery() {
        guideViewModel.submitQuery()
    }

    fun sendGuideChatMessage() {
        guideViewModel.sendChatMessage()
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

    fun product(productId: String?): Product? =
        productDetailState.product?.takeIf { it.id == productId } ?: cachedProduct(productId)

    override fun onCleared() {
        homeViewModel.clear()
        guideViewModel.clear()
        compareViewModel.clear()
        productDetailViewModel.clear()
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
