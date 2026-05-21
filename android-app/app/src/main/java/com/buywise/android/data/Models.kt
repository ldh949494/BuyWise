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

data class VisionState(
    val result: VisionResult,
)

data class ProductDetailState(
    val product: Product? = null,
    val isLoading: Boolean = false,
    val errorMessage: String? = null,
)
