package com.buywise.android.viewmodel

import android.os.Handler
import android.os.Looper
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.buywise.android.data.ChatStreamEvent
import com.buywise.android.data.CompareBasketState
import com.buywise.android.data.CompareState
import com.buywise.android.data.FeedbackPrompt
import com.buywise.android.data.GuideState
import com.buywise.android.data.HomeState
import com.buywise.android.data.Product
import com.buywise.android.data.ProductDetailState
import com.buywise.android.data.ShopRepository
import com.buywise.android.data.VisionState
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import okhttp3.sse.EventSource

class BuyWiseViewModel(
    private val repository: ShopRepository = ShopRepository(),
) : ViewModel() {
    private val mainHandler = Handler(Looper.getMainLooper())
    private var guideStream: EventSource? = null

    var homeState by mutableStateOf(repository.homeState())
        private set

    var compareState by mutableStateOf(repository.compareState())
        private set

    var compareBasketState by mutableStateOf(CompareBasketState())
        private set

    var visionState by mutableStateOf(repository.visionState())
        private set

    var guideState by mutableStateOf(repository.guideState(""))
        private set

    var productDetailState by mutableStateOf(ProductDetailState())
        private set

    init {
        loadHomeProducts()
    }

    fun loadHomeProducts() {
        viewModelScope.launch {
            homeState = homeState.copy(isLoading = true, errorMessage = null)
            runCatching {
                withContext(Dispatchers.IO) { repository.fetchProducts() }
            }.onSuccess { products ->
                homeState = homeState.copy(products = products, isLoading = false)
                loadCompare(products.take(3).map { it.id })
                refreshFeedbackPrompts()
            }.onFailure { throwable ->
                homeState = homeState.copy(
                    products = emptyList(),
                    isLoading = false,
                    errorMessage = throwable.userMessage("商品列表加载失败"),
                )
                compareState = compareState.copy(
                    products = emptyList(),
                    rows = emptyList(),
                    isLoading = false,
                    errorMessage = "商品列表加载失败，暂时无法生成对比。",
                )
            }
        }
    }

    fun loadCompare(productIds: List<String>, userNeed: String? = null) {
        viewModelScope.launch {
            if (productIds.size < 2) {
                compareState = CompareState(
                    products = emptyList(),
                    rows = emptyList(),
                    errorMessage = "至少需要 2 个商品才能对比。",
                )
                return@launch
            }
            compareState = compareState.copy(isLoading = true, errorMessage = null)
            runCatching {
                withContext(Dispatchers.IO) { repository.compareProducts(productIds, userNeed) }
            }.onSuccess { state ->
                compareState = state.copy(isLoading = false)
            }.onFailure { throwable ->
                compareState = compareState.copy(
                    isLoading = false,
                    errorMessage = throwable.userMessage("商品对比加载失败"),
                )
            }
        }
    }

    fun toggleCompareBasket(product: Product, userNeed: String? = null) {
        compareBasketState = compareBasketState.toggle(product, userNeed)
    }

    fun setCompareBasketExpanded(isExpanded: Boolean) {
        compareBasketState = compareBasketState.copy(isExpanded = isExpanded)
    }

    fun clearCompareBasket() {
        compareBasketState = CompareBasketState()
    }

    fun clearCompareBasketMessage() {
        compareBasketState = compareBasketState.copy(message = null)
    }

    fun isInCompareBasket(productId: String): Boolean =
        compareBasketState.products.any { it.id == productId }

    fun startCompareFromBasket(): Boolean {
        if (compareBasketState.products.size < 2) {
            compareBasketState = compareBasketState.copy(message = "至少选择 2 个商品才能对比")
            return false
        }
        loadCompare(compareBasketState.products.map { it.id }, compareBasketState.userNeed)
        compareBasketState = compareBasketState.copy(isExpanded = false, message = null)
        return true
    }

    fun loadProductDetail(productId: String?) {
        if (productId.isNullOrBlank()) {
            productDetailState = ProductDetailState(errorMessage = "商品 ID 无效。")
            return
        }
        productDetailState = ProductDetailState(product = cachedProduct(productId), isLoading = true)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.fetchProductDetail(productId) }
            }.onSuccess { product ->
                productDetailState = ProductDetailState(product = product, isLoading = false)
            }.onFailure { throwable ->
                productDetailState = productDetailState.copy(
                    isLoading = false,
                    errorMessage = throwable.userMessage("商品详情加载失败"),
                )
            }
        }
    }

    fun recordPurchase(productId: String) {
        productDetailState = productDetailState.copy(isLoading = true, errorMessage = null, orderStatusMessage = null)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.recordPurchase(productId) }
            }.onSuccess { status ->
                productDetailState = productDetailState.copy(
                    isLoading = false,
                    orderStatusMessage = if (status == "delivered") "已记录购买并模拟收货，达到反馈时间后会出现在首页。" else "已记录购买：$status",
                )
                refreshFeedbackPrompts()
            }.onFailure { throwable ->
                productDetailState = productDetailState.copy(
                    isLoading = false,
                    errorMessage = throwable.userMessage("购买记录创建失败"),
                )
            }
        }
    }

    fun refreshFeedbackPrompts() {
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.fetchFeedbackPrompts() }
            }.onSuccess { prompts ->
                homeState = homeState.copy(feedbackPrompts = prompts)
            }
        }
    }

    fun submitFeedback(prompt: FeedbackPrompt) {
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.submitFeedback(prompt) }
            }.onSuccess {
                homeState = homeState.copy(
                    feedbackPrompts = homeState.feedbackPrompts.filterNot { it.orderItemId == prompt.orderItemId },
                )
            }.onFailure { throwable ->
                homeState = homeState.copy(errorMessage = throwable.userMessage("评价提交失败"))
            }
        }
    }

    fun updateGuideQuery(query: String) {
        guideState = guideState.copy(query = query)
    }

    fun submitGuideQuery() {
        val query = guideState.query.ifBlank { "300 元以内，适合宿舍写代码的低噪音机械键盘" }
        guideStream?.cancel()
        guideState = guideState.copy(
            query = query,
            intentSummary = "正在连接 BuyWise 后端...",
            recommendations = emptyList(),
            partialReply = "",
            isStreaming = true,
            errorMessage = null,
        )
        guideStream = repository.streamGuide(
            query = query,
            sessionId = guideState.sessionId,
            onEvent = { event ->
                mainHandler.post { applyChatEvent(event) }
            },
        )
    }

    fun runVisionDemo() {
        visionState = visionState.copy(isLoading = true, errorMessage = null)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.runVisionDemo() }
            }.onSuccess { result ->
                visionState = visionState.copy(
                    result = result,
                    recognizedQuery = result.title,
                    isLoading = false,
                )
            }.onFailure { throwable ->
                visionState = visionState.copy(
                    isLoading = false,
                    errorMessage = throwable.userMessage("图像识别联调失败"),
                )
            }
        }
    }

    fun runSpeechDemo() {
        visionState = visionState.copy(isLoading = true, errorMessage = null)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.runSpeechDemo() }
            }.onSuccess { text ->
                visionState = visionState.copy(
                    speechText = text,
                    recognizedQuery = text,
                    isLoading = false,
                )
            }.onFailure { throwable ->
                visionState = visionState.copy(
                    isLoading = false,
                    errorMessage = throwable.userMessage("语音识别联调失败"),
                )
            }
        }
    }

    fun useVisionQueryInGuide() {
        val query = visionState.recognizedQuery ?: visionState.speechText ?: return
        updateGuideQuery(query)
    }

    fun product(productId: String?): Product? =
        productDetailState.product?.takeIf { it.id == productId } ?: cachedProduct(productId)

    override fun onCleared() {
        guideStream?.cancel()
        super.onCleared()
    }

    private fun cachedProduct(productId: String?): Product? =
        homeState.products.firstOrNull { it.id == productId }
            ?: guideState.recommendations.firstOrNull { it.product.id == productId }?.product
            ?: compareState.products.firstOrNull { it.id == productId }
            ?: visionState.result.similarProducts.firstOrNull { it.id == productId }

    private fun applyChatEvent(event: ChatStreamEvent) {
        guideState = when (event) {
            is ChatStreamEvent.Meta -> guideState.copy(sessionId = event.sessionId)
            is ChatStreamEvent.Status -> guideState.copy(intentSummary = event.message)
            is ChatStreamEvent.Token -> guideState.copy(partialReply = guideState.partialReply + event.text)
            is ChatStreamEvent.Products -> guideState.copy(
                intentSummary = event.intentSummary,
                recommendations = event.recommendations,
            )
            is ChatStreamEvent.Done -> guideState.copy(
                partialReply = event.reply.ifBlank { guideState.partialReply },
                isStreaming = false,
            )
            is ChatStreamEvent.Error -> guideState.copy(
                errorMessage = event.message,
                isStreaming = false,
            )
        }
    }

    private fun Throwable.userMessage(prefix: String): String =
        message?.takeIf { it.isNotBlank() }?.let { "$prefix：$it" } ?: prefix
}
