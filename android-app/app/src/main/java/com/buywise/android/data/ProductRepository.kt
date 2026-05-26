package com.buywise.android.data

import java.io.IOException

class ProductRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
) {
    @Throws(IOException::class)
    fun fetchProducts(page: Int = 1, pageSize: Int = 20): List<Product> {
        val response: ProductListResponseDto = apiClient.get("/api/v1/products?page=$page&page_size=$pageSize")
        return response.items.map { it.toProduct() }
    }

    @Throws(IOException::class)
    fun fetchProductDetail(productId: String): Product {
        val product: ProductDto = apiClient.get("/api/v1/products/$productId")
        return product.toProduct()
    }
}
