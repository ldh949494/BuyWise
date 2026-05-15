package com.buywise.android.data

data class Product(
    val id: String,
    val name: String,
    val brand: String,
    val category: String,
    val price: Int,
    val score: Int,
    val headline: String,
    val tags: List<String>,
    val advantages: List<String>,
    val cautions: List<String>,
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
)

data class GuideState(
    val query: String,
    val intentSummary: String,
    val recommendations: List<Recommendation>,
)

data class CompareState(
    val products: List<Product>,
    val rows: List<CompareRow>,
)

data class VisionState(
    val result: VisionResult,
)
