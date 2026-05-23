package com.buywise.android.data

import com.buywise.android.BuildConfig
import java.io.IOException
import okhttp3.MultipartBody
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
            title = "后端多模态联调",
            confidence = 0,
            labels = listOf("等待联调"),
            similarProducts = emptyList(),
        ),
    )

    @Throws(IOException::class)
    fun runVisionDemo(): VisionResult {
        val upload = uploadDemoFile(
            filename = "buywise-demo.png",
            contentType = "image/png",
            bytes = DEMO_PNG_BYTES,
        )
        val payload = JSONObject()
            .put("image_url", upload.url)
            .toString()
            .toRequestBody(jsonMediaType)
        val json = postJson("$baseUrl/api/v1/vision/recognize", payload)
        val category = json.optStringOrNull("category") ?: "识别结果"
        val features = json.optJSONArray("features").toStringList()
        val query = json.optStringOrNull("query") ?: listOf(features.joinToString(" "), category).joinToString(" ").trim()
        return VisionResult(
            title = query.ifBlank { category },
            confidence = 100,
            labels = listOfNotBlank(category) + features,
            similarProducts = emptyList(),
        )
    }

    @Throws(IOException::class)
    fun runSpeechDemo(): String {
        val upload = uploadDemoFile(
            filename = "buywise-demo.wav",
            contentType = "audio/wav",
            bytes = DEMO_WAV_BYTES,
        )
        val payload = JSONObject()
            .put("audio_url", upload.url)
            .toString()
            .toRequestBody(jsonMediaType)
        return postJson("$baseUrl/api/v1/speech/asr", payload).optString("text")
    }

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
    fun recordPurchase(productId: String): String {
        val payload = JSONObject()
            .put("product_id", productId.toInt())
            .put("quantity", 1)
            .toString()
            .toRequestBody(jsonMediaType)
        val created = postJson("$baseUrl/api/v1/orders", payload)
        val orderId = created.optInt("id")
        val shipped = postJson("$baseUrl/api/v1/orders/$orderId/advance", "{}".toRequestBody(jsonMediaType))
        val delivered = postJson("$baseUrl/api/v1/orders/$orderId/advance", "{}".toRequestBody(jsonMediaType))
        return delivered.optString("fulfillment_status", shipped.optString("fulfillment_status"))
    }

    @Throws(IOException::class)
    fun fetchFeedbackPrompts(): List<FeedbackPrompt> {
        val json = getJson("$baseUrl/api/v1/feedback/prompts")
        val items = json.optJSONArray("items") ?: JSONArray()
        return (0 until items.length()).mapNotNull { index ->
            items.optJSONObject(index)?.let { item ->
                FeedbackPrompt(
                    orderId = item.optInt("order_id").toString(),
                    orderItemId = item.optInt("order_item_id").toString(),
                    productId = item.optInt("product_id").toString(),
                    productName = item.optString("product_name", "已购商品"),
                )
            }
        }
    }

    @Throws(IOException::class)
    fun submitFeedback(prompt: FeedbackPrompt) {
        val payload = JSONObject()
            .put("order_item_id", prompt.orderItemId.toInt())
            .put("rating", 5)
            .put("content", "收货后体验符合预期，愿意继续推荐。")
            .put("met_expectation", true)
            .put("pros_tags", JSONArray().put("good_value").put("easy_to_use"))
            .put("cons_tags", JSONArray())
            .toString()
            .toRequestBody(jsonMediaType)
        postJson("$baseUrl/api/v1/reviews/from-order-item", payload)
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

    private fun uploadDemoFile(filename: String, contentType: String, bytes: ByteArray): UploadResult {
        val body = MultipartBody.Builder()
            .setType(MultipartBody.FORM)
            .addFormDataPart("file", filename, bytes.toRequestBody(contentType.toMediaType()))
            .build()
        val request = Request.Builder()
            .url("$baseUrl/api/v1/upload")
            .header("Authorization", "Bearer ${BuildConfig.BUYWISE_UPLOAD_TOKEN}")
            .post(body)
            .build()
        val json = executeJson(request)
        return UploadResult(
            url = json.optString("url"),
            filename = json.optString("filename"),
        )
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

    private fun JSONObject.optIntOrNull(name: String): Int? =
        if (has(name) && !isNull(name)) optInt(name) else null

    private data class UploadResult(val url: String, val filename: String)

}
