package com.buywise.android.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.buywise.android.data.CompareBasketState
import com.buywise.android.data.CompareRepository
import com.buywise.android.data.CompareState
import com.buywise.android.data.Product
import com.buywise.android.data.ShopRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class CompareViewModel(
    private val repository: CompareRepository,
    initialState: CompareState,
) : ViewModel() {
    var state by mutableStateOf(initialState)
        private set

    var basketState by mutableStateOf(CompareBasketState())
        private set

    private var lastProductIds: List<String> = emptyList()
    private var lastUserNeed: String? = null

    fun loadCompare(productIds: List<String>, userNeed: String? = null) {
        viewModelScope.launch {
            val validIds = productIds.filter { it.toIntOrNull() != null }.distinct()
            if (validIds.size < 2) {
                state = CompareState(products = emptyList(), rows = emptyList(), errorMessage = "至少需要 2 个商品才能对比。")
                return@launch
            }
            lastProductIds = validIds
            lastUserNeed = userNeed
            state = state.copy(isLoading = true, errorMessage = null)
            runCatching {
                withContext(Dispatchers.IO) { repository.compareProducts(validIds, userNeed) }
            }.onSuccess { next ->
                state = next.copy(isLoading = false)
            }.onFailure { throwable ->
                state = state.copy(isLoading = false, errorMessage = throwable.userMessage("商品对比加载失败"))
            }
        }
    }

    fun refresh() {
        if (lastProductIds.size < 2) {
            state = state.copy(errorMessage = "请先选择至少 2 个商品进行对比。")
            return
        }
        loadCompare(lastProductIds, lastUserNeed)
    }

    fun toggleBasket(product: Product, userNeed: String? = null) {
        basketState = basketState.toggle(product, userNeed)
    }

    fun setBasketExpanded(isExpanded: Boolean) {
        basketState = basketState.copy(isExpanded = isExpanded)
    }

    fun clearBasket() {
        basketState = CompareBasketState()
    }

    fun clearBasketMessage() {
        basketState = basketState.copy(message = null)
    }

    fun isInBasket(productId: String): Boolean =
        basketState.products.any { it.id == productId }

    fun startCompareFromBasket(): Boolean {
        if (basketState.products.size < 2) {
            basketState = basketState.copy(message = "至少选择 2 个商品才能对比")
            return false
        }
        loadCompare(basketState.products.map { it.id }, basketState.userNeed)
        basketState = basketState.copy(isExpanded = false, message = null)
        return true
    }

    fun clear() {
        onCleared()
    }

    companion object {
        fun from(shopRepository: ShopRepository): CompareViewModel =
            CompareViewModel(shopRepository.compareRepository, shopRepository.compareState())
    }
}
