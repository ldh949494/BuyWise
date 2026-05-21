package com.buywise.android.data

import com.buywise.android.BuildConfig
import java.io.IOException
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import org.json.JSONArray
import org.json.JSONObject

sealed interface ChatStreamEvent {
    data class Meta(val sessionId: String) : ChatStreamEvent
    data class Status(val message: String) : ChatStreamEvent
    data class Token(val text: String) : ChatStreamEvent
    data class Products(val intentSummary: String, val recommendations: List<Recommendation>) : ChatStreamEvent
    data class Done(val reply: String) : ChatStreamEvent
    data class Error(val message: String) : ChatStreamEvent
}

class ShopRepository(
    private val baseUrl: String = BuildConfig.BUYWISE_API_BASE_URL.trimEnd('/'),
) {
    private val httpClient = OkHttpClient()
    private val eventSourceFactory = EventSources.createFactory(httpClient)
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()

    private val demoProducts = listOf(
        Product(
            id = "vision-keyboard",
            name = "本地演示机械键盘",
            brand = "BuyWise Demo",
            category = "机械键盘",
            price = 299.0,
            rating = 4.7,
            recommendationScore = null,
            headline = "视觉页当前保留本地演示数据，未纳入本轮前后端联调。",
            tags = listOf("本地演示", "机械键盘", "低噪音"),
            advantages = listOf("用于展示识图页面布局"),
            cautions = listOf("不代表后端识别结果"),
        ),
    )

    fun homeState(): HomeState = HomeState(
        heroTitle = "更快找到适合你的商品",
        heroSubtitle = "连接 BuyWise 后端，按预算、场景和偏好生成导购建议。",
        products = emptyList(),
    )

    fun guideState(query: String): GuideState = GuideState(
        query = query,
        intentSummary = "输入预算、使用场景和偏好后，BuyWise 会从后端生成推荐。",
        recommendations = emptyList(),
    )

    fun compareState(): CompareState = CompareState(products = emptyList(), rows = emptyList())

    fun visionState(): VisionState = VisionState(
        result = VisionResult(
            title = "本地演示：视觉识别未纳入本轮联调",
            confidence = 0,
            labels = listOf("本地演示"),
            similarProducts = demoProducts,
        ),
    )

    @Throws(IOException::class)
    fun fetchProducts(page: Int = 1, pageSize: Int = 20): List<Product> {
        val json = getJson("$baseUrl/api/v1/products?page=$page&page_size=$pageSize")
        val items = json.optJSONArray("items") ?: JSONArray()
        return (0 until items.length()).mapNotNull { index ->
            items.optJSONObject(index)?.let(::parseProductRead)
        }
    }

    @Throws(IOException::class)
    fun fetchProductDetail(productId: String): Product {
        return parseProductRead(getJson("$baseUrl/api/v1/products/$productId"))
    }

    @Throws(IOException::class)
    fun compareProducts(productIds: List<String>, userNeed: String? = null): CompareState {
        if (productIds.size < 2) {
            return CompareState(
                products = emptyList(),
                rows = emptyList(),
                errorMessage = "至少需要 2 个商品才能对比。",
            )
        }
        val ids = JSONArray()
        productIds.mapNotNull { it.toIntOrNull() }.forEach(ids::put)
        val payload = JSONObject()
            .put("product_ids", ids)
            .put("user_need", userNeed ?: "对比这些商品的价格、评分、优点和注意事项")
            .toString()
            .toRequestBody(jsonMediaType)
        val json = postJson("$baseUrl/api/v1/products/compare", payload)
        val items = json.optJSONArray("items") ?: JSONArray()
        val products = (0 until items.length()).mapNotNull { index ->
            items.optJSONObject(index)?.let(::parseCompareItem)
        }
        return CompareState(
            products = products,
            rows = buildCompareRows(products),
            summary = json.optStringOrNull("summary"),
            winnerId = json.optIntOrNull("winner_id")?.toString(),
        )
    }

    fun streamGuide(
        query: String,
        sessionId: String?,
        onEvent: (ChatStreamEvent) -> Unit,
    ): EventSource {
        val payload = JSONObject()
            .put("session_id", sessionId)
            .put("message", query)
            .toString()
            .toRequestBody(jsonMediaType)
        val request = Request.Builder()
            .url("$baseUrl/api/v1/ai/chat/stream")
            .post(payload)
            .build()
        return eventSourceFactory.newEventSource(
            request,
            object : EventSourceListener() {
                override fun onEvent(eventSource: EventSource, id: String?, type: String?, data: String) {
                    onEvent(parseStreamEvent(type, data))
                }

                override fun onFailure(eventSource: EventSource, t: Throwable?, response: okhttp3.Response?) {
                    onEvent(ChatStreamEvent.Error(t?.message ?: "后端导购流连接失败"))
                }
            },
        )
    }

    private fun getJson(url: String): JSONObject {
        val request = Request.Builder().url(url).get().build()
        return executeJson(request)
    }

    private fun postJson(url: String, body: okhttp3.RequestBody): JSONObject {
        val request = Request.Builder().url(url).post(body).build()
        return executeJson(request)
    }

    private fun executeJson(request: Request): JSONObject {
        httpClient.newCall(request).execute().use { response ->
            val body = response.body?.string().orEmpty()
            if (!response.isSuccessful) {
                throw IOException("HTTP ${response.code}: ${body.ifBlank { response.message }}")
            }
            return JSONObject(body)
        }
    }

    private fun parseStreamEvent(type: String?, data: String): ChatStreamEvent {
        val json = JSONObject(data)
        return when (type) {
            "meta" -> ChatStreamEvent.Meta(json.optString("session_id"))
            "status" -> ChatStreamEvent.Status(json.optString("message", json.optString("stage")))
            "token" -> ChatStreamEvent.Token(json.optString("text"))
            "products" -> parseProductsEvent(json)
            "done" -> ChatStreamEvent.Done(json.optString("reply"))
            "error" -> ChatStreamEvent.Error(json.optString("message", "后端导购流失败"))
            else -> ChatStreamEvent.Status(type ?: "message")
        }
    }

    private fun parseProductsEvent(json: JSONObject): ChatStreamEvent.Products {
        val structuredNeed = json.optJSONObject("structured_need")
        val intent = structuredNeed?.optString("intent").orEmpty()
        val category = structuredNeed?.optString("category").orEmpty()
        val items = json.optJSONArray("items") ?: JSONArray()
        val recommendations = (0 until items.length()).mapNotNull { index ->
            val item = items.optJSONObject(index) ?: return@mapNotNull null
            val reason = item.optStringOrNull("reason")
                ?: item.optStringOrNull("description")
                ?: item.optString("name")
            Recommendation(
                product = parseProductCard(item, category, reason),
                reason = reason,
            )
        }
        return ChatStreamEvent.Products(
            intentSummary = intent.ifBlank { "后端已返回推荐商品" },
            recommendations = recommendations,
        )
    }

    private fun parseProductRead(json: JSONObject): Product {
        val description = json.optStringOrNull("description")
        val reviewSummary = json.optStringOrNull("review_summary")
        val scenes = json.optJSONArray("suitable_scene").toStringList()
        return Product(
            id = json.optInt("id").toString(),
            name = json.optString("name", "未命名商品"),
            brand = json.optStringOrNull("brand") ?: json.optStringOrNull("platform"),
            category = json.optStringOrNull("category"),
            price = json.optDoubleOrNull("price"),
            rating = json.optDoubleOrNull("rating"),
            recommendationScore = null,
            headline = description ?: reviewSummary ?: "暂无商品简介",
            tags = json.optJSONArray("tags").toStringList().ifEmpty { scenes },
            advantages = listOfNotBlank(reviewSummary) + scenes.map { "适合$it" },
            cautions = listOfNotBlank(json.optStringOrNull("stock_status")?.let { "库存状态：$it" }),
            imageUrl = json.optStringOrNull("image_url"),
            productUrl = json.optStringOrNull("product_url"),
            stockStatus = json.optStringOrNull("stock_status"),
            reviewSummary = reviewSummary,
        )
    }

    private fun parseProductCard(json: JSONObject, category: String, reason: String): Product {
        val conflicts = json.optJSONArray("conflicts").toStringList()
        return Product(
            id = json.optInt("id").toString(),
            name = json.optString("name", "未命名商品"),
            brand = "BuyWise",
            category = category.ifBlank { "推荐商品" },
            price = json.optDoubleOrNull("price"),
            rating = json.optDoubleOrNull("rating"),
            recommendationScore = json.optDoubleOrNull("score"),
            headline = reason,
            tags = json.optJSONArray("tags").toStringList(),
            advantages = listOfNotBlank(reason),
            cautions = conflicts,
            imageUrl = json.optStringOrNull("image_url"),
        )
    }

    private fun parseCompareItem(json: JSONObject): Product {
        val pros = json.optJSONArray("pros").toStringList()
        val cons = json.optJSONArray("cons").toStringList()
        return Product(
            id = (json.optIntOrNull("product_id") ?: json.optInt("id")).toString(),
            name = json.optString("name", "未命名商品"),
            brand = "BuyWise",
            category = "对比商品",
            price = json.optDoubleOrNull("price"),
            rating = json.optDoubleOrNull("rating"),
            recommendationScore = json.optDoubleOrNull("score"),
            headline = pros.firstOrNull() ?: "后端已返回对比结果",
            tags = pros.ifEmpty { listOf("对比结果") },
            advantages = pros,
            cautions = cons,
            imageUrl = json.optStringOrNull("image_url"),
        )
    }

    private fun buildCompareRows(products: List<Product>): List<CompareRow> {
        if (products.isEmpty()) {
            return emptyList()
        }
        return listOf(
            CompareRow("价格", products.map { it.price.displayPrice() }),
            CompareRow("评分", products.map { it.rating.displayRating() }),
            CompareRow("推荐分", products.map { it.recommendationScore.displayScore() }),
            CompareRow("优点", products.map { it.advantages.take(2).joinToString(" / ").ifBlank { "暂无" } }),
            CompareRow("注意事项", products.map { it.cautions.take(2).joinToString(" / ").ifBlank { "暂无" } }),
        )
    }

    private fun JSONArray?.toStringList(): List<String> {
        if (this == null) {
            return emptyList()
        }
        return (0 until length()).mapNotNull { index -> optString(index).takeIf { it.isNotBlank() } }
    }

    private fun listOfNotBlank(value: String?): List<String> =
        if (value.isNullOrBlank()) emptyList() else listOf(value)

    private fun JSONObject.optStringOrNull(name: String): String? =
        if (has(name) && !isNull(name)) optString(name).takeIf { it.isNotBlank() } else null

    private fun JSONObject.optDoubleOrNull(name: String): Double? =
        if (has(name) && !isNull(name)) optDouble(name) else null

    private fun JSONObject.optIntOrNull(name: String): Int? =
        if (has(name) && !isNull(name)) optInt(name) else null

    private fun Double?.displayPrice(): String = this?.let { "¥${formatNumber(it)}" } ?: "暂无"

    private fun Double?.displayRating(): String = this?.let { formatNumber(it) } ?: "暂无"

    private fun Double?.displayScore(): String = this?.let { formatNumber(it) } ?: "暂无"

    private fun formatNumber(value: Double): String =
        if (value % 1.0 == 0.0) value.toInt().toString() else "%.1f".format(value)
}
