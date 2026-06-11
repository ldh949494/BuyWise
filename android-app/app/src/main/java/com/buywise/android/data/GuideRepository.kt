package com.buywise.android.data

import okhttp3.OkHttpClient
import okhttp3.sse.EventSource
import okhttp3.sse.EventSourceListener
import okhttp3.sse.EventSources
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

sealed interface ChatStreamEvent {
    data class Meta(val sessionId: String) : ChatStreamEvent
    data class Status(val message: String) : ChatStreamEvent
    data class Token(val text: String) : ChatStreamEvent
    data class Products(
        val intentSummary: String,
        val recommendations: List<Recommendation>,
        val bundlePlans: List<BundlePlan> = emptyList(),
        val appliedPreferences: AppliedPreferences = AppliedPreferences(),
        val needClarify: Boolean = false,
        val missingFields: List<String> = emptyList(),
        val resultStatus: GuideResultStatus = GuideResultStatus.Exact,
        val fallbackMessage: String? = null,
    ) : ChatStreamEvent
    data class Done(
        val reply: String,
        val shouldRefresh: Boolean = false,
        val refreshReason: String? = null,
        val action: String? = null,
        val cart: CartState? = null,
    ) : ChatStreamEvent
    data class Error(val message: String) : ChatStreamEvent
    data object Heartbeat : ChatStreamEvent
}

