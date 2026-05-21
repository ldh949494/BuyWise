package com.buywise.android.data

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

class ShopRepository {
    private val httpClient = OkHttpClient()
    private val eventSourceFactory = EventSources.createFactory(httpClient)
    private val jsonMediaType = "application/json; charset=utf-8".toMediaType()
    private val baseUrl = "http://10.0.2.2:8000"

    private val products = listOf(
        Product(
            id = "mouse-lite",
            name = "AeroMouse S",
            brand = "Pulse",
            category = "游戏鼠标",
            price = 299,
            score = 95,
            headline = "49g 轻量机身，适合 FPS 玩家和宿舍桌面使用。",
            tags = listOf("49g", "8K 回报率", "无线"),
            advantages = listOf("握持轻巧", "延迟低", "预算友好"),
            cautions = listOf("大手用户建议先试握"),
        ),
        Product(
            id = "keyboard-75",
            name = "RainKey 75",
            brand = "WOBKEY",
            category = "机械键盘",
            price = 699,
            score = 92,
            headline = "75% 配列搭配 Gasket 结构，兼顾桌面空间和输入手感。",
            tags = listOf("75%", "Gasket", "多模连接"),
            advantages = listOf("敲击声音克制", "手感稳定", "适合办公和写代码"),
            cautions = listOf("预算紧张时可考虑低配版本"),
        ),
        Product(
            id = "headset-wireless",
            name = "Cloud Air III",
            brand = "HyperSound",
            category = "蓝牙耳机",
            price = 799,
            score = 89,
            headline = "主动降噪和轻量佩戴，适合通勤、学习和长时间会议。",
            tags = listOf("主动降噪", "无线", "长续航"),
            advantages = listOf("降噪表现稳定", "佩戴压力小", "通话清晰"),
            cautions = listOf("高音量下续航会缩短"),
        ),
        Product(
            id = "monitor-240",
            name = "Focus 27Q240",
            brand = "ViewCore",
            category = "显示器",
            price = 2499,
            score = 88,
            headline = "2K 240Hz Fast IPS 面板，面向电竞和创作混合场景。",
            tags = listOf("2K", "240Hz", "Fast IPS"),
            advantages = listOf("刷新率高", "画面响应快", "接口齐全"),
            cautions = listOf("需要预留较高桌面预算"),
        ),
    )

    fun homeState(): HomeState = HomeState(
        heroTitle = "更快找到适合你的商品",
        heroSubtitle = "用预算、场景和偏好生成导购建议，先通过 mock 数据跑通移动端体验。",
        products = products,
    )

    fun guideState(query: String): GuideState {
        val normalized = query.ifBlank { "300 元以内，适合 FPS 的轻量无线鼠标" }
        return GuideState(
            query = query,
            intentSummary = "围绕“$normalized”生成的 mock 需求画像：预算、使用场景和偏好已提取。",
            recommendations = products.take(3).mapIndexed { index, product ->
                Recommendation(
                    product = product,
                    reason = when (index) {
                        0 -> "最贴近预算和核心场景，优先推荐作为首选。"
                        1 -> "功能更均衡，适合作为预算上浮后的备选。"
                        else -> "适合相近使用场景，可作为横向比较参考。"
                    },
                )
            },
        )
    }

    fun compareState(): CompareState {
        val compared = products.take(3)
        return CompareState(
            products = compared,
            rows = listOf(
                CompareRow("价格", compared.map { "¥${it.price}" }),
                CompareRow("评分", compared.map { "${it.score}" }),
                CompareRow("品类", compared.map { it.category }),
                CompareRow("卖点", compared.map { it.tags.take(2).joinToString(" / ") }),
            ),
        )
    }

    fun visionState(): VisionState = VisionState(
        result = VisionResult(
            title = "识别结果：疑似紧凑机械键盘",
            confidence = 92,
            labels = listOf("机械键盘", "无线", "紧凑布局"),
            similarProducts = products.drop(1),
        ),
    )

    fun product(productId: String?): Product? = products.firstOrNull { it.id == productId }

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
                    onEvent(ChatStreamEvent.Error(t?.message ?: "Backend stream failed"))
                }
            },
        )
    }

    private fun parseStreamEvent(type: String?, data: String): ChatStreamEvent {
        val json = JSONObject(data)
        return when (type) {
            "meta" -> ChatStreamEvent.Meta(json.optString("session_id"))
            "status" -> ChatStreamEvent.Status(json.optString("stage", json.optString("message")))
            "token" -> ChatStreamEvent.Token(json.optString("text"))
            "products" -> parseProductsEvent(json)
            "done" -> ChatStreamEvent.Done(json.optString("reply"))
            "error" -> ChatStreamEvent.Error(json.optString("message", "Backend stream failed"))
            else -> ChatStreamEvent.Status(type ?: "message")
        }
    }

    private fun parseProductsEvent(json: JSONObject): ChatStreamEvent.Products {
        val structuredNeed = json.optJSONObject("structured_need")
        val category = structuredNeed?.optString("category").orEmpty()
        val intent = structuredNeed?.optString("intent").orEmpty()
        val products = json.optJSONArray("items") ?: JSONArray()
        val recommendations = (0 until products.length()).mapNotNull { index ->
            val item = products.optJSONObject(index) ?: return@mapNotNull null
            val tags = item.optJSONArray("tags").toStringList()
            val reason = item.optString("reason").ifBlank { item.optString("name") }
            Recommendation(
                product = Product(
                    id = item.optInt("id").toString(),
                    name = item.optString("name"),
                    brand = "BuyWise",
                    category = category.ifBlank { "AI" },
                    price = item.optDouble("price", 0.0).toInt(),
                    score = item.optDouble("score", 0.0).toInt(),
                    headline = reason,
                    tags = tags,
                    advantages = listOfNotBlank(reason),
                    cautions = item.optJSONArray("conflicts").toStringList(),
                ),
                reason = reason,
            )
        }
        return ChatStreamEvent.Products(
            intentSummary = intent.ifBlank { "AI guide" },
            recommendations = recommendations,
        )
    }

    private fun JSONArray?.toStringList(): List<String> {
        if (this == null) {
            return emptyList()
        }
        return (0 until length()).mapNotNull { index -> optString(index).takeIf { it.isNotBlank() } }
    }

    private fun listOfNotBlank(value: String): List<String> =
        if (value.isBlank()) emptyList() else listOf(value)
}
