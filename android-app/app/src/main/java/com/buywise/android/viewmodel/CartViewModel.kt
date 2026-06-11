package com.buywise.android.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.buywise.android.data.CartItem
import com.buywise.android.data.CartRepository
import com.buywise.android.data.CartState
import com.buywise.android.data.Product
import com.buywise.android.data.ShopRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class CartViewModel(
    private val repository: CartRepository,
    initialState: CartState,
) : ViewModel() {
    var state by mutableStateOf(initialState)
        private set

    fun refresh() {
        state = state.copy(isLoading = true, errorMessage = null)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.fetchCart() }
            }.onSuccess { next ->
                state = next.copy(isLoading = false)
            }.onFailure { throwable ->
                state = state.copy(isLoading = false, errorMessage = throwable.userMessage("购物车加载失败"))
            }
        }
    }

    fun addProduct(
        product: Product,
        sessionId: String? = null,
        onAdded: ((String) -> Unit)? = null,
    ) {
        if (product.id.toIntOrNull() == null) {
            state = state.copy(errorMessage = "该商品暂时无法加入购物车")
            return
        }
        state = state.copy(isLoading = true, errorMessage = null, message = null)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.addProduct(product, sessionId = sessionId) }
            }.onSuccess { next ->
                val message = "已加入购物车：${product.name}"
                state = next.copy(isLoading = false, message = message)
                onAdded?.invoke(message)
            }.onFailure { throwable ->
                state = state.copy(isLoading = false, errorMessage = throwable.userMessage("加入购物车失败"))
            }
        }
    }

    fun updateQuantity(item: CartItem, quantity: Int) {
        state = state.copy(isLoading = true, errorMessage = null, message = null)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.updateQuantity(item, quantity) }
            }.onSuccess { next ->
                state = next.copy(isLoading = false, message = "已更新数量")
            }.onFailure { throwable ->
                state = state.copy(isLoading = false, errorMessage = throwable.userMessage("数量更新失败"))
            }
        }
    }

    fun removeItem(item: CartItem) {
        state = state.copy(isLoading = true, errorMessage = null, message = null)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.removeItem(item) }
            }.onSuccess { next ->
                state = next.copy(isLoading = false, message = "已移除：${item.name}")
            }.onFailure { throwable ->
                state = state.copy(isLoading = false, errorMessage = throwable.userMessage("移除商品失败"))
            }
        }
    }

    fun checkout(sessionId: String? = null, onCheckedOut: (() -> Unit)? = null) {
        if (state.items.isEmpty()) {
            state = state.copy(errorMessage = "购物车为空，先加入商品再下单。")
            return
        }
        state = state.copy(isLoading = true, errorMessage = null, message = null)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { repository.checkout(sessionId) }
            }.onSuccess { result ->
                state = CartState(
                    message = "下单成功，订单 ${result.orderId} 已生成",
                )
                onCheckedOut?.invoke()
            }.onFailure { throwable ->
                state = state.copy(isLoading = false, errorMessage = throwable.userMessage("下单失败"))
            }
        }
    }

    fun applyServerCart(cart: CartState, message: String? = null) {
        state = cart.copy(isLoading = false, message = message, errorMessage = null)
    }

    fun clearMessage() {
        state = state.copy(message = null, errorMessage = null)
    }

    fun clear() {
        onCleared()
    }

    companion object {
        fun from(shopRepository: ShopRepository): CartViewModel =
            CartViewModel(shopRepository.cartRepository, shopRepository.cartState())
    }
}