class GuideRepository internal constructor(
    private val apiClient: BuyWiseApiClient,
    httpClient: OkHttpClient,
) {
    private val eventSourceFactory = EventSources.createFactory(
        httpClient.newBuilder()
            .readTimeout(0, TimeUnit.MILLISECONDS)
            .callTimeout(0, TimeUnit.MILLISECONDS)
            .build()
    )

    fun streamGuide(
        query: String,
        sessionId: String?,
        ignoreSavedPreferences: Boolean = false,
        onEvent: (ChatStreamEvent) -> Unit,
    ): EventSource = streamGuideRequest(
        request = apiClient.guideStreamRequest(
            GuideStreamRequestDto(
                sessionId = sessionId,
                message = query,
                ignoreSavedPreferences = ignoreSavedPreferences,
            )
        ),
        onEvent = onEvent,
    )

    fun streamGuideFollowUp(
        query: String,
        sessionId: String?,
        ignoreSavedPreferences: Boolean = false,
        onEvent: (ChatStreamEvent) -> Unit,
    ): EventSource = streamGuideRequest(
        request = apiClient.guideFollowUpStreamRequest(
            GuideStreamRequestDto(
                sessionId = sessionId,
                message = query,
                ignoreSavedPreferences = ignoreSavedPreferences,
            )
        ),
        onEvent = onEvent,
    )

    fun streamCompareFollowUp(
        query: String,
        context: CompareChatContext,
        onEvent: (ChatStreamEvent) -> Unit,
    ): EventSource = streamGuideRequest(
        request = apiClient.compareFollowUpStreamRequest(
            CompareFollowUpRequestDto(
                message = query,
                items = context.products.mapNotNull { product -> product.toCompareFollowUpProductDto() },
                summary = context.summary,
                winnerId = context.winnerId?.toIntOrNull(),
                userNeed = context.userNeed,
                sessionId = context.sessionId,
            )
        ),
        onEvent = onEvent,
    )

    private fun streamGuideRequest(
        request: okhttp3.Request,
        onEvent: (ChatStreamEvent) -> Unit,
    ): EventSource {
        return eventSourceFactory.newEventSource(
            request,
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
            "heartbeat" -> ChatStreamEvent.Heartbeat
            "done" -> ChatStreamEvent.Done(
                reply = json.optString("reply"),
                shouldRefresh = json.optBoolean("should_refresh", false),
                refreshReason = json.optStringOrNull("refresh_reason"),
                action = json.optJSONObject("extra")?.optStringOrNull("action"),
                cart = json.optJSONObject("extra")?.optJSONObject("cart")?.let(::parseCart),
            )
            "error" -> parseErrorEvent(json)
            else -> ChatStreamEvent.Status(type ?: "message")
        }
    }

    private fun parseErrorEvent(json: JSONObject): ChatStreamEvent.Error {
        val code = json.optString("code")
        val message = when (code) {
            "chat_stream_timeout" -> "导购回复超时，请稍后重试。"
            else -> json.optString("message", "导购建议生成失败")
        }
        return ChatStreamEvent.Error(message)
    }

    private fun parseProductsEvent(json: JSONObject): ChatStreamEvent.Products {
        val structuredNeed = json.optJSONObject("structured_need")
        val intent = structuredNeed?.optString("intent").orEmpty()
        val category = structuredNeed?.optString("category").orEmpty()
        val needClarify = json.optBoolean("need_clarify", false)
        val missingFields = structuredNeed?.optJSONArray("missing_fields").toStringList()
        val items = json.optJSONArray("items") ?: JSONArray()
        val bundlePlansJson = json.optJSONArray("bundle_plans") ?: JSONArray()
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
        val bundlePlans = (0 until bundlePlansJson.length()).mapNotNull { index ->
            bundlePlansJson.optJSONObject(index)?.let(::parseBundlePlan)
        }
        val appliedPreferences = parseAppliedPreferences(json.optJSONObject("applied_preferences"))
        val resultStatus = resultStatusFor(
            quality = json.optString("result_quality", "exact"),
            needClarify = needClarify,
            hasResults = recommendations.isNotEmpty() || bundlePlans.isNotEmpty(),
        )
        return ChatStreamEvent.Products(
            intentSummary = intentSummaryFor(
                intent = intent,
                needClarify = needClarify,
                missingFields = missingFields,
                hasBundles = bundlePlans.isNotEmpty(),
            ),
            recommendations = recommendations,
            bundlePlans = bundlePlans,
            appliedPreferences = appliedPreferences,
            needClarify = needClarify,
            missingFields = missingFields,
            resultStatus = resultStatus,
            fallbackMessage = fallbackMessageFor(resultStatus),
        )
    }

    private fun resultStatusFor(
        quality: String,
        needClarify: Boolean,
        hasResults: Boolean,
    ): GuideResultStatus {
        if (needClarify) {
            return GuideResultStatus.Clarifying
        }
        if (!hasResults) {
            return GuideResultStatus.Empty
        }
        return when (quality) {
            "relaxed" -> GuideResultStatus.Relaxed
            "broad" -> GuideResultStatus.Broad
            "low_confidence" -> GuideResultStatus.LowConfidence
            else -> GuideResultStatus.Exact
        }
    }

    private fun intentSummaryFor(
        intent: String,
        needClarify: Boolean,
        missingFields: List<String>,
        hasBundles: Boolean,
    ): String {
        if (needClarify) {
            return if ("category" in missingFields) "需要补充商品目标" else "需要补充导购信息"
        }
        return intent.ifBlank { if (hasBundles) "已生成组合方案" else "已生成推荐商品" }
    }

    private fun fallbackMessageFor(status: GuideResultStatus): String? =
        when (status) {
            GuideResultStatus.Relaxed -> "已放宽部分条件，先返回更接近的候选。"
            GuideResultStatus.Broad -> "当前按关键词宽搜返回候选，请先核对类目和商品页。"
            GuideResultStatus.LowConfidence -> "当前匹配度较低，先返回可参考商品。"
            else -> null
        }

    private fun JSONObject.optStringOrNull(name: String): String? =
        if (has(name) && !isNull(name)) optString(name).takeIf { it.isNotBlank() } else null
}

private fun JSONArray?.toStringList(): List<String> {
    if (this == null) {
        return emptyList()
    }
    return (0 until length()).mapNotNull { index -> optString(index).takeIf { it.isNotBlank() } }
}

private fun Product.toCompareFollowUpProductDto(): CompareFollowUpProductDto? {
    val id = id.toIntOrNull() ?: return null
    return CompareFollowUpProductDto(
        id = id,
        productId = id,
        name = name,
        price = price,
        rating = rating,
        score = recommendationScore,
        pros = advantages,
        cons = cautions,
    )
}
