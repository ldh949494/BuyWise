package com.buywise.android.viewmodel

import android.os.Handler
import android.os.Looper
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.ViewModel
import com.buywise.android.data.GuideChatMessage
import com.buywise.android.data.GuideChatRole
import com.buywise.android.data.ChatStreamEvent
import com.buywise.android.data.GuideRepository
import com.buywise.android.data.GuideState
import com.buywise.android.data.ShopRepository
import okhttp3.sse.EventSource

class GuideViewModel(
    private val repository: GuideRepository,
    initialState: GuideState,
) : ViewModel() {
    private val mainHandler = Handler(Looper.getMainLooper())
    private var guideStream: EventSource? = null
    private var streamMode: StreamMode = StreamMode.Workbench
    private var activeAssistantMessageId: String? = null
    private var nextMessageId = 1

    var state by mutableStateOf(initialState)
        private set

    fun updateQuery(query: String) {
        state = state.copy(query = query)
    }

    fun updateChatDraft(draft: String) {
        state = state.copy(chatDraft = draft)
    }

    fun prepareChatDraft() {
        if (state.chatDraft.isBlank() && state.query.isNotBlank()) {
            state = state.copy(chatDraft = state.query)
        }
    }

    fun submitQuery() {
        val query = state.query.ifBlank { "300 元以内，适合宿舍写代码的低噪音机械键盘" }
        guideStream?.cancel()
        streamMode = StreamMode.Workbench
        activeAssistantMessageId = null
        state = state.copy(
            query = query,
            intentSummary = "正在理解预算、场景和偏好...",
            recommendations = emptyList(),
            partialReply = "",
            isStreaming = true,
            errorMessage = null,
        )
        guideStream = repository.streamGuide(
            query = query,
            sessionId = state.sessionId,
            onEvent = { event -> mainHandler.post { applyChatEvent(event) } },
        )
    }

    fun sendChatMessage() {
        val message = state.chatDraft.trim()
        if (message.isBlank() || state.isStreaming) {
            return
        }
        guideStream?.cancel()
        streamMode = StreamMode.Chat
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
        state = state.copy(
            query = message,
            chatDraft = "",
            chatMessages = state.chatMessages + userMessage + assistantMessage,
            partialReply = "",
            isStreaming = true,
            errorMessage = null,
        )
        guideStream = repository.streamGuide(
            query = message,
            sessionId = state.sessionId,
            onEvent = { event -> mainHandler.post { applyChatEvent(event) } },
        )
    }

    fun useQuery(query: String) {
        updateQuery(query)
        if (state.chatDraft.isBlank()) {
            state = state.copy(chatDraft = query)
        }
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
            is ChatStreamEvent.Products -> applyProducts(event.intentSummary, event.recommendations)
            is ChatStreamEvent.Done -> applyDone(event.reply)
            is ChatStreamEvent.Error -> applyError(event.message)
        }
    }

    private fun applyToken(text: String): GuideState {
        if (streamMode != StreamMode.Chat) {
            return state.copy(partialReply = state.partialReply + text)
        }
        return updateAssistantMessage { message -> message.copy(text = message.text + text) }
    }

    private fun applyProducts(intentSummary: String, recommendations: List<com.buywise.android.data.Recommendation>): GuideState {
        val synced = state.copy(intentSummary = intentSummary, recommendations = recommendations)
        if (streamMode != StreamMode.Chat || recommendations.isEmpty()) {
            return synced
        }
        return updateAssistantMessage(synced) { message -> message.copy(recommendations = recommendations) }
    }

    private fun applyDone(reply: String): GuideState {
        if (streamMode != StreamMode.Chat) {
            return state.copy(partialReply = reply.ifBlank { state.partialReply }, isStreaming = false)
        }
        val withReply = if (reply.isBlank()) {
            state
        } else {
            updateAssistantMessage { message ->
                if (message.text.isBlank()) message.copy(text = reply) else message
            }
        }
        activeAssistantMessageId = null
        return withReply.copy(isStreaming = false)
    }

    private fun applyError(message: String): GuideState {
        activeAssistantMessageId = null
        return state.copy(errorMessage = message, isStreaming = false)
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

    private fun newMessageId(): String = "guide-chat-${nextMessageId++}"

    private sealed interface StreamMode {
        data object Workbench : StreamMode
        data object Chat : StreamMode
    }

    companion object {
        fun from(shopRepository: ShopRepository): GuideViewModel =
            GuideViewModel(shopRepository.guideRepository, shopRepository.guideState(""))
    }
}
