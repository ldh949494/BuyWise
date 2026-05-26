package com.buywise.android.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.buywise.android.data.HomeState
import com.buywise.android.data.ProductRepository
import com.buywise.android.data.ShopRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class HomeViewModel(
    private val repository: ProductRepository,
    initialState: HomeState,
) : ViewModel() {
    var state by mutableStateOf(initialState)
        private set

    fun loadProducts(onLoaded: (List<com.buywise.android.data.Product>) -> Unit = {}) {
        viewModelScope.launch {
            state = state.copy(isLoading = true, errorMessage = null)
            runCatching {
                withContext(Dispatchers.IO) { repository.fetchProducts() }
            }.onSuccess { products ->
                state = state.copy(products = products, isLoading = false)
                onLoaded(products)
            }.onFailure { throwable ->
                state = state.copy(
                    products = emptyList(),
                    isLoading = false,
                    errorMessage = throwable.userMessage("商品列表加载失败"),
                )
            }
        }
    }

    fun setFeedbackPrompts(prompts: List<com.buywise.android.data.FeedbackPrompt>) {
        state = state.copy(feedbackPrompts = prompts)
    }

    fun removeFeedbackPrompt(orderItemId: String) {
        state = state.copy(feedbackPrompts = state.feedbackPrompts.filterNot { it.orderItemId == orderItemId })
    }

    fun setError(message: String?) {
        state = state.copy(errorMessage = message)
    }

    fun clear() {
        onCleared()
    }

    companion object {
        fun from(shopRepository: ShopRepository): HomeViewModel =
            HomeViewModel(shopRepository.productRepository, shopRepository.homeState())
    }
}
