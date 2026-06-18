package com.buywise.android.viewmodel

import android.os.Handler
import android.os.Looper
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import com.buywise.android.data.BundlePlan
import com.buywise.android.data.CartState
import com.buywise.android.data.CompareChatContext
import com.buywise.android.data.GuideChatMessage
import com.buywise.android.data.GuideChatRole
import com.buywise.android.data.ChatStreamEvent
import com.buywise.android.data.GuideRepository
import com.buywise.android.data.GuideResultStatus
import com.buywise.android.data.GuideState
import com.buywise.android.data.AppliedPreferences
import com.buywise.android.data.Recommendation
import com.buywise.android.data.ShopRepository
import okhttp3.sse.EventSource

class GuideViewModel(
    private val repository: GuideRepository,
    initialState: GuideState,
    private val onCartUpdated: (CartState, String?) -> Unit = { _, _ -> },
    private val onCartRefreshRequested: () -> Unit = {},
) : ViewModel() {
    private val mainHandler = Handler(Looper.getMainLooper())
    private var guideStream: EventSource? = null
    private var streamMode: StreamMode = StreamMode.Workbench
    private var activeAssistantMessageId: String? = null
    private var activeUserMessageText: String? = null
    private var nextMessageId = 1

    var state by mutableStateOf(initialState)
        private set

    fun updateQuery(query: String) {
        state = state.copy(query = query)
    }

    fun updateChatDraft(draft: String) {
        state = state.copy(chatDraft = draft)
    }

    fun useChatDraft(draft: String) {
        state = state.copy(chatDraft = draft)
    }

    fun setIgnoreSavedPreferences(value: Boolean) {
        state = state.copy(ignoreSavedPreferences = value)
    }

    fun appendChatDraft(text: String, sourceLabel: String) {
        val normalized = text.trim().replace(Regex("""\s+"""), " ")
        if (normalized.isBlank()) {
            return
        }
        val nextDraft = listOf(state.chatDraft.trim(), normalized)
            .filter { it.isNotBlank() }
            .joinToString(" ")
        val systemMessage = GuideChatMessage(
            id = newMessageId(),
            role = GuideChatRole.SYSTEM,
            text = "已识别$sourceLabel：$normalized，已填入输入框。",
        )
        state = state.copy(
            chatDraft = nextDraft,
            chatMessages = state.chatMessages + systemMessage,
        )
    }

    fun addChatSystemMessage(text: String) {
        if (text.isBlank()) {
            return
        }
        state = state.copy(
            chatMessages = state.chatMessages + GuideChatMessage(
                id = newMessageId(),
                role = GuideChatRole.SYSTEM,
                text = text,
            ),
        )
    }

    fun prepareChatDraft() {
        val nextState = state.copy(compareChatContext = null)
        if (state.chatDraft.isBlank() && state.query.isNotBlank() && state.chatMessages.isEmpty()) {
            state = nextState.copy(chatDraft = nextState.query)
            return
        }
        state = nextState
    }

    fun useCompareChatContext(context: CompareChatContext, draft: String) {
        state = state.copy(
            query = draft,
            chatDraft = draft,
            chatMessages = emptyList(),
            partialReply = "",
            errorMessage = null,
            compareChatContext = context,
        )
    }

    fun submitQuery() {
        val query = state.query.ifBlank { "300 元以内，适合宿舍写代码的低噪音机械键盘" }
        guideStream?.cancel()
        streamMode = StreamMode.Workbench
        val userMessage = GuideChatMessage(
            id = newMessageId(),
            role = GuideChatRole.USER,
            text = query,
        )
        val assistantMessage = GuideChatMessage(
            id = newMessageId(),
            role = GuideChatRole.ASSISTANT,
            text = "",
        )
        activeAssistantMessageId = assistantMessage.id
        activeUserMessageText = query
        state = state.copy(
            query = query,
            chatDraft = "",
            chatMessages = listOf(userMessage, assistantMessage),
            intentSummary = "正在理解预算、场景和偏好...",
            recommendations = emptyList(),
            bundlePlans = emptyList(),
            resultStatus = GuideResultStatus.Idle,
            clarificationMessage = null,
            fallbackMessage = null,
            hasProvisionalResults = false,
            pendingRefreshMessage = null,
            appliedPreferences = AppliedPreferences(),
            partialReply = "",
            isStreaming = true,
            errorMessage = null,
            sessionId = null,
            compareChatContext = null,
        )
        guideStream = repository.streamGuide(
            query = query,
            sessionId = state.sessionId,
            ignoreSavedPreferences = state.ignoreSavedPreferences,
            onEvent = { event -> mainHandler.post { applyChatEvent(event) } },
        )
    }

    fun sendChatMessage() {
        val message = state.chatDraft.trim()
        if (message.isBlank() || state.isStreaming) {
            return
        }
        val compareContext = state.compareChatContext
        val shouldRunFullGuide = compareContext == null &&
            (state.resultStatus == GuideResultStatus.Clarifying || (state.recommendations.isEmpty() && state.bundlePlans.isEmpty()))
        guideStream?.cancel()
        streamMode = when {
            compareContext != null -> StreamMode.Compare
            shouldRunFullGuide -> StreamMode.Workbench
            else -> StreamMode.Chat
        }
        val userMessage = GuideChatMessage(
            id = newMessageId(),
            role = GuideChatRole.USER,
            text = message,
        )
        val assistantMessage = GuideChatMessage(
            id = newMessageId(),
            role = GuideChatRole.ASSISTANT,
            text = "",
        )
        activeAssistantMessageId = assistantMessage.id
        activeUserMessageText = message
        val keepExistingResults = !shouldRunFullGuide
        state = state.copy(
            query = message,
            chatDraft = "",
            chatMessages = state.chatMessages + userMessage + assistantMessage,
            recommendations = if (keepExistingResults) state.recommendations else emptyList(),
            bundlePlans = if (keepExistingResults) state.bundlePlans else emptyList(),
            resultStatus = GuideResultStatus.Idle,
            clarificationMessage = null,
            fallbackMessage = null,
            hasProvisionalResults = false,
            pendingRefreshMessage = null,
            appliedPreferences = if (keepExistingResults) state.appliedPreferences else AppliedPreferences(),
            partialReply = "",
            isStreaming = true,
            errorMessage = null,
        )
        guideStream = if (shouldRunFullGuide) {
            repository.streamGuide(
                query = message,
                sessionId = state.sessionId,
                ignoreSavedPreferences = state.ignoreSavedPreferences,
                onEvent = { event -> mainHandler.post { applyChatEvent(event) } },
            )
        } else if (compareContext == null) {
            repository.streamGuideFollowUp(
                query = message,
                sessionId = state.sessionId,
                ignoreSavedPreferences = state.ignoreSavedPreferences,
                onEvent = { event -> mainHandler.post { applyChatEvent(event) } },
            )
        } else {
            repository.streamCompareFollowUp(
                query = message,
                context = compareContext,
                onEvent = { event -> mainHandler.post { applyChatEvent(event) } },
            )
        }
    }

    fun useQuery(query: String) {
        updateQuery(query)
        if (state.chatDraft.isBlank()) {
            state = state.copy(chatDraft = query)
        }
    }

    fun runPendingRefresh() {
        val message = state.pendingRefreshMessage?.trim().orEmpty()
        if (message.isBlank() || state.isStreaming) {
            return
        }
        state = state.copy(query = message, chatDraft = "")
        submitQuery()
    }

    fun clearStream() {
        guideStream?.cancel()
    }

    fun clear() {
        onCleared()
    }

    override fun onCleared() {
        clearStream()
        super.onCleared()
    }

    private fun applyChatEvent(event: ChatStreamEvent) {
        state = when (event) {
            is ChatStreamEvent.Meta -> state.copy(sessionId = event.sessionId)
            is ChatStreamEvent.Status -> state.copy(intentSummary = event.message)
            is ChatStreamEvent.Token -> applyToken(event.text)
            is ChatStreamEvent.Products -> applyProducts(
                event.intentSummary,
                event.recommendations,
                event.bundlePlans,
                event.appliedPreferences,
                event.needClarify,
                event.resultStatus,
                event.fallbackMessage,
                event.provisional,
            )
            is ChatStreamEvent.Done -> applyDone(event)
            is ChatStreamEvent.Error -> applyError(event.message)
            ChatStreamEvent.Heartbeat -> state
        }
    }

    private fun applyToken(text: String): GuideState {
        if (streamMode != StreamMode.Chat) {
            val withPartialReply = state.copy(partialReply = state.partialReply + text)
            return updateAssistantMessage(withPartialReply) { message ->
                message.copy(text = message.text + text)
            }
        }
        return updateAssistantMessage { message -> message.copy(text = message.text + text) }
    }

    private fun applyProducts(
        intentSummary: String,
        recommendations: List<Recommendation>,
        bundlePlans: List<BundlePlan>,
        appliedPreferences: AppliedPreferences,
        needClarify: Boolean,
        resultStatus: GuideResultStatus,
        fallbackMessage: String?,
        provisional: Boolean,
    ): GuideState {
        if (needClarify) {
            val message = activeAssistantText().ifBlank { "想看哪类商品或商品名？" }
            val synced = state.copy(
                intentSummary = intentSummary,
                recommendations = emptyList(),
                bundlePlans = emptyList(),
                resultStatus = GuideResultStatus.Clarifying,
                clarificationMessage = message,
                fallbackMessage = null,
                hasProvisionalResults = false,
                appliedPreferences = appliedPreferences,
            )
            return updateAssistantMessage(synced) { assistant ->
                if (assistant.text.isBlank()) assistant.copy(text = message) else assistant
            }
        }
        val nextStatus = if (recommendations.isEmpty() && bundlePlans.isEmpty()) GuideResultStatus.Empty else resultStatus
        val synced = state.copy(
            intentSummary = intentSummary,
            recommendations = recommendations,
            bundlePlans = bundlePlans,
            resultStatus = nextStatus,
            clarificationMessage = null,
            fallbackMessage = fallbackMessage,
            hasProvisionalResults = provisional,
            appliedPreferences = appliedPreferences,
        )
        if (recommendations.isEmpty() && bundlePlans.isEmpty()) {
            return synced
        }
        return updateAssistantMessage(synced) { message ->
            message.copy(
                recommendations = recommendations,
                bundlePlans = bundlePlans,
                appliedPreferences = appliedPreferences,
            )
        }
    }

    private fun applyDone(event: ChatStreamEvent.Done): GuideState {
        if (event.shouldRefresh) {
            val reply = event.reply.ifBlank { "这个问题需要刷新导购结果。" }
            val withReply = updateAssistantMessage { message -> message.copy(text = reply) }
            val refreshMessage = activeUserMessageText?.takeIf { it.isNotBlank() } ?: state.query.takeIf { it.isNotBlank() }
            activeAssistantMessageId = null
            activeUserMessageText = null
            return withReply.copy(
                pendingRefreshMessage = refreshMessage,
                chatDraft = "",
                isStreaming = false,
            )
        }
        val reply = event.reply
        val finalReply = reply.ifBlank { if (streamMode == StreamMode.Workbench) state.partialReply else "" }
            .ifBlank { fallbackAssistantReply() }
        val keptProvisionalResults = state.hasProvisionalResults && (state.recommendations.isNotEmpty() || state.bundlePlans.isNotEmpty())
        val baseState = state.copy(
            partialReply = if (streamMode == StreamMode.Workbench) finalReply else state.partialReply,
            hasProvisionalResults = false,
            fallbackMessage = if (keptProvisionalResults && state.fallbackMessage == null) {
                "已先保留可参考候选，完整复核稍后可重试。"
            } else {
                state.fallbackMessage
            },
            isStreaming = false,
            clarificationMessage = if (state.resultStatus == GuideResultStatus.Clarifying) {
                state.clarificationMessage ?: finalReply.takeIf { it.isNotBlank() }
            } else {
                state.clarificationMessage
            },
        )
        val withReply = if (finalReply.isBlank()) {
            baseState
        } else {
            updateAssistantMessage(baseState) { message ->
                if (reply.isNotBlank() || streamMode == StreamMode.Workbench || message.text.isBlank()) {
                    message.copy(text = finalReply)
                } else {
                    message
                }
            }
        }
        syncCartAction(event, finalReply)
        activeAssistantMessageId = null
        activeUserMessageText = null
        return withReply
    }

    private fun syncCartAction(event: ChatStreamEvent.Done, message: String) {
        if (event.cart != null) {
            onCartUpdated(event.cart, message.takeIf { it.isNotBlank() })
            return
        }
        if (event.action in setOf("cart.add", "cart.remove", "checkout.confirm")) {
            onCartRefreshRequested()
        }
    }

    private fun applyError(message: String): GuideState {
        activeAssistantMessageId = null
        activeUserMessageText = null
        val keptProvisionalResults = state.hasProvisionalResults && (state.recommendations.isNotEmpty() || state.bundlePlans.isNotEmpty())
        return state.copy(
            errorMessage = message,
            hasProvisionalResults = false,
            fallbackMessage = if (keptProvisionalResults && state.fallbackMessage == null) {
                "已先保留可参考候选，完整复核稍后可重试。"
            } else {
                state.fallbackMessage
            },
            isStreaming = false,
        )
    }

    private fun updateAssistantMessage(
        baseState: GuideState = state,
        transform: (GuideChatMessage) -> GuideChatMessage,
    ): GuideState {
        val id = activeAssistantMessageId ?: return baseState
        return baseState.copy(
            chatMessages = baseState.chatMessages.map { message ->
                if (message.id == id) transform(message) else message
            },
        )
    }

    private fun fallbackAssistantReply(): String = when {
        state.resultStatus == GuideResultStatus.Clarifying -> state.clarificationMessage.orEmpty()
        state.bundlePlans.isNotEmpty() -> "已根据你的需求整理出组合方案。"
        state.recommendations.isNotEmpty() -> "已根据你的需求整理出推荐候选。"
        else -> ""
    }

    private fun activeAssistantText(): String {
        val id = activeAssistantMessageId ?: return ""
        return state.chatMessages.firstOrNull { it.id == id }?.text.orEmpty()
    }

    private fun newMessageId(): String = "guide-chat-${nextMessageId++}"

    private sealed interface StreamMode {
        data object Workbench : StreamMode
        data object Chat : StreamMode
        data object Compare : StreamMode
    }

    companion object {
        fun from(shopRepository: ShopRepository): GuideViewModel =
            GuideViewModel(shopRepository.guideRepository, shopRepository.guideState(""))
    }
}
