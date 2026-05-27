package com.buywise.android.data

import okhttp3.OkHttpClient
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

class GuideRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
    httpClient: OkHttpClient,
) {
    private val eventSourceFactory = EventSources.createFactory(httpClient)

    fun streamGuide(
        query: String,
        sessionId: String?,
        onEvent: (ChatStreamEvent) -> Unit,
    ): EventSource {
        return eventSourceFactory.newEventSource(
            apiClient.guideStreamRequest(GuideStreamRequestDto(sessionId = sessionId, message = query)),
            object : EventSourceListener() {
                override fun onEvent(eventSource: EventSource, id: String?, type: String?, data: String) {
                    onEvent(parseStreamEvent(type, data))
                }

                override fun onFailure(eventSource: EventSource, t: Throwable?, response: okhttp3.Response?) {
                    onEvent(ChatStreamEvent.Error(t?.message ?: "导购建议生成失败"))
                }
            },
        )
    }

    private fun parseStreamEvent(type: String?, data: String): ChatStreamEvent {
        val json = JSONObject(data)
        return when (type) {
            "meta" -> ChatStreamEvent.Meta(json.optString("session_id"))
            "status" -> ChatStreamEvent.Status(json.optString("message", json.optString("stage")))
            "token" -> ChatStreamEvent.Token(json.optString("text"))
            "products" -> parseProductsEvent(json)
            "done" -> ChatStreamEvent.Done(json.optString("reply"))
            "error" -> ChatStreamEvent.Error(json.optString("message", "导购建议生成失败"))
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
            intentSummary = intent.ifBlank { "已生成推荐商品" },
            recommendations = recommendations,
        )
    }

    private fun JSONObject.optStringOrNull(name: String): String? =
        if (has(name) && !isNull(name)) optString(name).takeIf { it.isNotBlank() } else null
}
