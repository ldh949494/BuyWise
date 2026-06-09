package com.buywise.android.viewmodel

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.buywise.android.data.BetaCapability
import com.buywise.android.data.OrderRepository
import com.buywise.android.data.Product
import com.buywise.android.data.ProductDetailState
import com.buywise.android.data.ProductRepository
import com.buywise.android.data.ShopRepository
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class ProductDetailViewModel(
    private val productRepository: ProductRepository,
    private val orderRepository: OrderRepository,
    private val capability: BetaCapability,
) : ViewModel() {
    var state by mutableStateOf(ProductDetailState(
        canRecordPurchase = capability.canUseUserFeatures,
        tokenRequiredMessage = capability.message,
    ))
        private set

    fun loadProductDetail(productId: String?, cachedProduct: Product?) {
        if (productId.isNullOrBlank()) {
            state = state.copy(errorMessage = "商品 ID 无效。")
            return
        }
        state = ProductDetailState(
            product = cachedProduct,
            isLoading = true,
            canRecordPurchase = capability.canUseUserFeatures,
            tokenRequiredMessage = capability.message,
        )
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { productRepository.fetchProductDetail(productId) }
            }.onSuccess { product ->
                state = state.copy(product = product, isLoading = false)
            }.onFailure { throwable ->
                state = state.copy(isLoading = false, errorMessage = throwable.userMessage("商品详情加载失败"))
            }
        }
    }

    fun recordPurchase(productId: String, onRecorded: () -> Unit = {}) {
        if (!capability.canUseUserFeatures) {
            state = state.copy(errorMessage = capability.message)
            return
        }
        state = state.copy(isLoading = true, errorMessage = null, orderStatusMessage = null)
        viewModelScope.launch {
            runCatching {
                withContext(Dispatchers.IO) { orderRepository.recordPurchase(productId) }
            }.onSuccess { status ->
                state = state.copy(
                    isLoading = false,
                    orderStatusMessage = if (status == "delivered") "已记录购买并模拟收货，达到反馈时间后会出现在首页。" else "已记录购买：$status",
                )
                onRecorded()
            }.onFailure { throwable ->
                state = state.copy(isLoading = false, errorMessage = throwable.userMessage("购买记录创建失败"))
            }
        }
    }

    fun setCartStatus(message: String?) {
        state = state.copy(cartStatusMessage = message, errorMessage = null)
    }

    fun clear() {
        onCleared()
    }

    companion object {
        fun from(shopRepository: ShopRepository): ProductDetailViewModel =
            ProductDetailViewModel(shopRepository.productRepository, shopRepository.orderRepository, shopRepository.betaCapability)
    }
}
